#!/usr/bin/env python3
"""Loopback-only emergency chat for local model runtimes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import webbrowser


ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
RUNTIME = ROOT / ".runtime"
SCHEMA_VERSION = "anthenara.ai-vault.local-chat.v1"
DEFAULT_PORT = 8765
MAX_BODY = 1_000_000
MAX_MODELS = 250
HTTP_TIMEOUT = 1.2


def is_loopback_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}


def request_json(url: str, *, method: str = "GET", payload: Any = None, timeout: float = HTTP_TIMEOUT) -> Any:
    if not is_loopback_url(url):
        raise ValueError("Only loopback HTTP endpoints are permitted")
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, method=method)
    request.add_header("Accept", "application/json")
    if data is not None:
        request.add_header("Content-Type", "application/json")
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def endpoint_specs() -> list[dict[str, str]]:
    specs = [
        {"id": "ollama", "kind": "ollama", "name": "Ollama", "baseUrl": "http://127.0.0.1:11434"},
        {"id": "lm-studio", "kind": "openai", "name": "LM Studio", "baseUrl": "http://127.0.0.1:1234"},
        {"id": "llama-cpp", "kind": "openai", "name": "llama.cpp", "baseUrl": "http://127.0.0.1:8080"},
        {"id": "colibri", "kind": "openai", "name": "Colibri", "baseUrl": "http://127.0.0.1:8000"},
    ]
    custom = os.environ.get("AI_VAULT_OPENAI_ENDPOINT", "").strip().rstrip("/")
    if custom:
        if not is_loopback_url(custom):
            raise ValueError("AI_VAULT_OPENAI_ENDPOINT must be a loopback HTTP URL")
        specs.append({"id": "custom-local", "kind": "openai", "name": "Custom local server", "baseUrl": custom})
    return specs


def parse_model_ids(kind: str, response: Any) -> list[str]:
    if not isinstance(response, dict):
        return []
    if kind == "ollama":
        rows = response.get("models", [])
        return sorted({str(row.get("name")) for row in rows if isinstance(row, dict) and row.get("name")})
    rows = response.get("data", [])
    return sorted({str(row.get("id")) for row in rows if isinstance(row, dict) and row.get("id")})


def discover_backends() -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    try:
        specs = endpoint_specs()
    except ValueError as exc:
        specs = []
        found.append({"id": "configuration-error", "name": "Configuration error", "kind": "error", "available": False, "models": [], "error": str(exc)})
    for spec in specs:
        path = "/api/tags" if spec["kind"] == "ollama" else "/v1/models"
        try:
            response = request_json(spec["baseUrl"] + path)
            models = parse_model_ids(spec["kind"], response)
            found.append({**spec, "available": True, "models": models, "error": None})
        except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError, OSError) as exc:
            found.append({**spec, "available": False, "models": [], "error": type(exc).__name__})
    return found


def model_roots() -> list[Path]:
    configured = [Path(value).expanduser() for value in os.environ.get("AI_VAULT_MODEL_DIRS", "").split(os.pathsep) if value.strip()]
    defaults = [ROOT / "models", Path.home() / "Models", Path.home() / "AI Models"]
    unique: list[Path] = []
    seen: set[str] = set()
    for path in configured + defaults:
        resolved = str(path.resolve(strict=False))
        if resolved not in seen:
            seen.add(resolved)
            unique.append(Path(resolved))
    return unique


def discover_gguf_files() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for root in model_roots():
        if not root.is_dir():
            continue
        for current, directories, filenames in os.walk(root, followlinks=False):
            directories[:] = [name for name in directories if not name.startswith(".")]
            for filename in filenames:
                normalized = filename.lower()
                if filename.startswith(".") or normalized.startswith("mmproj-") or not normalized.endswith(".gguf"):
                    continue
                path = (Path(current) / filename).resolve()
                try:
                    size = path.stat().st_size
                    with path.open("rb") as handle:
                        if handle.read(4) != b"GGUF":
                            continue
                except OSError:
                    continue
                results.append({
                    "id": hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:16],
                    "name": filename,
                    "path": str(path),
                    "sizeBytes": size,
                })
                if len(results) >= MAX_MODELS:
                    return sorted(results, key=lambda item: item["name"].lower())
    return sorted(results, key=lambda item: item["name"].lower())


def launch_gguf(model_id: str) -> dict[str, Any]:
    models = {model["id"]: model for model in discover_gguf_files()}
    selected = models.get(model_id)
    if not selected:
        raise ValueError("The selected model is not in the current approved scan")
    binary = os.environ.get("AI_VAULT_LLAMA_SERVER", "").strip() or shutil.which("llama-server")
    if not binary:
        raise RuntimeError("llama-server was not found in PATH")
    RUNTIME.mkdir(exist_ok=True)
    log_path = RUNTIME / "llama-server.log"
    log_handle = log_path.open("ab")
    process = subprocess.Popen(
        [
            binary,
            "--host", "127.0.0.1",
            "--port", "8080",
            "--cors-origins", "localhost",
            "--no-webui",
            "--model", selected["path"],
        ],
        cwd=str(ROOT),
        stdin=subprocess.DEVNULL,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    (RUNTIME / "llama-server.pid").write_text(str(process.pid), encoding="utf-8")
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"llama-server exited with code {process.returncode}; inspect {log_path}")
        try:
            request_json("http://127.0.0.1:8080/v1/models", timeout=0.5)
            return {"started": True, "pid": process.pid, "model": selected["name"], "log": str(log_path)}
        except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError, OSError):
            time.sleep(0.35)
    raise RuntimeError(f"llama-server did not become ready; inspect {log_path}")


def chat(backend_id: str, model: str, messages: list[dict[str, str]]) -> dict[str, Any]:
    backend = next((item for item in endpoint_specs() if item["id"] == backend_id), None)
    if not backend:
        raise ValueError("Unknown local backend")
    cleaned = []
    for message in messages[-40:]:
        role = message.get("role")
        content = message.get("content")
        if role not in {"system", "user", "assistant"} or not isinstance(content, str):
            raise ValueError("Invalid message")
        cleaned.append({"role": role, "content": content[:50_000]})
    if not cleaned or not model:
        raise ValueError("A model and at least one message are required")
    if backend["kind"] == "ollama":
        result = request_json(backend["baseUrl"] + "/api/chat", method="POST", payload={"model": model, "messages": cleaned, "stream": False}, timeout=600)
        answer = result.get("message", {}).get("content") if isinstance(result, dict) else None
    else:
        result = request_json(backend["baseUrl"] + "/v1/chat/completions", method="POST", payload={"model": model, "messages": cleaned, "stream": False}, timeout=600)
        choices = result.get("choices", []) if isinstance(result, dict) else []
        answer = choices[0].get("message", {}).get("content") if choices else None
    if not isinstance(answer, str):
        raise RuntimeError("The local runtime returned no assistant text")
    return {"content": answer, "backend": backend["name"], "model": model}


class Handler(BaseHTTPRequestHandler):
    server_version = "AnthenaraAIVault/0.2.2"

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write("[local-chat] " + format % args + "\n")

    def _json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> Any:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_BODY:
            raise ValueError("Invalid request size")
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/api/status":
            self._json(200, {
                "schemaVersion": SCHEMA_VERSION,
                "localOnly": True,
                "storesHistory": False,
                "backends": discover_backends(),
                "modelFiles": discover_gguf_files(),
                "llamaServerInstalled": bool(os.environ.get("AI_VAULT_LLAMA_SERVER", "").strip() or shutil.which("llama-server")),
            })
            return
        target = STATIC / ("index.html" if path == "/" else path.lstrip("/"))
        try:
            target = target.resolve()
            target.relative_to(STATIC.resolve())
        except (ValueError, OSError):
            self.send_error(404)
            return
        if not target.is_file():
            self.send_error(404)
            return
        body = target.read_bytes()
        content_type = "text/html; charset=utf-8" if target.suffix == ".html" else "text/plain; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        try:
            payload = self._body()
            if self.path == "/api/chat":
                result = chat(str(payload.get("backendId", "")), str(payload.get("model", "")), payload.get("messages", []))
                self._json(200, result)
                return
            if self.path == "/api/launch":
                result = launch_gguf(str(payload.get("modelId", "")))
                self._json(200, result)
                return
            self._json(404, {"error": "Not found"})
        except (ValueError, RuntimeError, HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            self._json(400, {"error": str(exc)})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--open", action="store_true", dest="open_browser")
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        raise SystemExit("Port must be between 1024 and 65535")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}"
    print(f"Anthenara AI Vault Emergency Local Chat: {url}")
    print("Local-only. Press Control-C to stop the chat interface.")
    if args.open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

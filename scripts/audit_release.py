#!/usr/bin/env python3
"""Focused deterministic audit for the emergency-chat release boundary."""

from __future__ import annotations

import ast
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON_FILES = [ROOT / "app.py", ROOT / "scripts" / "build_release.py"]
ALLOWED_TOP_LEVEL_IMPORTS = {
    "__future__", "argparse", "ast", "hashlib", "http", "json", "os", "pathlib", "re",
    "shutil", "subprocess", "sys", "threading", "time", "typing", "unittest",
    "urllib", "webbrowser", "zipfile",
}
FORBIDDEN_MANIFESTS = {
    "requirements.txt", "Pipfile", "poetry.lock", "pyproject.toml",
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
}
CREDENTIAL_ASSIGNMENT = re.compile(
    r"(?im)^\s*(?:api[_-]?key|password|secret|access[_-]?token)\s*=\s*['\"][^'\"]+['\"]"
)


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".", 1)[0])
    return modules


def main() -> int:
    errors: list[str] = []
    for path in PYTHON_FILES:
        unexpected = sorted(imported_modules(path) - ALLOWED_TOP_LEVEL_IMPORTS)
        if unexpected:
            errors.append(f"{path.relative_to(ROOT)}: non-stdlib or unapproved imports: {', '.join(unexpected)}")

    present_manifests = sorted(name for name in FORBIDDEN_MANIFESTS if (ROOT / name).exists())
    if present_manifests:
        errors.append("package-manager manifests present: " + ", ".join(present_manifests))

    for path in ROOT.rglob("*"):
        if not path.is_file() or ".runtime" in path.parts or "dist" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if CREDENTIAL_ASSIGNMENT.search(text):
            errors.append(f"{path.relative_to(ROOT)}: possible embedded credential assignment")

    app_text = (ROOT / "app.py").read_text(encoding="utf-8")
    if 'parsed.hostname in {"127.0.0.1", "localhost", "::1"}' not in app_text:
        errors.append("loopback-only endpoint guard is missing or changed")
    if '("127.0.0.1", args.port)' not in app_text:
        errors.append("loopback-only bind is missing or changed")

    if errors:
        print("DEPENDENCY AUDIT: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("DEPENDENCY AUDIT: PASS")
    print("- Python application imports are standard-library only")
    print("- no package-manager manifest found")
    print("- no embedded credential assignment found")
    print("- application bind and configured runtime endpoints are loopback-only")
    return 0


if __name__ == "__main__":
    sys.exit(main())

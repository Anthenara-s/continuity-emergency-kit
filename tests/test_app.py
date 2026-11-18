import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import app


class EmergencyChatTests(unittest.TestCase):
    def test_loopback_policy(self):
        self.assertTrue(app.is_loopback_url("http://127.0.0.1:8080"))
        self.assertTrue(app.is_loopback_url("http://localhost:1234/v1"))
        self.assertFalse(app.is_loopback_url("https://127.0.0.1:8080"))
        self.assertFalse(app.is_loopback_url("http://example.com:8080"))

    def test_model_response_parsing(self):
        self.assertEqual(app.parse_model_ids("ollama", {"models": [{"name": "b"}, {"name": "a"}]}), ["a", "b"])
        self.assertEqual(app.parse_model_ids("openai", {"data": [{"id": "z"}, {"id": "x"}]}), ["x", "z"])

    def test_gguf_scan_is_bounded_to_configured_root(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "model.gguf").write_bytes(b"GGUF")
            (root / "._model.gguf").write_bytes(b"APPLEDOUBLE")
            (root / "not-a-model.gguf").write_bytes(b"NOPE")
            (root / "mmproj-model.gguf").write_bytes(b"GGUF")
            (root / "ignore.txt").write_text("no", encoding="utf-8")
            with mock.patch.dict(os.environ, {"AI_VAULT_MODEL_DIRS": str(root)}, clear=False), mock.patch.object(app.Path, "home", return_value=root / "absent-home"):
                models = app.discover_gguf_files()
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0]["name"], "model.gguf")
        self.assertEqual(models[0]["sizeBytes"], 4)

    def test_colibri_is_a_loopback_preset(self):
        colibri = next(item for item in app.endpoint_specs() if item["id"] == "colibri")
        self.assertEqual(colibri["baseUrl"], "http://127.0.0.1:8000")
        self.assertEqual(colibri["kind"], "openai")

    def test_llama_launch_is_loopback_without_web_ui(self):
        source = Path(app.__file__).read_text(encoding="utf-8")
        self.assertIn('"--host", "127.0.0.1"', source)
        self.assertIn('"--cors-origins", "localhost"', source)
        self.assertIn('"--no-webui"', source)

    def test_custom_remote_endpoint_is_rejected(self):
        with mock.patch.dict(os.environ, {"AI_VAULT_OPENAI_ENDPOINT": "http://remote.example:9000"}, clear=False):
            with self.assertRaises(ValueError):
                app.endpoint_specs()


if __name__ == "__main__":
    unittest.main()

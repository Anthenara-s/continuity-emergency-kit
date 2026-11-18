# AI Vault Community Emergency Kit — macOS Apple Silicon

Package version 0.3.0 · 17 November 2026

This is a small, local-only emergency chat interface for testing an authorized
GGUF text model without a cloud account. It is not Home or Casita, does not
contain continuity, and does not establish identity continuity.

The repository contains the auditable application source and documentation.
Portable third-party runtimes are distributed only in the checksummed macOS
release archive. No model weights are committed or bundled.

## Start

1. Obtain a compatible text-model `.gguf` file whose license permits your use.
2. Put that file in the package's `models` folder.
3. Double-click `Start AI Vault Offline.command`.
4. If macOS asks for first-launch confirmation, Control-click the file, choose
   **Open**, inspect the publisher warning, and confirm only for this verified
   package.
5. When the browser opens, find the model under **GGUF files** and choose
   **Start with llama.cpp**.
6. Once `llama.cpp` appears as available, type a message and choose
   **Send locally**.
7. Close the Terminal window or press Control-C to stop the local interface.

No LM Studio, cloud account, password, API key, package installation, separately
installed Python, or internet connection is used during startup. Model weights
are not bundled; the person running the kit supplies an authorized GGUF file.

## Actual prerequisites

- Apple Silicon Mac (`arm64`).
- One compatible, authorized text-model `.gguf` file. Hardware and memory needs
  depend on the chosen model; begin with a small quantized model for testing.
- Ordinary permission to open local loopback ports 8080 and 8765.

Python 3.12.14 is bundled as a relocatable runtime inside this package. It is
not installed into macOS and does not modify the user's system Python.

## Offline acceptance test

1. Quit this package if it is already running.
2. Turn off Wi-Fi and disconnect Ethernet.
3. Double-click the launcher.
4. Start the GGUF model from the browser interface.
5. Ask: `Reply with exactly: OFFLINE_OK`.
6. Confirm the answer, then stop the Terminal process.
7. Re-enable networking only after the processes have stopped.

The browser address is local: `http://127.0.0.1:8765`. A browser window does
not imply internet use.

## Security choices

- AI Vault and llama.cpp bind only to `127.0.0.1`.
- llama.cpp's own Web UI is disabled.
- llama.cpp CORS is restricted to localhost.
- The runtime and source are version-pinned and checksummed.
- The bundled Python runtime is version-pinned and checksummed.
- There is no auto-update path.
- Conversations are held in the open browser page and are not written to disk
  by AI Vault.

The local runtime log is stored in `.runtime/llama-server.log` for diagnosis.
It can contain technical model-loading and performance information, but not the
conversation text in the tested configuration.

## Bundled components

- AI Vault Emergency Local Chat 0.2.2.
- llama.cpp 0.4.1 / build b10964 for macOS arm64.
- CPython 3.12.14 portable from python-build-standalone release 20260901.

Licenses and provenance receipts are stored alongside the relevant runtimes.

## Explicit limits

- This package currently supports Apple Silicon Macs only.
- It does not include model weights, passwords, API keys, conversations,
  private recovery material, or Casita/Home continuity.
- It does not download or update anything automatically.
- Compatibility and response quality depend on the selected GGUF model.
- A successful local response proves that this interface and model runtime
  worked for that test. It does not prove restoration of a prior system or
  continuity of identity.

## Before relying on it

Test the kit before relying on it in an emergency, and keep an alternative
recovery method available. This free community resource is provided as-is,
without guarantees of compatibility, availability, or successful recovery.

## Licensing

- Anthenara application code: Apache License 2.0 (`LICENSE`).
- Repository documentation: CC BY 4.0 (`DOCUMENTATION_LICENSE.md`).
- Bundled release runtimes: their own licenses (`THIRD_PARTY_NOTICES.md`).
- Model weights: not included; the model's own license applies.

Security reports should not contain conversations, model files, credentials,
private archives, personal information, or continuity material.

# Community start here

## What this kit is

The Anthenara AI Vault Community Emergency Kit is a local-only chat interface
for testing a compatible GGUF text model on an Apple Silicon Mac. The package
includes a portable Python runtime and a pinned llama.cpp runtime, so it does
not require LM Studio, a cloud account, an API key, an administrator password,
or a separate Python installation.

## What is deliberately not included

- Model weights.
- Passwords, API keys, or recovery keys.
- Conversations or private archives.
- Home or Casita continuity.
- Any automatic download, update, or cloud connection.

## Before you begin

You need:

1. An Apple Silicon Mac (`arm64`).
2. A compatible text-model `.gguf` file that you are authorized to use.
3. Enough storage and memory for that model.

Check the model's license and checksum before use. A small quantized model is
the gentlest starting point for a functional test.

## Run the test

1. Download `ai-vault-community-kit-macos-arm64-v0.3.0.tar.gz` and
   `SHA256SUMS-v0.3.0.txt`.
2. Verify that the archive's SHA-256 value matches the checksum file.
3. Extract the archive.
4. Put your authorized `.gguf` file inside the extracted `models` folder.
5. Double-click `Start AI Vault Offline.command`.
6. If macOS blocks the first launch, Control-click the launcher, choose
   **Open**, inspect the warning, and confirm only for this verified package.
7. In the local browser page, choose **Start with llama.cpp** beside your model.
8. Ask: `Reply with exactly: OFFLINE_OK`.
9. Close the Terminal window or press Control-C to stop the interface.

For the strongest test, download and verify everything first, then disconnect
Wi-Fi and Ethernet before step 4.

The local address is `http://127.0.0.1:8765`. Opening a browser at that address
does not mean that the conversation is sent to the internet.

## What a successful test means

A successful response shows that the downloaded interface, bundled runtimes,
and selected model worked together on that Mac. It does not prove that a prior
AI system, memory, relationship, or identity has been restored.

Test the kit before relying on it in an emergency, and keep an alternative
recovery method available. This free community resource is provided as-is,
without guarantees of compatibility, availability, or successful recovery.

Please do not place private archives, passwords, keys, or unencrypted
continuity material in a shared Drive folder or public bug report.

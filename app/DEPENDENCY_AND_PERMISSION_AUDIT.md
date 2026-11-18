# Dependency and permission audit

Version 0.2.2 · 24 September 2026

## Result

The application code has no cloud service, account, password, API key, package
manager, telemetry service, or non-loopback network dependency. It uses only
the Python standard library and binds to `127.0.0.1`.

## Required locally in the portable macOS package

1. An Apple Silicon Mac.
2. Compatible, authorized GGUF model weights to generate text.
3. Read access to the extracted application and chosen model file.
4. Permission to open local loopback ports. This is ordinary user-level
   operation and does not require administrator rights.

CPython 3.12.14 and llama.cpp 0.4.1 / build b10964 are bundled in the portable
package. They are not installed into macOS.

No `pip install`, login, cloud token, administrator password, incoming firewall
rule, or public/LAN port is part of the supported path.

## Platform caveats

- macOS may ask the user to confirm a downloaded `.command` file through
  Gatekeeper. That is an operating-system trust confirmation, not an
  application credential.
- This portable package does not support Intel Macs, Windows, or Linux. Those
  systems need separate verified builds.
- Model runtimes and weights have their own licenses, hardware needs, and
  integrity checks. Model weights remain separate from this package.

## Deterministic check

The underlying AI Vault Emergency Local Chat source audit checks Python imports,
embedded credential assignments, endpoint hosts, and unexpected package-manager
manifests. It is a focused release check, not a complete security certification.

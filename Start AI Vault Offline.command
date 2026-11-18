#!/bin/zsh
set -euo pipefail

ROOT="${0:A:h}"
APP="$ROOT/app"
RUNTIME="$ROOT/runtime/llama-b10964"
LLAMA_SERVER="$RUNTIME/llama-server"
PYTHON="$ROOT/python/bin/python3.12"
LOG_DIR="$ROOT/.runtime"
LLAMA_LOG="$LOG_DIR/llama-server.log"
LLAMA_PID_FILE="$APP/.runtime/llama-server.pid"

fail() {
  print "\nAI Vault could not start: $1"
  print "\nPress Return to close."
  read -r
  exit 1
}

[[ "$(uname -m)" == "arm64" ]] || fail "this portable package is for Apple Silicon Macs."
[[ -x "$PYTHON" ]] || fail "the bundled portable Python runtime is missing."
[[ -x "$LLAMA_SERVER" ]] || fail "the pinned llama-server binary is missing."

mkdir -p "$LOG_DIR"
chmod 700 "$LOG_DIR"

cleanup() {
  if [[ -f "$LLAMA_PID_FILE" ]]; then
    local launched_pid
    launched_pid="$(<"$LLAMA_PID_FILE")"
    if [[ "$launched_pid" == <-> ]] && kill -0 "$launched_pid" 2>/dev/null; then
      kill "$launched_pid" 2>/dev/null || true
      wait "$launched_pid" 2>/dev/null || true
    fi
    rm -f "$LLAMA_PID_FILE"
  fi
}
trap cleanup EXIT INT TERM HUP

MODEL_DIRS=("$ROOT/models" "$HOME/Models" "$HOME/AI Models")
if [[ -n "${AI_VAULT_MODEL_PATH:-}" ]]; then
  [[ -f "$AI_VAULT_MODEL_PATH" ]] || fail "AI_VAULT_MODEL_PATH is not a readable file."
  MODEL_DIRS=("${AI_VAULT_MODEL_PATH:h}" $MODEL_DIRS)
fi
if [[ -n "${AI_VAULT_MODEL_DIRS:-}" ]]; then
  MODEL_DIRS=("${(s.:.)AI_VAULT_MODEL_DIRS}" $MODEL_DIRS)
fi

export AI_VAULT_MODEL_DIRS="${(j.:.)MODEL_DIRS}"
export AI_VAULT_LLAMA_SERVER="$LLAMA_SERVER"
export DYLD_LIBRARY_PATH="$RUNTIME"

print "Opening AI Vault at http://127.0.0.1:8765"
print "Place an authorized text-model .gguf file in the package's models folder."
print "In the browser, choose Start with llama.cpp beside that model."
print "Close this Terminal window or press Control-C to stop the local interface."

"$PYTHON" "$APP/app.py" --open

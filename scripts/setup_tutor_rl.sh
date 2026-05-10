#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_DIR="${MODEL_DIR:-$ROOT_DIR/models}"
GGUF_FILE="${GGUF_FILE:-$MODEL_DIR/TutorRL-7B-think-Q4_K_M.gguf}"
MODEL_NAME="${OLLAMA_TUTOR_MODEL:-socrates-tutor-rl}"
HF_REPO="${HF_REPO:-mradermacher/TutorRL-7B-think-GGUF}"
HF_FILE="${HF_FILE:-TutorRL-7B-think.Q4_K_M.gguf}"

mkdir -p "$MODEL_DIR"

if [[ ! -f "$GGUF_FILE" ]]; then
  echo "Downloading $HF_REPO/$HF_FILE -> $GGUF_FILE"
  if command -v huggingface-cli >/dev/null 2>&1; then
    huggingface-cli download "$HF_REPO" "$HF_FILE" --local-dir "$MODEL_DIR" --local-dir-use-symlinks False
    if [[ -f "$MODEL_DIR/$HF_FILE" && "$MODEL_DIR/$HF_FILE" != "$GGUF_FILE" ]]; then
      mv "$MODEL_DIR/$HF_FILE" "$GGUF_FILE"
    fi
  elif command -v wget >/dev/null 2>&1; then
    wget -O "$GGUF_FILE" "https://huggingface.co/$HF_REPO/resolve/main/$HF_FILE?download=true"
  elif command -v curl >/dev/null 2>&1; then
    curl -L "https://huggingface.co/$HF_REPO/resolve/main/$HF_FILE?download=true" -o "$GGUF_FILE"
  else
    echo "Need one of: huggingface-cli, wget, curl" >&2
    exit 1
  fi
fi

TMP_MODELFILE="$(mktemp)"
sed "s#^FROM .*#FROM $GGUF_FILE#" "$ROOT_DIR/TutorRL.Modelfile" > "$TMP_MODELFILE"

echo "Creating Ollama model: $MODEL_NAME"
ollama create "$MODEL_NAME" -f "$TMP_MODELFILE"
rm -f "$TMP_MODELFILE"

echo
echo "Installed model:"
ollama list | grep "$MODEL_NAME" || true
echo
echo "Smoke test:"
OLLAMA_TUTOR_MODEL="$MODEL_NAME" python3 "$ROOT_DIR/scripts/test_tutor_rl.py"

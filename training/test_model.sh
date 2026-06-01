#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRAIN_DIR="$ROOT_DIR/training"
ADAPTER_DIR="$TRAIN_DIR/adapters/marg_darshak_gita_v4_lora"
MODEL_ID="${MODEL_ID:-mlx-community/Qwen2.5-1.5B-Instruct-4bit}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

print_error() {
  echo "[test_model] $1" >&2
}

print_info() {
  echo "[test_model] $1"
}

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  print_error "$PYTHON_BIN is not available in PATH"
  exit 1
fi

if [[ ! -d "$ADAPTER_DIR" ]]; then
  print_error "adapter directory not found: $ADAPTER_DIR"
  print_error "run training/train_lora.sh first"
  exit 1
fi

if [[ ! -f "$ADAPTER_DIR/adapters.safetensors" ]]; then
  print_error "adapter weights not found in $ADAPTER_DIR"
  print_error "expected adapters.safetensors after a successful training run"
  exit 1
fi

print_info "loading model $MODEL_ID with adapter $ADAPTER_DIR"

MODEL_ID="$MODEL_ID" ADAPTER_DIR="$ADAPTER_DIR" "$PYTHON_BIN" - <<'PY'
import os

from mlx_lm import generate, load

MODEL_ID = os.environ["MODEL_ID"]
ADAPTER_DIR = os.environ["ADAPTER_DIR"]
SYSTEM_PROMPT = (
    "You are Marg Darshak, a calm philosophical guide inspired by Indian wisdom "
    "traditions. You help users with inner battles using gentle reflection, clarity, "
    "and practical action. You are not a therapist, doctor, or religious authority."
)

PROMPTS = [
    "I feel lost and confused about my career.",
    "I know what I should do but I keep avoiding it.",
    "I am too attached to the result.",
    "I feel overwhelmed by uncertainty.",
    "What should I do when fear is stopping me from acting?",
]

model, tokenizer = load(MODEL_ID, adapter_path=ADAPTER_DIR)

for index, prompt in enumerate(PROMPTS, start=1):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    rendered_prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    response = generate(
        model,
        tokenizer,
        prompt=rendered_prompt,
        max_tokens=220,
        verbose=False,
    )
    print(f"\n=== Prompt {index} ===")
    print(f"User: {prompt}\n")
    print("Assistant:")
    print(response.strip())
PY

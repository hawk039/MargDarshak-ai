#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRAIN_DIR="$ROOT_DIR/training"
GITA_ADAPTER_DIR="$TRAIN_DIR/adapters/marg_darshak_gita_v4_lora"
MERGED_V23_ADAPTER_DIR="$TRAIN_DIR/adapters/marg_darshak_merged_v23_lora"
EXPANDED_V1_ADAPTER_DIR="$TRAIN_DIR/adapters/marg_darshak_expanded_v1_lora"
MODEL_ID="${MODEL_ID:-mlx-community/Qwen2.5-1.5B-Instruct-4bit}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

print_error() {
  echo "[test_model_expanded_v1] $1" >&2
}

print_info() {
  echo "[test_model_expanded_v1] $1"
}

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  print_error "$PYTHON_BIN is not available in PATH"
  exit 1
fi

if ! "$PYTHON_BIN" -c "import mlx_lm" >/dev/null 2>&1; then
  print_error "mlx_lm is not importable from $PYTHON_BIN"
  exit 1
fi

if [[ ! -d "$EXPANDED_V1_ADAPTER_DIR" ]]; then
  print_error "expanded_v1 adapter directory not found: $EXPANDED_V1_ADAPTER_DIR"
  print_error "run training/train_lora_expanded_v1.sh first"
  exit 1
fi

if [[ ! -f "$EXPANDED_V1_ADAPTER_DIR/adapters.safetensors" ]]; then
  print_error "expanded_v1 adapter weights not found in $EXPANDED_V1_ADAPTER_DIR"
  print_error "expected adapters.safetensors after a successful expanded_v1 training run"
  exit 1
fi

print_info "loading comparison models for expanded_v1 testing"

MODEL_ID="$MODEL_ID" \
GITA_ADAPTER_DIR="$GITA_ADAPTER_DIR" \
MERGED_V23_ADAPTER_DIR="$MERGED_V23_ADAPTER_DIR" \
EXPANDED_V1_ADAPTER_DIR="$EXPANDED_V1_ADAPTER_DIR" \
"$PYTHON_BIN" - <<'PY'
import os

from mlx_lm import generate, load

MODEL_ID = os.environ["MODEL_ID"]
GITA_ADAPTER_DIR = os.environ["GITA_ADAPTER_DIR"]
MERGED_V23_ADAPTER_DIR = os.environ["MERGED_V23_ADAPTER_DIR"]
EXPANDED_V1_ADAPTER_DIR = os.environ["EXPANDED_V1_ADAPTER_DIR"]
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


def render_and_generate(model, tokenizer, prompt: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    rendered_prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    return generate(
        model,
        tokenizer,
        prompt=rendered_prompt,
        max_tokens=220,
        verbose=False,
    ).strip()


models = []
base_model, base_tokenizer = load(MODEL_ID)
models.append(("Base Qwen", base_model, base_tokenizer))

if os.path.exists(os.path.join(GITA_ADAPTER_DIR, "adapters.safetensors")):
    gita_model, gita_tokenizer = load(MODEL_ID, adapter_path=GITA_ADAPTER_DIR)
    models.append(("Gita LoRA", gita_model, gita_tokenizer))

if os.path.exists(os.path.join(MERGED_V23_ADAPTER_DIR, "adapters.safetensors")):
    merged_v23_model, merged_v23_tokenizer = load(MODEL_ID, adapter_path=MERGED_V23_ADAPTER_DIR)
    models.append(("Merged v23 LoRA", merged_v23_model, merged_v23_tokenizer))

expanded_v1_model, expanded_v1_tokenizer = load(MODEL_ID, adapter_path=EXPANDED_V1_ADAPTER_DIR)
models.append(("Expanded v1 LoRA", expanded_v1_model, expanded_v1_tokenizer))

for index, prompt in enumerate(PROMPTS, start=1):
    print(f"\n=== Prompt {index} ===")
    print(f"User: {prompt}\n")
    for label, model, tokenizer in models:
        print(f"[{label}]")
        print(render_and_generate(model, tokenizer, prompt))
        print()
PY

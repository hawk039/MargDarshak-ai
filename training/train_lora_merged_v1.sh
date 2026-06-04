#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRAIN_DIR="$ROOT_DIR/training"
DATA_FILE="$TRAIN_DIR/data/train_merged_v1.jsonl"
CONFIG_FILE="$TRAIN_DIR/configs/qwen_1_5b_lora_merged_v1.yaml"
ADAPTER_DIR="$TRAIN_DIR/adapters/marg_darshak_merged_v1_lora"
OUTPUT_DIR="$TRAIN_DIR/outputs"
LOG_FILE="$OUTPUT_DIR/train_merged_v1_$(date +"%Y%m%d_%H%M%S").log"
PYTHON_BIN="${PYTHON_BIN:-python3}"

MODEL_ID="${MODEL_ID:-mlx-community/Qwen2.5-1.5B-Instruct-4bit}"
BASE_MODEL_NOTE="Qwen/Qwen2.5-1.5B-Instruct"

mkdir -p "$OUTPUT_DIR" "$TRAIN_DIR/adapters"

print_error() {
  echo "[train_lora_merged_v1] $1" >&2
}

print_info() {
  echo "[train_lora_merged_v1] $1"
}

if [[ ! -f "$DATA_FILE" ]]; then
  print_error "dataset not found at $DATA_FILE"
  print_error "expected a JSONL file at training/data/train_merged_v1.jsonl"
  exit 1
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
  print_error "config file not found at $CONFIG_FILE"
  exit 1
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  print_error "$PYTHON_BIN is not available in PATH"
  exit 1
fi

if ! "$PYTHON_BIN" -c "import mlx_lm" >/dev/null 2>&1; then
  print_error "mlx_lm is not importable from $PYTHON_BIN"
  print_error "install MLX-LM training extras with: pip install \"mlx-lm[train]\""
  exit 1
fi

print_info "validating merged dataset before training"
if ! "$PYTHON_BIN" "$TRAIN_DIR/prepare_dataset.py" --dataset "$DATA_FILE"; then
  print_error "dataset validation failed"
  exit 1
fi

print_info "target base model: $BASE_MODEL_NOTE"
print_info "MLX runtime model: $MODEL_ID"
print_info "warming model cache; this will download the model if it is missing"
if ! "$PYTHON_BIN" -m mlx_lm generate --model "$MODEL_ID" --prompt "ping" --max-tokens 1 >/dev/null 2>&1; then
  print_error "model warm-up failed"
  print_error "if this is the first run, confirm network access and Hugging Face availability"
  exit 1
fi

print_info "starting merged LoRA training"
print_info "config: $CONFIG_FILE"
print_info "dataset: $DATA_FILE"
print_info "adapter output: $ADAPTER_DIR"
print_info "log file: $LOG_FILE"

set +e
"$PYTHON_BIN" -m mlx_lm lora --config "$CONFIG_FILE" 2>&1 | tee "$LOG_FILE"
TRAIN_EXIT=${PIPESTATUS[0]}
set -e

if [[ $TRAIN_EXIT -ne 0 ]]; then
  print_error "training failed with exit code $TRAIN_EXIT"
  print_error "check the log at $LOG_FILE"
  print_error "for an M1 8GB machine, try fewer iters, fewer layers, or confirm no other heavy apps are open"
  exit "$TRAIN_EXIT"
fi

print_info "training finished successfully"
print_info "adapters should now be available under $ADAPTER_DIR"

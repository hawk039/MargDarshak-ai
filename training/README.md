# Training

## Overview

This directory contains the first local LoRA fine-tuning setup for Marg Darshak using MLX-LM on Apple Silicon.

The initial experiment targets:

* Base family: `Qwen2.5-1.5B-Instruct`
* MLX training model: `mlx-community/Qwen2.5-1.5B-Instruct-4bit`
* Dataset: `training/data/train.jsonl`
* Output adapter: `training/adapters/marg_darshak_gita_v4_lora`

The setup is intentionally conservative for a MacBook M1 with 8GB RAM. It favors stability over speed.

## Environment Setup

Recommended:

* Python `3.11+`
* macOS on Apple Silicon
* a virtual environment dedicated to this repository

Example:

```bash
cd /Users/mayankdhyani/PycharmProjects/marg-darshak-ai-service
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
```

## Installation

Install MLX-LM with training extras:

```bash
pip install "mlx-lm[train]"
```

Optional but useful:

```bash
pip install huggingface_hub
```

## Dataset Validation

Validate the training dataset before training:

```bash
python3 training/prepare_dataset.py --dataset training/data/train.jsonl
```

What it checks:

* every line is valid JSON
* every record has a `messages` list
* message roles are limited to `system`, `user`, and `assistant`
* each example includes all three roles

The validator prints:

* total examples
* total valid examples
* total invalid examples
* 3 random examples

If validation fails, it exits with a non-zero status.

## Training

Run the first LoRA experiment:

```bash
export PYTHON_BIN=python3
bash training/train_lora.sh
```

What the script does:

* verifies the dataset and config exist
* verifies `mlx-lm` is installed
* validates `training/data/train.jsonl`
* warms the model cache and downloads the model if needed
* starts LoRA training with conservative MLX-LM settings
* writes logs under `training/outputs/`

The scripts use the current MLX-LM CLI style:

```bash
python -m mlx_lm generate ...
python -m mlx_lm lora ...
```

The current config is:

* batch size `1`
* gradient accumulation `4`
* LoRA layers `4`
* gradient checkpointing enabled
* short experimental run for first-pass testing

## Testing

After training finishes, test the adapter:

```bash
export PYTHON_BIN=python3
bash training/test_model.sh
```

This script loads:

* `mlx-community/Qwen2.5-1.5B-Instruct-4bit`
* `training/adapters/marg_darshak_gita_v4_lora`

It then runs several sample prompts and prints the responses clearly.

## Outputs

Adapter outputs:

* `training/adapters/marg_darshak_gita_v4_lora/`

Training logs:

* `training/outputs/`

Active dataset copy:

* `training/data/train.jsonl`

Configuration:

* `training/configs/qwen_1_5b_lora.yaml`

## Troubleshooting

### Out of Memory

If the M1 8GB machine runs out of memory:

* close other heavy applications
* reduce `iters`
* reduce `num_layers`
* keep `batch_size: 1`
* keep gradient checkpointing enabled

If needed, make the config even smaller before retrying.

### Low Disk Space

If model download or training fails because of disk space:

* clear old files under `training/outputs/`
* remove unused adapter runs under `training/adapters/`
* check that the base model cache has enough free space

### Corrupt Dataset

If validation fails:

* rerun `python training/prepare_dataset.py --dataset training/data/train.jsonl`
* inspect the reported line numbers
* fix malformed JSON or invalid message roles before training

## Commands

Validate dataset:

```bash
python3 training/prepare_dataset.py --dataset training/data/train.jsonl
```

Train LoRA:

```bash
bash training/train_lora.sh
```

Test the fine-tuned adapter:

```bash
bash training/test_model.sh
```

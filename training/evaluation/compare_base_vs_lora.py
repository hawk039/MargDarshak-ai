#!/usr/bin/env python3
"""Generate side-by-side evaluation outputs for base Qwen and Marg Darshak LoRA."""

from __future__ import annotations

import json
import os
from pathlib import Path

from mlx_lm import generate, load
from mlx_lm.sample_utils import make_sampler


ROOT_DIR = Path(__file__).resolve().parents[2]
EVAL_DIR = ROOT_DIR / "training" / "evaluation"
PROMPTS_PATH = EVAL_DIR / "eval_prompts.json"
RESULTS_PATH = EVAL_DIR / "results.json"
LORA_PATH = ROOT_DIR / "training" / "adapters" / "marg_darshak_gita_v4_lora"
MODEL_ID = "mlx-community/Qwen2.5-1.5B-Instruct-4bit"
SYSTEM_PROMPT = (
    "You are Marg Darshak, a calm philosophical guide inspired by Indian wisdom "
    "traditions. You help users with inner battles using gentle reflection, clarity, "
    "and practical action. You are not a therapist, doctor, or religious authority."
)
GENERATION_CONFIG = {
    "max_tokens": 220,
    "temp": 0.7,
    "top_p": 0.9,
    "verbose": False,
}


def load_prompts() -> list[dict[str, object]]:
    """Load evaluation prompts from JSON."""

    with PROMPTS_PATH.open("r", encoding="utf-8") as handle:
        prompts = json.load(handle)
    if not isinstance(prompts, list) or not prompts:
        raise ValueError("evaluation prompt file must contain a non-empty list")
    return prompts


def build_chat_prompt(tokenizer, prompt: str) -> str:
    """Render a prompt using the tokenizer chat template."""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )


def generate_response(model, tokenizer, prompt: str) -> str:
    """Generate one response using a shared generation config."""

    rendered_prompt = build_chat_prompt(tokenizer, prompt)
    sampler = make_sampler(
        GENERATION_CONFIG["temp"],
        GENERATION_CONFIG["top_p"],
        0.0,
        1,
    )
    response = generate(
        model,
        tokenizer,
        prompt=rendered_prompt,
        max_tokens=GENERATION_CONFIG["max_tokens"],
        verbose=GENERATION_CONFIG["verbose"],
        sampler=sampler,
    )
    return response.strip()


def main() -> int:
    """Run the base-vs-LoRA comparison and save JSON results."""

    if not PROMPTS_PATH.exists():
        raise FileNotFoundError(f"evaluation prompt file not found: {PROMPTS_PATH}")
    if not LORA_PATH.exists():
        raise FileNotFoundError(f"LoRA adapter directory not found: {LORA_PATH}")

    prompts = load_prompts()

    print(f"loading base model: {MODEL_ID}")
    base_model, base_tokenizer = load(MODEL_ID)

    print(f"loading lora model: {MODEL_ID} + {LORA_PATH}")
    lora_model, lora_tokenizer = load(MODEL_ID, adapter_path=str(LORA_PATH))

    results: list[dict[str, object]] = []
    for item in prompts:
        prompt_id = item["id"]
        prompt_text = str(item["prompt"])
        print(f"evaluating prompt {prompt_id}: {prompt_text}")

        base_response = generate_response(base_model, base_tokenizer, prompt_text)
        lora_response = generate_response(lora_model, lora_tokenizer, prompt_text)

        results.append(
            {
                "id": prompt_id,
                "prompt": prompt_text,
                "base_response": base_response,
                "lora_response": lora_response,
            }
        )

    RESULTS_PATH.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"saved comparison results to {RESULTS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

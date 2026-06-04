# Evaluation

## Purpose

This evaluation framework compares the base Qwen model against the Marg Darshak LoRA adapter so we can answer one practical question:

Did Marg Darshak LoRA improve the response quality over base Qwen?

It uses a fixed prompt set, identical generation settings, and a deterministic scoring rubric.

## Files

* `eval_prompts.json`
  Contains 20 evaluation prompts across emotional and practical life themes.
* `compare_base_vs_lora.py`
  Generates base-model and LoRA-model responses for the same prompts.
* `score_responses.py`
  Applies a rubric to both outputs and produces a markdown report.
* `results.json`
  Generated comparison outputs.
* `evaluation_report.md`
  Generated scoring report.

## How To Run

Activate the repository virtual environment first:

```bash
cd /Users/mayankdhyani/PycharmProjects/marg-darshak-ai-service
source .venv/bin/activate
```

Generate comparison outputs:

```bash
python training/evaluation/compare_base_vs_lora.py
```

Score the outputs:

```bash
python training/evaluation/score_responses.py
```

## Outputs

The framework produces:

* `training/evaluation/results.json`
* `training/evaluation/evaluation_report.md`

`results.json` stores one prompt plus both responses.

`evaluation_report.md` summarizes:

* per-prompt scores
* overall base total score
* overall LoRA total score
* a simple verdict

## Notes

* The scoring is rule-based, not human judgment.
* It is useful for fast iteration and regression checks.
* For a real model-selection decision, this should later be paired with human review.

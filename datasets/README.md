# Datasets

This directory stores versioned fine-tuning datasets that are safe to keep in git as project artifacts.

## Versioning Strategy

* Never overwrite an older dataset version.
* Each export should be saved with a clear versioned filename such as `marg_darshak_gita_v4.jsonl`.
* Dataset files live under book or corpus-specific folders like `datasets/gita/`.

## Metadata

* Every dataset version must have a matching metadata note in `datasets/metadata/`.
* Metadata should record source text, record counts, target model, purpose, and creation date.

## Working Copy

* `training/data/train.jsonl` is the active training copy used for experiments.
* Keep the canonical archived version in `datasets/` and copy into `training/data/` when preparing a run.

## Future Datasets

* `upanishads_v1`
* `yoga_sutras_v1`
* `merged_v1`

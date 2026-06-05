# Expanded v1 Training Notes

- dataset size: `300`
- source: approved Gita + Upanishad wisdom entries
- training dataset: [training/data/train_expanded_v1.jsonl](/Users/mayankdhyani/PycharmProjects/marg-darshak-ai-service/training/data/train_expanded_v1.jsonl)
- target model family: `Qwen2.5-1.5B-Instruct`
- MLX runtime model: `mlx-community/Qwen2.5-1.5B-Instruct-4bit`
- adapter output: [training/adapters/marg_darshak_expanded_v1_lora](/Users/mayankdhyani/PycharmProjects/marg-darshak-ai-service/training/adapters/marg_darshak_expanded_v1_lora)
- purpose: LoRA v3
- expected improvement: less template lock-in, broader scenario handling

## Training Shape

- batch size: `1`
- grad accumulation: `4`
- learning rate: `1.0e-5`
- iterations: `220`
- LoRA layers: `4`
- gradient checkpointing: `true`
- mask prompt: `true`

## Comparison Targets

The evaluation pass after training should compare:

- base Qwen
- Gita LoRA
- merged_v23 LoRA
- expanded_v1 LoRA

## Notes

- This setup keeps older adapters untouched.
- The expanded dataset is larger and more scenario-diverse than the earlier merged training sets.
- The main expected gain is broader user-problem coverage with less scaffold repetition than prior runs.

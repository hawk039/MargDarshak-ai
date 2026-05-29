"""Pipeline that orchestrates training dataset generation."""

from app.models.training_example import TrainingExample
from app.services.training_data_generation_service import TrainingDataGenerationService


class GenerateTrainingDatasetPipeline:
    """Convert approved training examples into exportable JSONL lines."""

    def __init__(
        self,
        training_data_generation_service: TrainingDataGenerationService | None = None,
    ) -> None:
        self.training_data_generation_service = (
            training_data_generation_service or TrainingDataGenerationService()
        )

    def run(self, training_examples: list[TrainingExample]) -> list[str]:
        """Generate JSONL output lines from training examples."""

        return self.training_data_generation_service.build_jsonl_lines(training_examples)

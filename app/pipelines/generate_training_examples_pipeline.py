"""Pipeline that orchestrates training example generation from wisdom entries."""

from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.training_example import TrainingExample
from app.models.wisdom_entry import WisdomEntry
from app.services.training_data_generation_service import TrainingDataGenerationService


@dataclass(slots=True)
class TrainingExampleGenerationBatchResult:
    generated_examples: list[TrainingExample]
    generated_count: int
    skipped_count: int
    processed_wisdom_entries: int


class GenerateTrainingExamplesPipeline:
    def __init__(self, training_data_generation_service: TrainingDataGenerationService | None = None) -> None:
        self.training_data_generation_service = training_data_generation_service or TrainingDataGenerationService()

    async def run(self, wisdom_entries: list[WisdomEntry], db: AsyncSession) -> list[TrainingExample]:
        result = await self.run_batched(wisdom_entries=wisdom_entries, db=db, replace_existing=True)
        return result.generated_examples

    async def run_batched(
        self,
        wisdom_entries: list[WisdomEntry],
        db: AsyncSession,
        *,
        replace_existing: bool = False,
        commit_every_examples: int = 10,
    ) -> TrainingExampleGenerationBatchResult:
        if not wisdom_entries:
            return TrainingExampleGenerationBatchResult([], 0, 0, 0)
        wisdom_entry_ids = [wisdom_entry.id for wisdom_entry in wisdom_entries]
        if replace_existing:
            await db.execute(delete(TrainingExample).where(TrainingExample.wisdom_entry_id.in_(wisdom_entry_ids)))
            await db.commit()
            eligible_wisdom_entries = wisdom_entries
            skipped_count = 0
        else:
            existing_result = await db.execute(
                select(TrainingExample.wisdom_entry_id).where(TrainingExample.wisdom_entry_id.in_(wisdom_entry_ids))
            )
            existing_ids = set(existing_result.scalars().all())
            eligible_wisdom_entries = [wisdom_entry for wisdom_entry in wisdom_entries if wisdom_entry.id not in existing_ids]
            skipped_count = len(wisdom_entries) - len(eligible_wisdom_entries)
        generated_examples = self.training_data_generation_service.generate_examples_for_wisdom_entries(eligible_wisdom_entries)
        pending_examples = 0
        for example in generated_examples:
            db.add(TrainingExample(
                wisdom_entry_id=example.wisdom_entry_id,
                user_problem=example.user_problem,
                assistant_response=example.assistant_response,
                tone=example.tone,
                safety_category=example.safety_category,
                source_references=example.source_references,
                approved_for_finetune=example.approved_for_finetune,
            ))
            pending_examples += 1
            if pending_examples >= commit_every_examples:
                await db.commit()
                pending_examples = 0
        if pending_examples:
            await db.commit()
        if not eligible_wisdom_entries:
            return TrainingExampleGenerationBatchResult([], 0, skipped_count, len(wisdom_entries))
        result = await db.execute(
            select(TrainingExample)
            .where(TrainingExample.wisdom_entry_id.in_([wisdom_entry.id for wisdom_entry in eligible_wisdom_entries]))
            .order_by(TrainingExample.created_at.desc())
        )
        return TrainingExampleGenerationBatchResult(
            list(result.scalars().all()),
            len(generated_examples),
            skipped_count,
            len(wisdom_entries),
        )

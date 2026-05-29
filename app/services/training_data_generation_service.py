"""Services for generating diverse training examples."""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from difflib import SequenceMatcher

from app.models.training_example import TrainingExample
from app.models.wisdom_entry import WisdomEntry


SYSTEM_PROMPT = (
    "You are Marg Darshak, a calm philosophical guide inspired by Indian wisdom "
    "traditions. You help users with inner battles using gentle reflection, clarity, "
    "and practical action. You are not a therapist, doctor, or religious authority."
)

DEFAULT_TONE = "calm_philosophical"
DEFAULT_SAFETY_CATEGORY = "normal"
MINIMUM_APPROVED_CONFIDENCE = 80.0
MAX_OPENING_REPETITIONS = 5
SIMILARITY_THRESHOLD = 0.94
SIMILARITY_LOOKBACK = 80
MIN_RESPONSE_WORDS = 80
MAX_RESPONSE_WORDS = 150
CORRUPTION_PATTERN = re.compile(r"[{}@ïÌœ]|H¥|�|jkhh|vijkhh|iijkhh|viiijkhh")

USER_PROBLEM_TEMPLATES = {
    "anxiety": [
        "I feel anxious about what might happen next and I cannot settle my mind.",
        "My mind keeps racing about the future and I do not know how to stay steady.",
        "I am overwhelmed by worry and I need a calmer way to face this situation.",
    ],
    "grief": [
        "I am carrying grief and it feels hard to move through the day with strength.",
        "A deep sense of loss is making everything feel heavy and unclear.",
        "I am grieving and I need a grounded way to hold this pain without collapsing.",
    ],
    "fear": [
        "Fear is stopping me from taking the next step even though I know it matters.",
        "I keep shrinking back because I am afraid of failure and its consequences.",
        "I want to act bravely, but fear keeps taking over my mind.",
    ],
    "duty": [
        "I know what my responsibility is, but I keep resisting it.",
        "I am torn between comfort and doing what I know is my duty.",
        "How do I stay committed to my responsibilities without feeling burdened?",
    ],
    "attachment": [
        "I am too attached to a specific outcome and it is disturbing my peace.",
        "My expectations are making me suffer when things do not go my way.",
        "How do I work sincerely without clinging so tightly to results?",
    ],
    "anger": [
        "Anger rises quickly in me and I regret what it does to my words and actions.",
        "I feel consumed by frustration and I want a wiser way to respond.",
        "How do I keep anger from ruling my decisions?",
    ],
    "confusion": [
        "I feel confused about what the right path is and my mind keeps wavering.",
        "I cannot tell whether I am acting from clarity or confusion.",
        "Everything feels mentally tangled and I need a steadier perspective.",
    ],
    "discipline": [
        "I want more discipline, but I keep breaking my own intentions.",
        "My practice becomes inconsistent whenever life gets difficult.",
        "How can I build steadiness and discipline without becoming harsh on myself?",
    ],
    "devotion": [
        "I want to live with more devotion, but I feel spiritually distracted.",
        "My heart longs for deeper trust, yet I keep drifting into restlessness.",
        "How do I bring devotion into daily life in a sincere way?",
    ],
    "self-control": [
        "I struggle to control my impulses when emotions become intense.",
        "I know what is wise, but I do not always have the self-control to follow it.",
        "How can I become more inwardly steady when temptation or agitation appears?",
    ],
    "default": [
        "I am facing an inner struggle and I want to respond with more clarity and balance.",
        "I feel unsettled by my situation and I need a wiser way to act.",
        "How can I meet this challenge with calm reflection instead of reactivity?",
    ],
}

OPENING_STYLES = [
    "This {emotion_word} stretch of life can feel especially tight when {focus_word} is under strain.",
    "There are moments when {emotion_word} fills the whole horizon, yet a steadier response is still possible.",
    "It is understandable that {emotion_word} is loud right now, especially when {focus_word} feels unsettled.",
    "When the heart is carrying {emotion_word}, even simple decisions can feel unusually heavy.",
    "A season shaped by {emotion_word} often makes {focus_word} seem harder than it really is.",
    "Inner pressure grows quickly when {emotion_word} and {focus_word} start pulling in different directions.",
    "Many people reach this kind of crossroads when {emotion_word} clouds their sense of {focus_word}.",
    "A mind touched by {emotion_word} usually needs steadiness before it can see {focus_word} clearly.",
    "This kind of struggle often appears when {emotion_word} tightens around questions of {focus_word}.",
    "When {emotion_word} rises, it can make {focus_word} feel distant even when it is still available.",
    "The weight you describe makes sense because {emotion_word} can narrow the mind and blur {focus_word}.",
    "What feels difficult here is not weakness; it is the strain that appears when {emotion_word} unsettles {focus_word}.",
]

STRUCTURE_PATTERNS = [
    ("ack", "principle", "explanation", "action", "closing"),
    ("ack", "explanation", "principle", "action", "closing"),
    ("ack", "principle", "action", "explanation", "closing"),
    ("ack", "example", "principle", "action", "closing"),
    ("ack", "principle", "explanation", "reframe", "action"),
    ("ack", "reframe", "principle", "action", "closing"),
    ("ack", "example", "explanation", "principle", "action"),
    ("ack", "principle", "reframe", "action", "closing"),
]


@dataclass(slots=True)
class GeneratedTrainingExample:
    """In-memory representation of a generated training example."""

    wisdom_entry_id: int
    user_problem: str
    assistant_response: str
    tone: str
    safety_category: str
    source_references: list[str]
    approved_for_finetune: bool


class TrainingDataGenerationService:
    """Build deterministic, varied training examples and fine-tuning JSONL output."""

    def is_training_eligible(self, wisdom_entry: WisdomEntry) -> bool:
        """Return whether a wisdom entry is approved for training example generation."""

        return (
            (wisdom_entry.principle_status or "needs_review") == "approved"
            and (wisdom_entry.confidence_score or 0.0) >= MINIMUM_APPROVED_CONFIDENCE
            and bool(self._clean_text(wisdom_entry.extracted_principle))
        )

    def generate_examples_for_wisdom_entries(
        self,
        wisdom_entries: list[WisdomEntry],
    ) -> list[GeneratedTrainingExample]:
        """Generate a diverse set of training examples for many wisdom entries."""

        generated_examples: list[GeneratedTrainingExample] = []
        opening_counts: Counter[str] = Counter()
        normalized_responses: list[str] = []

        for wisdom_entry in wisdom_entries:
            generated_examples.extend(
                self._generate_examples_for_wisdom_entry(
                    wisdom_entry=wisdom_entry,
                    opening_counts=opening_counts,
                    normalized_responses=normalized_responses,
                )
            )

        return generated_examples

    def generate_examples_for_wisdom_entry(
        self,
        wisdom_entry: WisdomEntry,
    ) -> list[GeneratedTrainingExample]:
        """Backwards-compatible single-entry generation wrapper."""

        return self.generate_examples_for_wisdom_entries([wisdom_entry])

    def build_jsonl_lines(self, training_examples: list[TrainingExample]) -> list[str]:
        """Convert training examples into JSONL lines for future fine-tuning."""

        jsonl_lines: list[str] = []
        for example in training_examples:
            payload = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": example.user_problem},
                    {"role": "assistant", "content": example.assistant_response},
                ]
            }
            jsonl_lines.append(json.dumps(payload, ensure_ascii=False))
        return jsonl_lines

    def _generate_examples_for_wisdom_entry(
        self,
        wisdom_entry: WisdomEntry,
        opening_counts: Counter[str],
        normalized_responses: list[str],
    ) -> list[GeneratedTrainingExample]:
        """Generate three diverse examples for a single wisdom entry."""

        if not self.is_training_eligible(wisdom_entry):
            return []

        user_problems = self._build_user_problems(wisdom_entry)
        source_references = self._build_source_references(wisdom_entry)
        generated_examples: list[GeneratedTrainingExample] = []

        for example_index, user_problem in enumerate(user_problems):
            assistant_response = self._build_response_with_guards(
                wisdom_entry=wisdom_entry,
                user_problem=user_problem,
                example_index=example_index,
                opening_counts=opening_counts,
                normalized_responses=normalized_responses,
            )
            generated_examples.append(
                GeneratedTrainingExample(
                    wisdom_entry_id=wisdom_entry.id,
                    user_problem=user_problem,
                    assistant_response=assistant_response,
                    tone=DEFAULT_TONE,
                    safety_category=DEFAULT_SAFETY_CATEGORY,
                    source_references=source_references,
                    approved_for_finetune=False,
                )
            )

        return generated_examples

    def _build_response_with_guards(
        self,
        wisdom_entry: WisdomEntry,
        user_problem: str,
        example_index: int,
        opening_counts: Counter[str],
        normalized_responses: list[str],
    ) -> str:
        """Build one response while guarding against repeated openings and similar bodies."""

        context = self._build_response_context(wisdom_entry, user_problem, example_index)
        base_seed = wisdom_entry.id * 17 + example_index * 5
        opening_candidates = self._ordered_indices(len(OPENING_STYLES), base_seed)
        structure_candidates = self._ordered_indices(len(STRUCTURE_PATTERNS), base_seed * 3 + 7)

        best_response: str | None = None
        best_opening_key: str | None = None
        best_score = -1

        for opening_index in opening_candidates:
            opening_sentence = self._build_opening_sentence(context, opening_index)
            opening_key = self._opening_key(opening_sentence)
            opening_penalty = 1 if opening_counts[opening_key] >= MAX_OPENING_REPETITIONS else 0

            for structure_index in structure_candidates:
                response = self._compose_response(context, opening_sentence, structure_index)
                normalized_response = self._normalize_response(response)
                if self._is_too_similar(normalized_response, normalized_responses):
                    continue

                score = 10 - opening_penalty
                if score > best_score:
                    best_score = score
                    best_response = response
                    best_opening_key = opening_key
                if opening_penalty == 0:
                    opening_counts[opening_key] += 1
                    normalized_responses.append(normalized_response)
                    return response

        if best_response is None or best_opening_key is None:
            fallback_opening_index = opening_candidates[0]
            fallback_structure_index = structure_candidates[0]
            fallback_opening = self._build_opening_sentence(context, fallback_opening_index)
            best_response = self._compose_response(context, fallback_opening, fallback_structure_index)
            best_opening_key = self._opening_key(fallback_opening)

        opening_counts[best_opening_key] += 1
        normalized_responses.append(self._normalize_response(best_response))
        return best_response

    def _build_response_context(
        self,
        wisdom_entry: WisdomEntry,
        user_problem: str,
        example_index: int,
    ) -> dict[str, str]:
        """Build reusable response fragments for one example."""

        emotional_tags = list(wisdom_entry.emotional_tags or [])
        philosophical_tags = list(wisdom_entry.philosophical_tags or [])
        use_cases = list(wisdom_entry.use_cases or [])

        emotion = emotional_tags[0] if emotional_tags else "strain"
        focus = self._focus_word(wisdom_entry, philosophical_tags)
        principle = self._clean_text(wisdom_entry.extracted_principle) or (
            self._clean_text(wisdom_entry.translation) or "steady action matters more than restless reaction."
        )
        principle = self._remove_forbidden_phrases(principle)

        return {
            "emotion": emotion,
            "emotion_word": self._emotion_word(emotion),
            "focus_word": focus,
            "ack": self._build_acknowledgement(user_problem, emotion, focus, example_index),
            "principle": self._build_principle_sentence(principle, philosophical_tags, focus),
            "explanation": self._build_explanation_sentence(wisdom_entry, emotion, focus),
            "example": self._build_example_sentence(emotion, focus),
            "reframe": self._build_reframe_sentence(philosophical_tags, focus),
            "action": self._build_action_sentence(wisdom_entry, emotional_tags, philosophical_tags, use_cases),
            "closing": self._build_closing_sentence(emotion, focus, example_index),
        }

    def _compose_response(
        self,
        context: dict[str, str],
        opening_sentence: str,
        structure_index: int,
    ) -> str:
        """Compose and normalize one response from a selected structure."""

        parts = [opening_sentence]
        for component_name in STRUCTURE_PATTERNS[structure_index]:
            parts.append(context[component_name])

        response = " ".join(self._dedupe_adjacent(parts))
        response = self._clean_text(response) or ""
        response = self._enforce_length_bounds(response, context)
        return response

    def _build_user_problems(self, wisdom_entry: WisdomEntry) -> list[str]:
        """Generate three deterministic user problems from tags and use cases."""

        selected_tag = next(iter(wisdom_entry.emotional_tags), None)
        template_key = selected_tag if selected_tag in USER_PROBLEM_TEMPLATES else "default"
        user_problems = list(USER_PROBLEM_TEMPLATES[template_key][:2])

        if wisdom_entry.use_cases:
            user_problems.append(self._problem_from_use_case(wisdom_entry.use_cases[0]))
        else:
            user_problems.append(USER_PROBLEM_TEMPLATES[template_key][2])

        if len(user_problems) < 3:
            for problem in USER_PROBLEM_TEMPLATES[template_key]:
                if problem not in user_problems:
                    user_problems.append(problem)
                if len(user_problems) == 3:
                    break
        return user_problems[:3]

    def _problem_from_use_case(self, use_case: str) -> str:
        """Convert a use case phrase into a user-facing problem prompt."""

        normalized_use_case = use_case.rstrip(".")
        return f"I am working on {normalized_use_case}, but I keep losing clarity and steadiness."

    def _build_opening_sentence(self, context: dict[str, str], opening_index: int) -> str:
        """Return one varied opening sentence."""

        return OPENING_STYLES[opening_index].format(
            emotion_word=context["emotion_word"],
            focus_word=context["focus_word"],
        )

    def _build_acknowledgement(
        self,
        user_problem: str,
        emotion: str,
        focus: str,
        example_index: int,
    ) -> str:
        """Return an emotional acknowledgement sentence."""

        if example_index == 0:
            return (
                f"Your struggle makes sense because {emotion} can narrow attention and make {focus} feel farther away than it is."
            )
        if example_index == 1:
            return (
                f"This is a human place to be, and {emotion} often becomes louder when {focus} feels uncertain."
            )
        return (
            f"You are not failing here; you are meeting the kind of pressure that appears when {emotion} collides with the wish to live with {focus}."
        )

    def _build_principle_sentence(
        self,
        principle: str,
        philosophical_tags: list[str],
        focus: str,
    ) -> str:
        """Return a calm explanation of the core principle."""

        if principle.lower().startswith(("that ", "this ", "one ")):
            principle_text = principle[0].upper() + principle[1:]
        else:
            principle_text = f"The central lesson is that {principle[0].lower() + principle[1:]}"

        if len(principle_text.split()) < 12:
            principle_text = (
                f"{principle_text.rstrip('.')} This points the mind back toward {focus} instead of scattered reaction."
            )
        return principle_text.rstrip(".") + "."

    def _build_explanation_sentence(
        self,
        wisdom_entry: WisdomEntry,
        emotion: str,
        focus: str,
    ) -> str:
        """Return a sentence connecting the principle to inner conflict."""

        principle_text = (wisdom_entry.extracted_principle or "").lower()
        philosophical_tags = set(wisdom_entry.philosophical_tags or [])

        if "dharma" in philosophical_tags or "duty" in principle_text:
            return "The teaching does not ask you to become cold; it asks you to act from responsibility rather than from panic or avoidance."
        if "karma" in philosophical_tags or "renunciation" in philosophical_tags:
            return "The point is to release the fever around results so effort becomes cleaner, steadier, and less ruled by fear."
        if "bhakti" in philosophical_tags or "devotion" in philosophical_tags:
            return "It turns the heart away from restless self-importance and toward trust, humility, and steadier intention."
        if "jnana" in philosophical_tags or "atman" in philosophical_tags:
            return "It reminds you that clear seeing matters because the confused mind exaggerates danger while the steadier mind notices what is actually true."
        if "yoga" in philosophical_tags:
            return "It treats steadiness as a practice, not a mood, so clarity grows through repeated alignment of thought, action, and restraint."
        return f"The practical value here is that {emotion} loses some of its force when you return to {focus} instead of feeding mental turbulence."

    def _build_example_sentence(self, emotion: str, focus: str) -> str:
        """Return a sentence that grounds the principle in ordinary life."""

        return (
            f"In daily life this often means noticing the first moment when {emotion} pushes you to rush, withdraw, or over-control, and choosing a calmer relationship with {focus} instead."
        )

    def _build_reframe_sentence(self, philosophical_tags: list[str], focus: str) -> str:
        """Return a sentence that reframes the problem through wisdom."""

        if "self-realization" in philosophical_tags or "jnana" in philosophical_tags:
            return "The deeper shift is from proving yourself in the moment to seeing the moment more truthfully."
        return f"The real work is not winning an argument with your mind but returning again and again to {focus} with honesty."

    def _build_action_sentence(
        self,
        wisdom_entry: WisdomEntry,
        emotional_tags: list[str],
        philosophical_tags: list[str],
        use_cases: list[str],
    ) -> str:
        """Return a practical action sentence."""

        emotion_set = set(emotional_tags)
        philosophy_set = set(philosophical_tags)
        if use_cases:
            use_case_fragment = use_cases[0].rstrip(".")
            return (
                f"Today, choose one small action around {use_case_fragment}: pause, write down the next honest step, and complete it without dramatizing the outcome."
            )
        if "fear" in emotion_set:
            return "Today, name the step you are avoiding, take one measured action toward it, and let courage grow from movement rather than from waiting for certainty."
        if "attachment" in emotion_set or "desire" in emotion_set:
            return "Today, do the work in front of you fully, then deliberately loosen your grip by refusing to rehearse every possible result."
        if "anger" in emotion_set:
            return "Today, give yourself one full pause before speaking in a charged moment, and use that pause to choose words that serve clarity rather than injury."
        if "confusion" in emotion_set:
            return "Today, reduce the decision to one clear next step, write it plainly, and act on that single step before reopening the whole question."
        if "discipline" in emotion_set or "yoga" in philosophy_set:
            return "Today, keep one modest discipline at a fixed time, because reliability in a small practice trains the mind to trust steadiness."
        if "devotion" in emotion_set or "bhakti" in philosophy_set:
            return "Today, set aside a quiet minute for remembrance or gratitude before action, so your effort begins from reverence instead of restlessness."
        if "dharma" in philosophy_set:
            return "Today, identify the duty that is actually yours, complete one part of it cleanly, and leave behind the urge to manage every consequence."
        return "Today, take one concrete step that is honest, proportionate, and steady, then stop feeding the mind with extra worry after the step is done."

    def _build_closing_sentence(self, emotion: str, focus: str, example_index: int) -> str:
        """Return a closing sentence that softens the tone without preaching."""

        if example_index == 0:
            return f"If you repeat that kind of small steadiness, {emotion} will not disappear instantly, but it will stop dictating the whole field of {focus}."
        if example_index == 1:
            return f"Clarity usually returns in this way: not through mental force, but through a quieter relationship with {emotion} and a more faithful relationship with {focus}."
        return f"That is enough for today, because lasting calm is usually built by returning to {focus} one sincere action at a time."

    def _build_source_references(self, wisdom_entry: WisdomEntry) -> list[str]:
        """Build a simple source reference list for a training example."""

        references: list[str] = []
        if wisdom_entry.book_title:
            references.append(wisdom_entry.book_title)
        if wisdom_entry.chapter:
            references.append(wisdom_entry.chapter)
        if wisdom_entry.verse_number:
            references.append(wisdom_entry.verse_number)
        return references

    def _emotion_word(self, emotion: str) -> str:
        """Return a natural phrase for the leading emotional tag."""

        mapping = {
            "anxiety": "anxious pressure",
            "grief": "grief",
            "fear": "fear",
            "duty": "responsibility",
            "attachment": "attachment",
            "anger": "anger",
            "confusion": "confusion",
            "discipline": "inner inconsistency",
            "devotion": "spiritual longing",
            "self-control": "inner unrest",
            "ego": "self-importance",
            "desire": "restless wanting",
            "surrender": "the struggle to let go",
            "purpose": "uncertainty about direction",
        }
        return mapping.get(emotion, "inner strain")

    def _focus_word(self, wisdom_entry: WisdomEntry, philosophical_tags: list[str]) -> str:
        """Return a short focus phrase for openings and explanations."""

        principle_text = (wisdom_entry.extracted_principle or "").lower()
        if "dharma" in philosophical_tags or "duty" in principle_text:
            return "duty"
        if "karma" in philosophical_tags or "renunciation" in philosophical_tags:
            return "right action"
        if "bhakti" in philosophical_tags or "devotion" in philosophical_tags:
            return "trust"
        if "jnana" in philosophical_tags or "self-realization" in philosophical_tags:
            return "clarity"
        if "atman" in philosophical_tags:
            return "inner steadiness"
        if "yoga" in philosophical_tags:
            return "discipline"
        return "clarity"

    def _opening_key(self, opening_sentence: str) -> str:
        """Return the normalized opening phrase used by the dataset audit."""

        return " ".join(opening_sentence.strip().split()[:12]).rstrip(".,;:!?").lower()

    def _ordered_indices(self, length: int, seed: int) -> list[int]:
        """Return a deterministic rotated list of indices."""

        start = seed % length
        return [(start + offset) % length for offset in range(length)]

    def _normalize_response(self, response: str) -> str:
        """Return normalized response text for similarity checks."""

        normalized = response.lower()
        normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _is_too_similar(self, normalized_response: str, existing_responses: list[str]) -> bool:
        """Return True when a candidate response is too similar to an existing one."""

        for existing_response in existing_responses[-SIMILARITY_LOOKBACK:]:
            if abs(len(normalized_response) - len(existing_response)) > 180:
                continue
            if SequenceMatcher(None, normalized_response, existing_response).ratio() >= SIMILARITY_THRESHOLD:
                return True
        return False

    def _enforce_length_bounds(self, response: str, context: dict[str, str]) -> str:
        """Ensure a response stays within the target word-count range."""

        words = response.split()
        if len(words) < MIN_RESPONSE_WORDS:
            extra_sentence = (
                "Stay close to one concrete step, because calm usually grows after honest action rather than before it."
            )
            response = f"{response} {extra_sentence}"
            words = response.split()
        if len(words) < MIN_RESPONSE_WORDS:
            response = f"{response} {context['closing']}"
            words = response.split()
        if len(words) > MAX_RESPONSE_WORDS:
            trimmed_words = words[:MAX_RESPONSE_WORDS]
            response = " ".join(trimmed_words).rstrip(",;:") + "."
        return response

    def _dedupe_adjacent(self, parts: list[str]) -> list[str]:
        """Drop consecutive duplicate sentence fragments."""

        deduped: list[str] = []
        for part in parts:
            cleaned_part = self._clean_text(part)
            if not cleaned_part:
                continue
            if deduped and deduped[-1] == cleaned_part:
                continue
            deduped.append(cleaned_part)
        return deduped

    def _remove_forbidden_phrases(self, text: str) -> str:
        """Strip visibly repetitive phrases that should not appear in responses."""

        cleaned_text = text
        for phrase in (
            "I hear",
            "Begin by slowing the mind",
            "A helpful reflection",
            "Let this teaching",
        ):
            cleaned_text = cleaned_text.replace(phrase, "")
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip(" ,.")
        return cleaned_text or text

    def _clean_text(self, text: str | None) -> str | None:
        """Normalize whitespace and drop obviously corrupted content."""

        if not text:
            return None
        cleaned_text = " ".join(text.split()).strip()
        if not cleaned_text:
            return None
        if CORRUPTION_PATTERN.search(cleaned_text):
            return None
        return cleaned_text

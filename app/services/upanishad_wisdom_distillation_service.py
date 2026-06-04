"""Deterministically distill Upanishad wisdom entries into human-applicable lessons."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable, Sequence

from app.models.wisdom_entry import WisdomEntry


SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")
CORRUPTION_PATTERN = re.compile(r"[{}@ïÌœ]|H¥|�|\.\.\.")
CHARACTER_PATTERN = re.compile(
    r"\b(nachiketas|death|yama|agni|vayu|indra|brahma|ouddalaki|aruna|angiras|saunaka|vajasrava|gautama|yaksha)\b",
    re.IGNORECASE,
)
RITUAL_PATTERN = re.compile(
    r"\b(sacrifice|oblations|altar|bricks|agnihotra|fire that leads to heaven|rites?|vow of holding fire|guest enters the houses|boons?)\b",
    re.IGNORECASE,
)
SCRIPTURE_NARRATION_PATTERN = re.compile(
    r"\b(these gods|thus he said|therefore these|taking hold of the bow|death told him|he then said|i will teach thee|o death|o brahmana|ask for three boons)\b",
    re.IGNORECASE,
)
SPEAKER_ONLY_PATTERN = re.compile(r"^(death said|teacher said|disciple said|student said)\b", re.IGNORECASE)
DIRECT_SPEECH_PATTERN = re.compile(r"[\"“”]|^\(?nachiketas said|^\(?disciple|^\(?teacher", re.IGNORECASE)
ARCHAIC_PATTERN = re.compile(r"\b(thou|thee|thy|whoso|hast|wilt|dost)\b", re.IGNORECASE)
SANSKRIT_PATTERN = re.compile(
    r"\b(brahman|atman|purusha|om|maya|veda|upanishad|yajna|karma|moksha|prana)\b",
    re.IGNORECASE,
)
LITERAL_OUTPUT_PATTERN = re.compile(
    r"^(ask for|from him|he who|when this self|as rivers|the indwelling self|the self that|the first-born|the rik|within that in which|understanding deepens when that which)",
    re.IGNORECASE,
)

VARIATION_BANKS: dict[str, tuple[str, ...]] = {
    "steady_attention": (
        "Steady attention helps the mind return from distraction to what is deeply true.",
        "Clarity grows when the mind learns how to return instead of keep wandering.",
        "A restless mind becomes more trustworthy when attention is trained to come back.",
        "Discipline helps the mind settle when it no longer follows every distraction.",
        "Inner steadiness grows when attention is taught where to return under pressure.",
        "The mind clears when attention stops drifting and comes back to what matters.",
        "Practice becomes powerful when the mind is trained to return instead of scatter.",
        "Mental steadiness deepens when distraction no longer gets the final word.",
        "A scattered mind settles when attention returns to truth instead of chasing noise.",
        "Steadiness becomes possible when attention keeps returning instead of running outward.",
        "The mind grows clearer when it is trained to come back from agitation.",
        "Distraction loses power when attention learns a steadier place to return.",
        "Clarity strengthens when the mind stops drifting and starts returning with purpose.",
        "Attention matures when the mind no longer obeys every restless impulse.",
        "The mind becomes steadier when attention returns to what is true under pressure.",
        "Inner clarity deepens when distraction stops directing the movement of the mind.",
        "Mental discipline grows when attention comes back instead of continuing to wander.",
        "A calmer mind is built by returning attention again and again to truth.",
        "Restlessness weakens when attention is guided back to what matters most.",
        "The mind gains strength when it learns to return from distraction without struggle.",
        "Attention becomes healing when it no longer follows every impulse away from truth.",
        "Steady practice helps the mind return before restlessness takes over completely.",
        "Clarity becomes durable when attention is trained to recover from distraction quickly.",
        "The mind steadies when attention stops negotiating with every passing disturbance.",
        "Restlessness fades when attention returns to what is quietly true.",
        "Discipline brings calm when attention is no longer scattered by every impulse.",
        "The mind becomes more stable when attention returns instead of reacting blindly.",
        "Attention strengthens character when it keeps coming back to what matters.",
        "Steadiness grows when distraction is noticed early and attention gently returns.",
        "The mind finds balance when attention is practiced like a return, not a chase.",
    ),
    "fear_change": (
        "Fear loosens when you stop treating change as the end of who you are.",
        "Courage grows when change is no longer mistaken for the loss of your deepest self.",
        "Anxiety softens when you stop believing every ending destroys what is most real in you.",
        "Peace becomes possible when change no longer defines your entire identity.",
        "Inner steadiness grows when impermanence is not treated like personal collapse.",
        "Fear loses force when you stop reading change as proof that you are lost.",
        "Calm returns when you stop confusing transition with the disappearance of your worth.",
        "Change becomes less frightening when it is not mistaken for the death of meaning.",
        "Courage deepens when you stop letting impermanence decide who you are.",
        "Fear eases when you stop assuming that change erases your deepest reality.",
        "Steadiness becomes possible when endings are not treated like the end of your identity.",
        "Peace grows when you stop handing ultimate power to change.",
    ),
    "identity_confusion": (
        "Clarity grows when you stop confusing passing thoughts with your whole identity.",
        "Self-understanding deepens when every mental reaction is not treated as your deepest self.",
        "Inner confusion eases when you stop reducing yourself to what the mind says today.",
        "A steadier identity appears when passing thoughts no longer define who you are.",
        "Freedom begins when you stop identifying completely with surface mental activity.",
        "The mind becomes less confusing when you remember thoughts are not your whole identity.",
        "Clarity returns when you stop letting passing reactions explain your entire self.",
        "A stronger inner life begins when thoughts are not mistaken for your deepest identity.",
        "Self-knowledge deepens when you stop treating mental noise as the whole truth about you.",
        "Confusion softens when you stop collapsing your identity into every passing thought.",
        "Awareness becomes clearer when you stop measuring yourself by transient mental states.",
        "Inner freedom grows when fleeting thoughts stop pretending to define your whole self.",
    ),
    "humility_learning": (
        "Some truths become clear when humility grows stronger than the need to win arguments.",
        "Understanding deepens when sincerity matters more than proving yourself right.",
        "Real learning begins when listening matters more than protecting your image.",
        "Wisdom becomes available when practice matters more than appearing knowledgeable.",
        "Insight grows when honesty becomes stronger than the urge to look advanced.",
        "Learning matures when the need to be right stops blocking the desire to understand.",
        "Clarity deepens when humility makes room for truths argument alone cannot reach.",
        "Growth begins when understanding becomes more important than self-display.",
        "Wisdom enters more deeply when pride no longer leads the learning process.",
        "Truth becomes accessible when the heart is more teachable than defensive.",
        "Some insights arrive only when humility opens what debate cannot force.",
        "Understanding ripens when the wish to learn outgrows the wish to impress.",
    ),
    "desire_wisdom": (
        "Wisdom strengthens when you choose what is right over what is immediately comforting.",
        "Growth often begins when comfort no longer decides what deserves your loyalty.",
        "Peace becomes possible when desire stops directing your choices.",
        "Maturity deepens when short-term comfort stops ruling long-term decisions.",
        "Inner freedom grows when what is pleasant no longer outweighs what is true.",
        "A better life begins when desire is no longer trusted more than wisdom.",
        "Clarity grows when comfort stops deciding what matters most.",
        "Strong choices emerge when truth matters more than immediate relief.",
        "Freedom deepens when you stop obeying whatever feels easiest in the moment.",
        "Wisdom becomes practical when desire no longer sets the direction of your life.",
        "Peace strengthens when you stop asking comfort to tell you what is good.",
        "Growth becomes real when what is right matters more than what is soothing.",
    ),
    "attachment_temporary": (
        "Freedom grows when you loosen your grip on what was never stable enough to hold you.",
        "Peace returns when temporary things stop carrying the weight of lasting security.",
        "Attachment weakens when you stop asking passing things to make you whole.",
        "Inner steadiness deepens when you stop leaning on what cannot remain unchanged.",
        "Clarity grows when temporary comforts are no longer expected to last forever.",
        "Emotional freedom begins when you release the demand for permanence from passing things.",
        "The heart settles when changeable things are no longer treated like final anchors.",
        "Peace becomes more durable when you stop expecting the temporary to feel eternal.",
        "Attachment loosens when impermanent things stop carrying your deepest hopes.",
        "Freedom begins when you stop asking what passes to give what can endure.",
    ),
    "ego_achievement": (
        "Even sincere effort becomes distorted when ego quietly turns progress into self-importance.",
        "Growth becomes unstable when success is used to protect identity instead of deepen truth.",
        "Pride hides easily when appearing advanced matters more than becoming honest.",
        "Insight becomes shallow when recognition matters more than transformation.",
        "Achievement becomes dangerous when it is used to hide insecurity instead of face it.",
        "Humility is necessary because ego can hide inside even spiritual ambition.",
        "Progress loses depth when the wish to appear wise outruns the wish to grow.",
        "Inner honesty weakens when success becomes a shelter for pride.",
    ),
    "inner_steadiness": (
        "Inner steadiness grows when you stop chasing every disturbance as if it deserves control.",
        "Calm becomes more trustworthy when each pressure no longer decides your state of mind.",
        "The heart settles when you stop handing authority to every passing emotion.",
        "Emotional balance deepens when inner noise is met without being obeyed.",
        "Steadiness becomes possible when disturbances are noticed without becoming commands.",
        "Trust becomes steadier when passing waves stop deciding how you live.",
        "Peace deepens when every feeling is not treated like an instruction.",
        "Inner calm matures when disturbance is witnessed without immediate surrender.",
        "Steadiness grows when emotions are felt honestly without being allowed to rule.",
        "The mind becomes gentler when pressure is not given full authority.",
    ),
    "lived_wisdom": (
        "Truth becomes useful when it is practiced under pressure instead of admired from a distance.",
        "Wisdom becomes real when it shapes daily choices instead of remaining a beautiful idea.",
        "Understanding changes us when it is lived honestly rather than repeated elegantly.",
        "Insight becomes strength when it enters conduct instead of staying in explanation.",
        "Clarity matters most when it changes how you respond to difficulty.",
        "Knowledge becomes transformative when it is embodied instead of merely described.",
        "Truth gains power when it becomes a way of living rather than a slogan.",
        "Wisdom ripens when it moves from explanation into action.",
    ),
    "direction_purpose": (
        "Direction returns when you listen beneath surface reactions for what is quietly true.",
        "Purpose becomes clearer when mental noise stops deciding what matters most.",
        "A steadier path appears when impulse no longer drowns deeper honesty.",
        "Clarity about your direction grows when passing agitation stops leading the mind.",
        "What matters becomes clearer when confusion is not allowed to define you.",
        "Purpose strengthens when you listen for what remains true under pressure.",
        "Direction deepens when the mind grows quiet enough to hear what is essential.",
        "A truer path appears when deeper honesty speaks louder than inner noise.",
    ),
}


class UpanishadWisdomDistillationService:
    """Convert Upanishad wisdom entries into concise universal lessons."""

    def distill_entries(self, wisdom_entries: Sequence[WisdomEntry]) -> dict[int, tuple[str | None, float]]:
        """Return corpus-aware distilled wisdom for a batch of Upanishad wisdom entries."""

        candidate_map: dict[int, list[tuple[str, float]]] = {}
        selected: dict[int, tuple[str | None, float]] = {}
        counts: Counter[str] = Counter()

        for wisdom_entry in wisdom_entries:
            candidates = self._build_candidates(wisdom_entry)
            candidate_map[wisdom_entry.id] = candidates
            chosen = None
            for candidate, confidence in candidates:
                if counts[candidate] < 2:
                    chosen = (candidate, confidence)
                    counts[candidate] += 1
                    break
            selected[wisdom_entry.id] = chosen or (None, 60.0)

        for repeated_text, repeat_count in list(counts.items()):
            if repeat_count <= 2:
                continue
            affected_entries = [
                entry for entry in wisdom_entries
                if selected.get(entry.id, (None, 60.0))[0] == repeated_text
            ]
            for entry in affected_entries[2:]:
                replacement = self._find_replacement(
                    entry_id=entry.id,
                    current_text=repeated_text,
                    candidates=candidate_map.get(entry.id, []),
                    counts=counts,
                )
                if replacement is None:
                    counts[repeated_text] -= 1
                    selected[entry.id] = (None, 60.0)
                else:
                    new_text, new_confidence = replacement
                    counts[repeated_text] -= 1
                    counts[new_text] += 1
                    selected[entry.id] = (new_text, new_confidence)

        return selected

    def distill_entry(self, wisdom_entry: WisdomEntry) -> tuple[str | None, float]:
        """Return distilled wisdom and updated confidence for one Upanishad wisdom entry."""

        return self.distill_entries([wisdom_entry]).get(
            wisdom_entry.id,
            (None, 60.0),
        )

    def _build_candidates(self, wisdom_entry: WisdomEntry) -> list[tuple[str, float]]:
        """Build ordered candidate distilled wisdom strings for one entry."""

        if wisdom_entry.source_document_id != 3:
            existing = self._clean_text(wisdom_entry.distilled_wisdom)
            return [(existing, wisdom_entry.confidence_score or 70.0)] if existing else []

        translation_text = self._clean_text(wisdom_entry.translation) or ""
        principle_text = self._clean_text(wisdom_entry.extracted_principle) or ""

        if self._contains_rejection_pattern(translation_text) and self._contains_rejection_pattern(principle_text):
            return []

        emotional_tags = set(self._normalized_tags(wisdom_entry.emotional_tags))
        philosophical_tags = set(self._normalized_tags(wisdom_entry.philosophical_tags))
        source_pool = " ".join(part for part in [translation_text, principle_text] if part)
        source_lower = source_pool.lower()

        candidates: list[tuple[str, float]] = []
        for category, confidence in self._category_sequence(emotional_tags, philosophical_tags, source_lower):
            for candidate in self._variation_candidates(
                category=category,
                wisdom_entry=wisdom_entry,
                emotional_tags=emotional_tags,
                philosophical_tags=philosophical_tags,
            ):
                if self._is_valid_distillation(candidate) and not any(existing[0] == candidate for existing in candidates):
                    candidates.append((candidate, confidence))

        keyword_candidate = self._keyword_guided_distillation(source_lower)
        if keyword_candidate and self._is_valid_distillation(keyword_candidate):
            candidates.append((keyword_candidate, 82.0))

        for candidate_text in (translation_text, principle_text):
            distilled = self._distill_from_candidate(candidate_text)
            if distilled and not any(existing[0] == distilled for existing in candidates):
                candidates.append((distilled, 76.0))

        return candidates

    def _category_sequence(
        self,
        emotional_tags: set[str],
        philosophical_tags: set[str],
        source_lower: str,
    ) -> list[tuple[str, float]]:
        """Return ordered insight categories for an entry."""

        categories: list[tuple[str, float]] = []

        def add(category: str, confidence: float) -> None:
            if category not in {name for name, _ in categories}:
                categories.append((category, confidence))

        if {"fear"} & emotional_tags and {"death", "immortality"} & philosophical_tags:
            add("fear_change", 95.0)
        if {"confusion", "ego"} & emotional_tags and {"self_knowledge", "consciousness", "atman", "non_duality"} & philosophical_tags:
            add("identity_confusion", 95.0)
        if {"desire", "attachment"} & emotional_tags:
            add("desire_wisdom", 90.0)
        if "teacher_student" in philosophical_tags or "argument" in source_lower:
            add("humility_learning", 100.0)
        if {"restlessness", "discipline", "self-control"} & emotional_tags or "meditation" in philosophical_tags:
            add("steady_attention", 95.0)
        if {"inner_steadiness", "trust"} & emotional_tags:
            add("inner_steadiness", 100.0)
        if {"attachment", "desire"} & emotional_tags and {"reality", "liberation", "renunciation"} & philosophical_tags:
            add("attachment_temporary", 92.0)
        if {"purpose", "confusion"} & emotional_tags and {"self_knowledge", "consciousness", "reality"} & philosophical_tags:
            add("direction_purpose", 88.0)
        if "ego" in emotional_tags or "pride" in source_lower or "glory" in source_lower:
            add("ego_achievement", 90.0)
        if "truth" in source_lower or "lived" in source_lower or "practice" in source_lower:
            add("lived_wisdom", 86.0)

        if not categories:
            if {"meditation", "consciousness", "self_knowledge"} & philosophical_tags:
                add("steady_attention", 84.0)
            elif {"death", "immortality"} & philosophical_tags:
                add("fear_change", 84.0)
            elif {"self_knowledge", "atman", "non_duality"} & philosophical_tags:
                add("identity_confusion", 84.0)
            elif {"teacher_student"} & philosophical_tags:
                add("humility_learning", 84.0)

        return categories

    def _variation_candidates(
        self,
        category: str,
        wisdom_entry: WisdomEntry,
        emotional_tags: set[str],
        philosophical_tags: set[str],
    ) -> list[str]:
        """Generate deterministic variants for a category."""

        if category not in VARIATION_BANKS:
            return []

        variants = VARIATION_BANKS[category]
        seed = self._entry_seed(
            wisdom_entry.id,
            wisdom_entry.book_title,
            wisdom_entry.chapter,
            wisdom_entry.section,
            sorted(emotional_tags),
            sorted(philosophical_tags),
            category,
        )
        variant_order = self._rotated(variants, seed)

        candidates: list[str] = []
        for variant in variant_order:
            candidate = self._finalize_candidate(variant)
            if candidate and self._is_valid_distillation(candidate) and candidate not in candidates:
                candidates.append(candidate)
        return candidates

    def _find_replacement(
        self,
        entry_id: int,
        current_text: str,
        candidates: Sequence[tuple[str, float]],
        counts: Counter[str],
    ) -> tuple[str, float] | None:
        """Find a non-overused replacement candidate for a repeated distilled wisdom value."""

        for candidate, confidence in candidates:
            if candidate == current_text:
                continue
            if counts[candidate] >= 2:
                continue
            return candidate, confidence
        return None

    def _keyword_guided_distillation(self, source_lower: str) -> str | None:
        """Fallback tag-free distillation from recognizable Upanishad teaching motifs."""

        keyword_rules: tuple[tuple[re.Pattern[str], str], ...] = (
            (
                re.compile(r"\b(argument|arguable|cannot be had through argumentation)\b", re.IGNORECASE),
                "Some truths become clear when humility matters more than winning the argument.",
            ),
            (
                re.compile(r"\b(preferable|pleasant|desirable|covetable)\b", re.IGNORECASE),
                "Wise choices often require preferring long-term truth over immediate comfort.",
            ),
            (
                re.compile(r"\b(desire|wealth|ephemeral|craving)\b", re.IGNORECASE),
                "Desire becomes less controlling when comfort no longer decides what matters.",
            ),
            (
                re.compile(r"\b(ear of the ear|mind of the mind|eye of the eye)\b", re.IGNORECASE),
                "Awareness becomes clearer when you stop reducing yourself to sensation and thought alone.",
            ),
            (
                re.compile(r"\b(immortal|immortality|death|mortal)\b", re.IGNORECASE),
                "Fear loosens when change is no longer mistaken for the loss of your deepest identity.",
            ),
            (
                re.compile(r"\b(desireless|without attachment|freed from attachment|renouncing)\b", re.IGNORECASE),
                "Freedom grows when your peace is no longer tied to what cannot remain.",
            ),
            (
                re.compile(r"\b(knot of the heart|doubts become solved)\b", re.IGNORECASE),
                "Honest clarity untangles the heart when confusion is no longer protected.",
            ),
            (
                re.compile(r"\b(victory|pride|glory)\b", re.IGNORECASE),
                "Achievement becomes dangerous when pride hides inside the wish to appear advanced.",
            ),
        )

        for pattern, distilled in keyword_rules:
            if pattern.search(source_lower):
                return self._finalize_candidate(distilled)
        return None

    def _distill_from_candidate(self, text: str) -> str | None:
        """Build a distilled sentence from a candidate block."""

        if not text:
            return None

        for sentence in SENTENCE_PATTERN.split(text):
            candidate = self._clean_text(sentence)
            if not candidate or self._contains_rejection_pattern(candidate):
                continue
            universal = self._universalize(candidate)
            if universal and self._is_valid_distillation(universal):
                return universal
        return None

    def _universalize(self, sentence: str) -> str | None:
        """Convert a literal sentence into a more universal human insight."""

        rewritten = sentence
        replacements = (
            (r"\bthe self\b", "identity"),
            (r"\bbrahman\b", "truth"),
            (r"\bimmortality\b", "what remains deepest in you"),
            (r"\bimperishable\b", "what remains under pressure"),
            (r"\bdesireless\b", "less ruled by craving"),
            (r"\bknowledge\b", "understanding"),
        )
        for pattern, replacement in replacements:
            rewritten = re.sub(pattern, replacement, rewritten, flags=re.IGNORECASE)

        rewritten = re.sub(r"\([^)]*\)", "", rewritten)
        rewritten = CHARACTER_PATTERN.sub("", rewritten)
        rewritten = SANSKRIT_PATTERN.sub("", rewritten)
        rewritten = re.sub(r"\s+", " ", rewritten).strip(" .,:;-")
        if not rewritten:
            return None

        lowered = rewritten.lower()
        if LITERAL_OUTPUT_PATTERN.match(lowered):
            return None
        if lowered.startswith(("he ", "she ", "they ", "it ", "this ", "that ")):
            return None
        if "mind" in lowered and "control" in lowered:
            return self._finalize_candidate("Clarity becomes possible when the mind is guided instead of obeyed.")
        if "truth" in lowered and "live" in lowered:
            return self._finalize_candidate("Truth matters most when it shapes how you live under pressure.")
        if "heart" in lowered and "desire" in lowered:
            return self._finalize_candidate("The heart settles when desire no longer decides what matters most.")
        return None

    def _contains_rejection_pattern(self, text: str) -> bool:
        """Return True when a text block should not be distilled directly."""

        if not text:
            return True
        if CORRUPTION_PATTERN.search(text):
            return True
        if SCRIPTURE_NARRATION_PATTERN.search(text):
            return True
        if DIRECT_SPEECH_PATTERN.search(text):
            return True
        if RITUAL_PATTERN.search(text):
            return True
        if SPEAKER_ONLY_PATTERN.match(text):
            return True
        return False

    def _is_valid_distillation(self, text: str) -> bool:
        """Return True when distilled wisdom satisfies Upanishad output rules."""

        lowered = text.lower()
        word_count = len(text.split())
        if word_count < 8 or word_count > 30:
            return False
        if CORRUPTION_PATTERN.search(text):
            return False
        if CHARACTER_PATTERN.search(text):
            return False
        if SCRIPTURE_NARRATION_PATTERN.search(text):
            return False
        if DIRECT_SPEECH_PATTERN.search(text):
            return False
        if RITUAL_PATTERN.search(text):
            return False
        if ARCHAIC_PATTERN.search(text):
            return False
        if LITERAL_OUTPUT_PATTERN.match(lowered):
            return False
        if any(phrase in lowered for phrase in ("these gods", "thus he said", "therefore these", "taking hold of the bow")):
            return False
        return True

    def _finalize_candidate(self, text: str | None) -> str | None:
        """Normalize candidate sentence length and punctuation."""

        if not text:
            return None
        normalized = re.sub(r"\s+", " ", text).strip(" .,:;-")
        if not normalized:
            return None
        words = normalized.split()
        if len(words) > 30:
            normalized = " ".join(words[:30]).rstrip(".,;:") + "."
        elif not normalized.endswith("."):
            normalized = f"{normalized}."
        normalized = normalized[0].upper() + normalized[1:] if len(normalized) > 1 else normalized.upper()
        return normalized

    def _normalized_tags(self, tags: Iterable[str] | None) -> list[str]:
        """Return lowercased tag names."""

        if not tags:
            return []
        return [str(tag).strip().lower() for tag in tags if str(tag).strip()]

    def _clean_text(self, text: str | None) -> str | None:
        """Normalize whitespace while preserving readable content."""

        if not text:
            return None
        cleaned_text = " ".join(text.split()).strip()
        return cleaned_text or None

    def _rotated(self, values: Sequence[str], seed: int) -> list[str]:
        """Return a deterministic rotation of a sequence."""

        if not values:
            return []
        offset = seed % len(values)
        return list(values[offset:]) + list(values[:offset])

    def _entry_seed(self, *parts: object) -> int:
        """Return a stable integer seed from entry metadata."""

        text = "|".join("" if part is None else str(part) for part in parts)
        return sum((index + 1) * ord(char) for index, char in enumerate(text))

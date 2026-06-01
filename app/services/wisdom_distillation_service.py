"""Deterministically distill verse material into universal human lessons."""

from __future__ import annotations

import re

from app.models.wisdom_entry import WisdomEntry


SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")
CORRUPTION_PATTERN = re.compile(r"[{}@ïÌœ]|H¥|jkhh|vijkhh|iijkhh|viiijkhh|�")
SPEAKER_PATTERN = re.compile(
    r"\b(arjuna|krishna|sanjaya|dhritarashtra|gandeeva|partha|madhusudana|kaunteya)\b",
    re.IGNORECASE,
)
NARRATION_PATTERN = re.compile(
    r"^(o king|o partha|arjuna said|sanjaya said|krishna said|the lord said)\b",
    re.IGNORECASE,
)
SANSKRIT_TERM_PATTERN = re.compile(
    r"\b(karma|dharma|atman|bhakti|jnana|moksha|maya|guna|yoga|samsara|rajas|tamas|sattva)\b",
    re.IGNORECASE,
)
FIRST_PERSON_PATTERN = re.compile(r"\b(i|my|me|we|our|us)\b", re.IGNORECASE)
QUESTION_PATTERN = re.compile(r"[?]|^(what|how|why|when)\b", re.IGNORECASE)
KEYWORD_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"\b(bow|limbs|skin is burning|unable to stand|delusion|doubt)\b", re.IGNORECASE),
        "Strong emotions can cloud judgment and make even capable people doubt themselves.",
    ),
    (
        re.compile(r"\b(expectation|expectations|outcomes?|fruit of action|results?)\b", re.IGNORECASE),
        "Focus on the actions you can control rather than obsessing over outcomes.",
    ),
    (
        re.compile(r"\b(prescribed dut|natural attributes|responsibilit|calling)\b", re.IGNORECASE),
        "Clarity grows when you honor the work that is yours to do.",
    ),
    (
        re.compile(r"\b(desire|craving|lust|sense pleasures?)\b", re.IGNORECASE),
        "Desire loses its power when you stop letting it define your choices.",
    ),
    (
        re.compile(r"\b(anger|wrath|resentment|rage)\b", re.IGNORECASE),
        "Anger becomes less destructive when you pause before acting from it.",
    ),
    (
        re.compile(r"\b(wandering mind|restless mind|control the mind|meditation|practice)\b", re.IGNORECASE),
        "Steady practice can train a restless mind into greater clarity.",
    ),
    (
        re.compile(r"\b(control the senses|sense organs|self-control|restraint|mastery)\b", re.IGNORECASE),
        "Self-control grows when you guide your impulses instead of obeying them.",
    ),
    (
        re.compile(r"\b(devotion|worship|faith|surrender|loving service)\b", re.IGNORECASE),
        "Devotion becomes meaningful when sincerity matters more than outward display.",
    ),
    (
        re.compile(r"\b(grief|sorrow|lament|mourning|loss)\b", re.IGNORECASE),
        "Grief softens when wisdom steadies the heart without denying the pain.",
    ),
    (
        re.compile(r"\b(fear|afraid|terror|panic|dread)\b", re.IGNORECASE),
        "Courage begins when you do what is right even while fear is present.",
    ),
    (
        re.compile(r"\b(attachment|attached|clinging|possessive|letting go)\b", re.IGNORECASE),
        "Peace deepens when you loosen your grip on what you cannot control.",
    ),
    (
        re.compile(r"\b(paths taken|return to this world|not return|seekers)\b", re.IGNORECASE),
        "The direction of your life is shaped by what your mind repeatedly turns toward.",
    ),
    (
        re.compile(r"\b(knowledge|wisdom|discernment|understanding)\b", re.IGNORECASE),
        "Clarity grows when you seek understanding instead of reacting impulsively.",
    ),
    (
        re.compile(r"\b(famil(y|ies)|unrighteousness|sinful acts|perils)\b", re.IGNORECASE),
        "Short-term gain is not worth betraying the values that hold life together.",
    ),
    (
        re.compile(r"\b(space|tainted|pervading everywhere)\b", re.IGNORECASE),
        "Your deeper steadiness can remain untouched even when life around you is turbulent.",
    ),
    (
        re.compile(r"\b(success and failure|equanimity|balanced mind)\b", re.IGNORECASE),
        "Peace grows when you meet success and failure with the same steady mind.",
    ),
    (
        re.compile(r"\b(liberation|freedom|release)\b", re.IGNORECASE),
        "Inner freedom grows when you live with discipline, truth, and detachment.",
    ),
)
class WisdomDistillationService:
    """Convert verse-linked insights into short universal lessons."""

    def distill_entry(self, wisdom_entry: WisdomEntry) -> str | None:
        """Return a one-sentence distilled lesson for a wisdom entry."""

        if self._contains_corruption(wisdom_entry.translation) or self._contains_corruption(
            wisdom_entry.commentary
        ):
            return None

        keyword_based = self._distill_from_keywords(wisdom_entry)
        if keyword_based:
            return keyword_based

        tag_based = self._distill_from_tags(wisdom_entry)
        if tag_based:
            return tag_based

        for candidate in self._candidate_sentences(wisdom_entry):
            distilled = self._universalize_sentence(candidate)
            if distilled:
                return distilled

        return None

    def _distill_from_keywords(self, wisdom_entry: WisdomEntry) -> str | None:
        """Use keyword patterns from the verse material to create universal lessons."""

        combined_text = " ".join(
            part
            for part in (
                self._clean_text(wisdom_entry.extracted_principle),
                self._clean_text(wisdom_entry.translation),
                self._clean_text(wisdom_entry.commentary),
            )
            if part
        )
        if not combined_text:
            return None

        for pattern, distilled_text in KEYWORD_RULES:
            if pattern.search(combined_text):
                return distilled_text
        return None

    def _distill_from_tags(self, wisdom_entry: WisdomEntry) -> str | None:
        """Use existing tags to generate strong universal wisdom first."""

        emotional_tags = set(wisdom_entry.emotional_tags or [])
        philosophical_tags = set(wisdom_entry.philosophical_tags or [])

        if {"confusion", "fear"} & emotional_tags:
            return "Strong emotions can cloud judgment and make even capable people doubt themselves."
        if "duty" in emotional_tags and ("karma" in philosophical_tags or "dharma" in philosophical_tags):
            return "Focus on the actions you can control rather than obsessing over outcomes."
        if "attachment" in emotional_tags:
            return "Peace deepens when you loosen your grip on what you cannot control."
        if "anger" in emotional_tags:
            return "Anger becomes less destructive when you pause before acting from it."
        if "discipline" in emotional_tags or "yoga" in philosophical_tags:
            return "Steady discipline strengthens the mind when emotions are unsettled."
        if "self-control" in emotional_tags:
            return "Self-control grows when you guide your impulses instead of obeying them."
        if "desire" in emotional_tags:
            return "Desire loses its power when you stop letting it define your choices."
        if "devotion" in emotional_tags or "bhakti" in philosophical_tags:
            return "Devotion becomes meaningful when sincerity matters more than outward display."
        if "surrender" in emotional_tags:
            return "Surrender brings relief when you offer your effort without demanding certainty."
        if "purpose" in emotional_tags or "dharma" in philosophical_tags:
            return "Purpose becomes clearer when your actions serve something deeper than ego."
        if "jnana" in philosophical_tags or "atman" in philosophical_tags:
            return "Lasting clarity comes from returning to truth instead of feeding confusion."
        if "fear" in emotional_tags:
            return "Courage begins when you do what is right even while fear is present."
        return None

    def _candidate_sentences(self, wisdom_entry: WisdomEntry) -> list[str]:
        """Collect possible source sentences from current wisdom entry fields."""

        candidates: list[str] = []
        for block in (
            wisdom_entry.extracted_principle,
            wisdom_entry.translation,
            wisdom_entry.commentary,
        ):
            cleaned_block = self._clean_text(block)
            if not cleaned_block:
                continue
            for sentence in SENTENCE_PATTERN.split(cleaned_block):
                normalized = self._clean_text(sentence)
                if normalized and normalized not in candidates:
                    candidates.append(normalized)
        return candidates

    def _universalize_sentence(self, sentence: str) -> str | None:
        """Convert a verse-specific sentence into a universal human lesson."""

        lowered_sentence = sentence.lower()
        if len(lowered_sentence.split()) < 6:
            return None
        if QUESTION_PATTERN.search(sentence):
            return None
        if FIRST_PERSON_PATTERN.search(sentence):
            return None
        if NARRATION_PATTERN.match(lowered_sentence):
            return None
        if SPEAKER_PATTERN.search(lowered_sentence):
            if "doubt" in lowered_sentence or "delusion" in lowered_sentence or "fear" in lowered_sentence:
                return "Strong emotions can cloud judgment and make even capable people doubt themselves."
            if "duty" in lowered_sentence or "action" in lowered_sentence or "fruit" in lowered_sentence:
                return "Focus on the actions you can control rather than obsessing over outcomes."
            return None

        stripped_sentence = SPEAKER_PATTERN.sub("", sentence)
        stripped_sentence = SANSKRIT_TERM_PATTERN.sub("", stripped_sentence)
        stripped_sentence = re.sub(r"\([^)]*\)", "", stripped_sentence)
        stripped_sentence = re.sub(r"\b(this verse|the lord|the selfsame|therefore)\b", "", stripped_sentence, flags=re.IGNORECASE)
        stripped_sentence = re.sub(r"\s+", " ", stripped_sentence).strip(" .,:;-")
        if not stripped_sentence:
            return None

        lowered_stripped = stripped_sentence.lower()
        if FIRST_PERSON_PATTERN.search(stripped_sentence):
            return None
        if QUESTION_PATTERN.search(stripped_sentence):
            return None
        if any(phrase in lowered_stripped for phrase in ("my bow", "my limbs", "my skin", "battlefield")):
            return "Strong emotions can cloud judgment and make even capable people doubt themselves."
        if "outcome" in lowered_stripped or "fruit of action" in lowered_stripped:
            return "Focus on the actions you can control rather than obsessing over outcomes."
        if "control the senses" in lowered_stripped or "restraint" in lowered_stripped:
            return "Self-control grows when you guide your impulses instead of obeying them."
        if "anger" in lowered_stripped:
            return "Anger becomes less destructive when you pause before acting from it."
        if "fear" in lowered_stripped:
            return "Courage begins when you do what is right even while fear is present."
        if any(
            phrase in lowered_stripped
            for phrase in ("teach you", "i will now", "great warriors", "possessing heavy weapons", "surviving women")
        ):
            return None

        universal = stripped_sentence[0].upper() + stripped_sentence[1:] if len(stripped_sentence) > 1 else stripped_sentence.upper()
        if not universal.endswith("."):
            universal = f"{universal}."
        if len(universal.split()) > 30:
            truncated = " ".join(universal.split()[:30]).rstrip(".,;:")
            universal = f"{truncated}."
        if self._is_invalid_distillation(universal):
            return None
        return universal

    def _is_invalid_distillation(self, text: str) -> bool:
        """Return True when distilled wisdom fails the required output rules."""

        lowered_text = text.lower()
        if len(lowered_text.split()) > 30:
            return True
        if CORRUPTION_PATTERN.search(text):
            return True
        if NARRATION_PATTERN.match(lowered_text):
            return True
        if QUESTION_PATTERN.search(text):
            return True
        if FIRST_PERSON_PATTERN.search(text):
            return True
        if SPEAKER_PATTERN.search(lowered_text):
            return True
        if SANSKRIT_TERM_PATTERN.search(lowered_text):
            return True
        return False

    def _clean_text(self, text: str | None) -> str | None:
        """Normalize whitespace while preserving readable text."""

        if not text:
            return None
        cleaned_text = " ".join(text.split()).strip()
        return cleaned_text or None

    def _contains_corruption(self, text: str | None) -> bool:
        """Return True when text contains obvious encoding corruption."""

        return bool(text and CORRUPTION_PATTERN.search(text))

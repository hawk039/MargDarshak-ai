# Upanishads Gold-Sample Annotation Specification

This document defines how to create a small manual gold-standard set for the Upanishads pilot parser.

It is based on:

* [upanishads_ingestion_plan.md](/Users/mayankdhyani/PycharmProjects/marg-darshak-ai-service/upanishads_ingestion_plan.md)
* [upanishads_implementation_checklist.md](/Users/mayankdhyani/PycharmProjects/marg-darshak-ai-service/upanishads_implementation_checklist.md)
* [upanishads_pilot_parser_spec.md](/Users/mayankdhyani/PycharmProjects/marg-darshak-ai-service/upanishads_pilot_parser_spec.md)

Pilot scope:

* Kena Upanishad
* Katha Upanishad
* Mundaka Upanishad

This is a specification only. It does **not** add parser or application code.

---

## 1. Purpose

Gold samples are needed before parser implementation because they provide a small set of **known-good canonical passages** and **known-bad rejected fragments** against which the first parser run can be measured.

Without gold samples, parser evaluation becomes subjective and inconsistent.

Gold samples help answer:

* Did the parser detect the right Upanishad boundaries?
* Did it split passages at the right place?
* Did it preserve source metadata correctly?
* Did it accidentally ingest footnotes, headers, or noise?
* Did the extracted passage support useful wisdom distillation?

The gold set is not meant to represent the full corpus. It is meant to provide a reliable early benchmark for:

* boundary accuracy
* metadata accuracy
* contamination detection
* downstream wisdom usefulness

---

## 2. Gold Sample Size

Recommended manual gold set:

* `5` passages from **Kena**
* `8` passages from **Katha**
* `7` passages from **Mundaka**

Total:

* `20` passages

### Why this size is appropriate

* small enough for careful manual review
* large enough to cover multiple structural patterns
* large enough to expose bad splitting and contamination issues early
* balanced toward Katha because dialogue structure is the hardest of the three pilot texts

---

## 3. Annotation Schema

Each gold sample should contain the following fields:

* `gold_id`
* `upanishad_name`
* `chapter`
* `section`
* `passage_number`
* `speaker`
* `english_translation`
* `commentary_or_note`
* `page_reference`
* `expected_distilled_wisdom`
* `expected_emotional_tags`
* `expected_philosophical_tags`
* `expected_user_problem_types`
* `reject_reason`

### Field definitions

#### `gold_id`

Stable identifier for the sample.

Recommended format:

* `kena_001`
* `katha_003`
* `mundaka_007`
* `reject_001`

#### `upanishad_name`

One of:

* `Kena`
* `Katha`
* `Mundaka`

For rejected non-canonical text, keep the best known source text family if available.

#### `chapter`

Top-level chapter or division reference from the source.

Use the form that best preserves source structure, for example:

* `1`
* `I`
* `Mundaka 2`

#### `section`

Local division label from the source.

Examples:

* `Section 1`
* `Khanda 2`
* `Part I, Section 3`

#### `passage_number`

Canonical local locator string.

Examples:

* `1`
* `1.3`
* `2.1.4`
* `I.2`

#### `speaker`

Use when explicit or strongly inferable.

Possible values:

* `teacher`
* `student`
* `Death`
* `Nachiketas`
* `narrator`
* `null`

#### `english_translation`

The clean, manually approved passage text.

This is the most important field for parser evaluation.

#### `commentary_or_note`

Usually `null` for canonical translated passages.

Use only if a short explanatory note is intentionally retained as part of the canonical teaching unit.

#### `page_reference`

The source page reference from the raw document.

#### `expected_distilled_wisdom`

One-sentence universal lesson derived from the passage.

#### `expected_emotional_tags`

Expected human-emotion-oriented tags.

Examples:

* `confusion`
* `fear`
* `grief`
* `attachment`
* `discipline`
* `self-control`
* `purpose`
* `uncertainty`

#### `expected_philosophical_tags`

Expected philosophical concepts.

Examples:

* `atman`
* `jnana`
* `renunciation`
* `maya`
* `moksha`
* `self-realization`
* `detachment`
* `awareness`

#### `expected_user_problem_types`

Expected user-facing application categories.

Examples:

* `career confusion`
* `fear of uncertainty`
* `attachment to outcomes`
* `identity confusion`
* `grief and impermanence`
* `difficulty letting go`

#### `reject_reason`

Use only when the sample is intentionally negative.

Examples:

* `title_only`
* `footnote`
* `speaker_only`
* `ritual_metadata`
* `incomplete_fragment`

For accepted gold passages, `reject_reason` should be `null`.

---

## 4. Annotation Rules

### Core rules

* preserve source reference
* passage must contain a complete teaching idea
* avoid footnotes
* avoid editor notes
* avoid incomplete fragments
* do not over-abstract expected wisdom
* `expected_distilled_wisdom` should be one sentence under 30 words

### Additional annotation guidance

* Keep the annotated `english_translation` as close as possible to the source wording after cleanup.
* Do not merge two unrelated teachings just to create a longer passage.
* Do not split one coherent idea into multiple micro-fragments unless the source itself clearly does so.
* Use `commentary_or_note = null` unless the kept note is truly part of the teaching unit.
* `expected_distilled_wisdom` should be practical and universal, but still faithful to the source.
* Emotional tags should reflect likely end-user relevance, not just literal vocabulary.
* Philosophical tags should reflect the main teaching, not every concept that appears.

---

## 5. Positive Examples

These are illustrative annotation records. The text is placeholder-style where exact source text is not yet locked.

### 5.1 Kena positive example

```json
{
  "gold_id": "kena_001",
  "upanishad_name": "Kena",
  "chapter": "1",
  "section": "Section 1",
  "passage_number": "1.1",
  "speaker": "student",
  "english_translation": "By whom directed does the mind go toward its object, and by whose command does life proceed?",
  "commentary_or_note": null,
  "page_reference": "p. 12",
  "expected_distilled_wisdom": "Real understanding begins when we question the hidden force behind our thoughts and actions.",
  "expected_emotional_tags": ["confusion", "purpose"],
  "expected_philosophical_tags": ["jnana", "atman", "awareness"],
  "expected_user_problem_types": ["identity confusion", "search for purpose"],
  "reject_reason": null
}
```

### 5.2 Katha positive example

```json
{
  "gold_id": "katha_001",
  "upanishad_name": "Katha",
  "chapter": "1",
  "section": "Part I, Section 2",
  "passage_number": "1.2.2",
  "speaker": "Death",
  "english_translation": "The good and the merely pleasant approach a person; the wise choose the good over the pleasant.",
  "commentary_or_note": null,
  "page_reference": "p. 48",
  "expected_distilled_wisdom": "Growth often requires choosing what is right over what is immediately comforting.",
  "expected_emotional_tags": ["discipline", "attachment"],
  "expected_philosophical_tags": ["jnana", "renunciation", "self-control"],
  "expected_user_problem_types": ["temptation and self-control", "difficulty making wise choices"],
  "reject_reason": null
}
```

### 5.3 Mundaka positive example

```json
{
  "gold_id": "mundaka_001",
  "upanishad_name": "Mundaka",
  "chapter": "Mundaka 1",
  "section": "Khanda 2",
  "passage_number": "1.2.12",
  "speaker": "teacher",
  "english_translation": "The truth is not reached by the restless mind, but by one who seeks with steadiness and discernment.",
  "commentary_or_note": null,
  "page_reference": "p. 96",
  "expected_distilled_wisdom": "Inner clarity grows when steady attention replaces restless searching.",
  "expected_emotional_tags": ["confusion", "discipline", "uncertainty"],
  "expected_philosophical_tags": ["jnana", "awareness", "self-realization"],
  "expected_user_problem_types": ["mental restlessness", "search for clarity"],
  "reject_reason": null
}
```

---

## 6. Negative Examples

These should be annotated as rejected samples.

### 6.1 Title-only text

```json
{
  "gold_id": "reject_001",
  "upanishad_name": "Kena",
  "chapter": null,
  "section": null,
  "passage_number": null,
  "speaker": null,
  "english_translation": "Kena Upanishad",
  "commentary_or_note": null,
  "page_reference": "p. 11",
  "expected_distilled_wisdom": null,
  "expected_emotional_tags": [],
  "expected_philosophical_tags": [],
  "expected_user_problem_types": [],
  "reject_reason": "title_only"
}
```

### 6.2 Footnote

```json
{
  "gold_id": "reject_002",
  "upanishad_name": "Katha",
  "chapter": "1",
  "section": "Part I",
  "passage_number": null,
  "speaker": null,
  "english_translation": "Translator's note: compare SBE Vol. XV for alternate rendering.",
  "commentary_or_note": null,
  "page_reference": "p. 44",
  "expected_distilled_wisdom": null,
  "expected_emotional_tags": [],
  "expected_philosophical_tags": [],
  "expected_user_problem_types": [],
  "reject_reason": "footnote"
}
```

### 6.3 Speaker-only line

```json
{
  "gold_id": "reject_003",
  "upanishad_name": "Katha",
  "chapter": "1",
  "section": "Part I, Section 2",
  "passage_number": null,
  "speaker": "Death",
  "english_translation": "Death said:",
  "commentary_or_note": null,
  "page_reference": "p. 46",
  "expected_distilled_wisdom": null,
  "expected_emotional_tags": [],
  "expected_philosophical_tags": [],
  "expected_user_problem_types": [],
  "reject_reason": "speaker_only"
}
```

### 6.4 Ritual metadata

```json
{
  "gold_id": "reject_004",
  "upanishad_name": "Mundaka",
  "chapter": "Mundaka 1",
  "section": "Khanda 1",
  "passage_number": null,
  "speaker": null,
  "english_translation": "This section enumerates ritual fires and sacrificial correspondences without a complete teaching unit.",
  "commentary_or_note": null,
  "page_reference": "p. 88",
  "expected_distilled_wisdom": null,
  "expected_emotional_tags": [],
  "expected_philosophical_tags": [],
  "expected_user_problem_types": [],
  "reject_reason": "ritual_metadata"
}
```

### 6.5 Incomplete fragment

```json
{
  "gold_id": "reject_005",
  "upanishad_name": "Kena",
  "chapter": "2",
  "section": "Section 1",
  "passage_number": null,
  "speaker": null,
  "english_translation": "He who knows it not as that which the mind can...",
  "commentary_or_note": null,
  "page_reference": "p. 15",
  "expected_distilled_wisdom": null,
  "expected_emotional_tags": [],
  "expected_philosophical_tags": [],
  "expected_user_problem_types": [],
  "reject_reason": "incomplete_fragment"
}
```

---

## 7. Evaluation Use

The parser output should be compared against the gold samples on five dimensions.

### A. Passage boundary accuracy

Check whether:

* the parser captured the intended teaching unit
* the parser did not over-merge nearby passages
* the parser did not split a coherent idea into fragments

### B. Metadata accuracy

Check whether:

* `upanishad_name` is correct
* `chapter` is correct
* `section` is correct
* `passage_number` is correct
* `speaker` is correct when applicable
* `page_reference` is preserved

### C. Contamination detection

Check whether the parser correctly excludes:

* title-only text
* footnotes
* editor notes
* speaker-only lines
* ritual metadata with no usable teaching
* incomplete fragments

### D. Wisdom distillation usefulness

Check whether the extracted canonical passage is strong enough to support:

* one-sentence distilled wisdom
* universal phrasing
* calm philosophical training examples later

### E. Tag quality

Check whether the likely emotional and philosophical tags remain plausible for the passage.

This is not full scoring yet, but it helps judge whether the parser preserved the semantic center of the text.

---

## 8. Acceptance Criteria

The parser pilot passes if:

* `80%+` of gold samples are matched
* no rejected gold sample appears as a valid passage
* extracted passages preserve correct source reference
* distilled wisdom is usable for training example generation

### More explicit interpretation

The parser should be considered ready for expansion beyond the pilot if:

* at least `16` of the `20` gold samples are correctly recovered
* all `reject_*` examples remain excluded or invalidated
* no major boundary mistakes appear in the accepted pilot set
* expected distilled wisdom remains reasonably faithful and useful

---

## Final Recommendation

Before parser implementation begins, create the 20-sample gold set manually from the Hume source and keep it as the first quality benchmark.

The parser should not be judged only by how many passages it extracts. It should be judged by whether it recovers the **right** passages cleanly enough for the rest of the Marg Darshak pipeline to produce real wisdom, not noise.

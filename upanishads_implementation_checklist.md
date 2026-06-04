# Upanishads Dataset v1 Implementation Checklist

This checklist turns [upanishads_ingestion_plan.md](/Users/mayankdhyani/PycharmProjects/marg-darshak-ai-service/upanishads_ingestion_plan.md) into a concrete engineering sequence for Dataset v1.

This document does **not** add code. It is a build checklist for the next implementation phase.

---

## 1. Source Preparation

### Primary source to use first

- Use **Robert Ernest Hume, _The Thirteen Principal Upanishads_ (1921)** as the first canonical source.
- Use the public-domain PDF as the working ingestion source.
- Keep **Max Müller’s SBE Upanishads** as a structure-validation reference, not the first ingestion file.

### First source file to ingest

- Download and store one working source PDF for Hume’s edition.
- Prefer one stable local file over multiple mirrors.
- Record the original public source URL in metadata for traceability.

### Storage location

- Store the PDF under `storage/source_documents/`
- Use the existing source-document ingestion pattern already used for the Bhagavad Gita.
- Keep exported datasets separate under `datasets/` and `training/data/`

### Metadata fields needed

For `SourceDocument`, confirm the dataset can reliably capture:

- `title`
- `author` or translator if available in current schema or document metadata
- `source_url`
- `document_type`
- `tradition`
- `book_title` or corpus title if supported downstream
- `language`
- `publication_or_translation_note`

If some of these are not formal DB fields today, preserve them in ingestion notes until the implementation step decides where they belong.

### Expected metadata values

- `title`: `The Thirteen Principal Upanishads`
- `document_type`: `scripture_translation` or `philosophical_text`
- `tradition`: `hinduism` or `vedanta`
- `language`: `english`
- `source_family`: `upanishads`
- `translator`: `Robert Ernest Hume`

### Source preparation checklist

- Select one primary Hume PDF
- Save local copy in `storage/source_documents/`
- Record public source URL
- Record translator and edition name
- Record expected Upanishad list in a working note
- Confirm the file opens and extracts text consistently

---

## 2. Parser Design

### Core parsing principle

- Parse the Upanishads at the **passage level**, not strictly at the verse level.
- A passage may be:
  - one mantra
  - one prose segment
  - one short question-answer unit
  - one compact teaching block

### Upanishad-name detection

Build a deterministic name detection layer for:

- Isha
- Kena
- Katha
- Prashna
- Mundaka
- Mandukya
- Taittiriya
- Aitareya
- Chandogya
- Brihadaranyaka
- Shvetashvatara
- Kaushitaki
- Maitri

Detection should support:

- uppercase heading forms
- title-case heading forms
- transliterated variants
- OCR-distorted near-matches where safe

### Section and chapter detection

Detect internal divisions using flexible patterns such as:

- `Chapter`
- `Khanda`
- `Khaṇḍa`
- `Adhyaya`
- `Adhyāya`
- `Valli`
- `Vallī`
- `Prapathaka`
- `Prapāṭhaka`
- `Question`
- `First Question`, `Second Question`, etc.
- roman numeral section headings
- dotted numeric passage locators like `1.2`, `2.1.4`

### Teaching-passage detection

Passage boundaries should be inferred using:

- explicit numbering
- clear section breaks
- short contiguous prose blocks under one heading
- dialogue blocks that remain semantically self-contained
- repeated refrains treated as part of the nearest teaching unit unless obviously standalone

### Ignore and cleanup rules

Remove or ignore:

- page headers
- page footers
- scan watermarks
- mirrored PDF source strings
- page numbers
- footnotes
- inline reference numerals when clearly editorial
- translator prefaces
- introductions
- appendices
- bibliography
- index pages
- editor notes
- bracketed site navigation text from HTML-derived conversions

### Parser design checklist

- Define canonical heading patterns
- Define division-detection regex families
- Define passage boundary heuristics
- Define narrative/dialogue speaker heuristics
- Define exclusion patterns for non-canonical text
- Define OCR corruption patterns
- Define fallback behavior when section numbering is unclear

---

## 3. Data Model Fit

### Is `CanonicalVerse` enough?

Short answer: **probably yes for v1**, if used flexibly.

Why it can work:

- `verse_number` is already a string
- `speaker` already exists
- `commentary` already exists
- `english_translation` already exists
- `page_reference` already exists
- `is_valid` already exists

### Current limitation

The name `CanonicalVerse` is Gita-shaped and slightly misleading for prose-heavy Upanishad passages.

### Recommended v1 approach

- Keep using `CanonicalVerse` for v1 implementation.
- Treat it as a **canonical passage record**, even if the class name remains unchanged.
- Avoid a new model unless real implementation pain appears.

### When a new `CanonicalPassage` model would be justified

Create a new model only if one or more of these become blocking:

- chapter numbering is too inconsistent across books
- one passage needs multiple locator fields
- prose blocks need richer structural metadata
- multiple traditions need non-verse canonical units regularly

### Recommended schema approach for v1

Use current fields with these conventions:

- `source_document_id`
- `chapter_number`
  - numeric ordinal within the current Upanishad
- `verse_number`
  - string locator like `I.3`, `2.1.4`, `Question 4.6`
- `speaker`
  - teacher, student, named sage, narrator, or null
- `sanskrit_text`
  - optional, only if reliably extractable
- `transliteration`
  - optional, only if reliably extractable
- `english_translation`
  - required primary passage text
- `commentary`
  - optional extracted commentary/editor note block if intentionally preserved
- `page_reference`
  - original page marker
- `is_valid`
  - quality gate flag

### Data model checklist

- Reuse `CanonicalVerse` for v1
- Define passage-level conventions for its fields
- Decide whether `chapter_number` is per-Upanishad ordinal or book-internal chapter index
- Define exact format for `verse_number` locator strings
- Reassess model needs only after pilot parsing

---

## 4. Pipeline Mapping

### Stage 1: PDF → raw text

- ingest Hume PDF
- extract text page by page
- preserve page references
- normalize whitespace and line breaks
- strip obvious headers/footers early where safe

### Stage 2: raw text → canonical passages

- detect Upanishad boundaries
- detect internal divisions
- split into teaching passages
- assign locator strings
- assign page references
- mark invalid passages where extraction is corrupted or non-canonical

### Stage 3: canonical passages → wisdom entries

- run existing canonical-to-wisdom logic
- reject weak passages
- generate translation-based principles
- detect emotional and philosophical tags

### Stage 4: wisdom entries → distilled wisdom

- convert passage-specific or metaphysical language into universal human lessons
- reject over-abstract or over-literal summaries

### Stage 5: distilled wisdom → training examples

- use distilled wisdom first
- map to calm human scenarios
- generate one strong example per approved wisdom entry

### Stage 6: audit → export

- audit training examples for repetition, coherence, practicality, and tone
- approve only clean examples
- export versioned JSONL dataset

### Pipeline checklist

- confirm PDF extraction quality
- confirm passage segmentation quality
- confirm wisdom-entry yield
- confirm distilled-wisdom quality
- confirm training-example variety
- confirm audit pass rate
- export as versioned dataset artifact

---

## 5. Quality Rules

### Passage validity rules

Reject or flag passages if:

- text is too short to carry a teaching
- text is mostly OCR corruption
- text is mostly editorial note
- text is mostly ritual cataloging without human insight
- text is mostly bibliographic noise
- text is incomplete due to page break corruption
- text contains repeated header/footer fragments

### Wisdom distillation rules

Distilled wisdom should:

- be one sentence
- be understandable without prior Upanishad knowledge
- avoid Sanskrit unless essential
- avoid character names unless essential
- avoid metaphysical jargon if a universal phrasing is possible
- express a humanly useful insight
- stay under the current length discipline used for distilled wisdom

Reject or downgrade if:

- too abstract
- too vague
- too literal to the passage
- too dependent on cosmological vocabulary
- sounds like commentary notes rather than human guidance

### Training example audit rules

Retain the strict audit posture already used for Gita-derived examples:

- no repetitive openings above threshold
- no near-duplicate responses
- no scripture leakage
- no raw source metadata
- no corrupted characters
- no weak or missing practical action
- no preachy tone
- no unstable grammar loops

### Rejection criteria

Reject examples if they:

- sound synthetic or circular
- overuse phrases like `what matters is` with no concrete application
- remain philosophical but not useful
- turn metaphysics into vague motivational filler
- fail to emotionally match the prompt

---

## 6. Pilot Plan

### First 2–3 Upanishads to test

Recommended pilot set:

- **Katha Upanishad**
- **Kena Upanishad**
- **Mundaka Upanishad**

Why these three:

- philosophically central
- relatively manageable in size
- strong teachings on fear, self, knowledge, and inward clarity
- less structurally chaotic than Chandogya or Brihadaranyaka

### Expected passage count

Pilot estimated canonical passages:

- Kena: `20-40`
- Katha: `60-120`
- Mundaka: `40-80`

Pilot total estimate:

- `120-240` canonical passages

### Expected approved examples

Pilot quality estimate:

- usable wisdom entries: `70-160`
- approved principles: `30-80`
- clean final training examples: `20-60`

### Acceptance criteria

Pilot is successful if:

- Upanishad boundaries are detected reliably
- section locators are preserved consistently
- at least `70%` of canonical passages are structurally valid
- at least `40%` of valid passages yield usable wisdom entries
- distilled wisdom reads as universal and non-technical
- at least `20` high-quality training examples survive audit

---

## 7. Risks

### Translation style

- Hume is strong structurally, but the language can feel old or academic.
- Distillation quality must compensate for archaic phrasing.

### Long philosophical passages

- Some passages are too large for one wisdom unit.
- Over-large segments may produce vague or bloated principles.

### OCR corruption

- Diacritics, ligatures, and scan artifacts can damage both passage segmentation and wisdom extraction.

### Footnotes and editorial notes

- These may be mistaken for canonical text if not aggressively filtered.

### Repetition

- Many texts repeat core metaphysical formulations.
- Without filtering, the dataset may become thematically rich but stylistically repetitive.

### Over-abstract wisdom

- The Upanishads can drift into identity-and-reality language that sounds deep but is not actionable.
- This is the biggest downstream dataset risk.

### Risk checklist

- validate source extraction quality before parser work
- test segmentation on one shorter Upanishad first
- inspect repetitive distilled-wisdom patterns early
- keep audit strict from the start

---

## 8. Next Coding Tasks

Ordered implementation tasks:

1. Add one Hume source PDF into `storage/source_documents/` through the existing ingestion flow.
2. Extract raw text and inspect page-level quality manually.
3. Create a working note of all expected Upanishad title variants and division keywords.
4. Design a deterministic Upanishad-boundary detector.
5. Design a deterministic section/division detector.
6. Design a passage-splitting heuristic for prose and verse-like blocks.
7. Design exclusion filters for headers, footers, page numbers, editor notes, and OCR noise.
8. Define the exact `verse_number` locator format for Upanishad passages.
9. Implement a pilot parser for Kena, Katha, and Mundaka only.
10. Inspect pilot canonical outputs manually.
11. Run wisdom extraction on pilot passages.
12. Run distilled wisdom generation on pilot wisdom entries.
13. Inspect weak, vague, and over-abstract distillations.
14. Tune rejection rules before expanding to more Upanishads.
15. Generate pilot training examples from approved distilled wisdom.
16. Run full audit on the pilot set.
17. Review failure reasons and refine filters.
18. Expand parser coverage to the remaining principal Upanishads.
19. Create a versioned export for `upanishads_v1`
20. Add dataset metadata under `datasets/metadata/`

---

## Final Recommendation

The best engineering path is:

- reuse the existing pipeline
- keep v1 scoped to the principal Upanishads
- keep `CanonicalVerse` as the working canonical-passage store
- start with a 3-text pilot
- optimize for **clarity and quality**, not coverage

If the pilot produces clean, universal, non-repetitive distilled wisdom, then the full 13-text corpus is worth implementing as the next dataset family after the Gita.

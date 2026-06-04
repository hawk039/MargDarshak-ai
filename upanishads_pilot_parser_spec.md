# Upanishads Pilot Parser Specification

This document defines the pilot parser behavior for Upanishads Dataset v1.

It is based on:

* [upanishads_ingestion_plan.md](/Users/mayankdhyani/PycharmProjects/marg-darshak-ai-service/upanishads_ingestion_plan.md)
* [upanishads_implementation_checklist.md](/Users/mayankdhyani/PycharmProjects/marg-darshak-ai-service/upanishads_implementation_checklist.md)

Pilot scope:

* Kena Upanishad
* Katha Upanishad
* Mundaka Upanishad

This is a specification only. It does **not** add parser code.

---

## 1. Pilot Source Assumptions

### Expected source

The pilot parser is designed for:

* **Robert Ernest Hume, _The Thirteen Principal Upanishads_**

This should be treated as the primary ingestion source for the pilot.

### Expected text structure

The parser should assume the extracted raw text contains:

* one continuous source document with multiple Upanishads in sequence
* clearly printed Upanishad headings
* translator or editorial material near book boundaries
* internal structural headings that differ by Upanishad
* page headers, page numbers, and occasional source noise

### How Upanishad names may appear

The parser should expect title variants like:

* `Kena Upanishad`
* `Kena Upanisad`
* `Kena`
* `The Kena Upanishad`
* `Katha Upanishad`
* `Katha Upanisad`
* `Katha`
* `The Katha Upanishad`
* `Mundaka Upanishad`
* `Mundaka Upanisad`
* `Mundaka`
* `The Mundaka Upanishad`

The parser should allow:

* uppercase headings
* title-case headings
* OCR-softened variants where the title is still unambiguous

### How sections, chapters, and parts may appear

The parser should expect different structural markers by text:

* **Kena**:
  * section-style divisions
  * khanda-like numbering
  * short mantra blocks and brief explanations
* **Katha**:
  * chapter/part style divisions
  * dialogue-oriented teaching blocks
  * structured progression between Nachiketas and Death
* **Mundaka**:
  * `Mundaka` and `Khanda` style divisions
  * compact teaching passages, often aphoristic or semi-verse-like

The parser must not assume a single numbering format across all three texts.

---

## 2. Canonical Unit Definition

### Definition

A `CanonicalPassage` for the pilot means one clean, self-contained teaching unit extracted from the source.

This unit is **not always a verse**.

It may be:

* one mantra
* one numbered teaching sentence
* one short paragraph
* one dialogue exchange
* one grouped mantra cluster if the ideas are too fragmented when split individually

### What makes a good canonical passage

A canonical passage should:

* preserve the original source location
* contain a complete enough teaching idea to support wisdom extraction
* be small enough to distill into one universal lesson
* avoid mixing multiple unrelated ideas

### What should not be considered a canonical passage

Do not treat the following as canonical passages:

* title-only lines
* section headings by themselves
* speaker labels by themselves
* footnotes
* bibliography items
* editorial explanations outside the translated text
* noisy OCR fragments

---

## 3. Passage Boundaries

### 3.1 Kena Upanishad

#### Boundary strategy

Use **section-based extraction**.

Preferred unit:

* one numbered or clearly delimited teaching segment

Fallback unit:

* a short adjacent group of lines if one individual line is too incomplete on its own

#### Expected parser behavior

* detect `Kena` heading
* detect major internal division markers
* split by explicit numbering where present
* keep short explanatory or interpretive prose together with the directly attached translated unit only if it clearly belongs to that unit

#### Kena passage rule

If a translated line is too short to stand alone as a wisdom-bearing passage, it may be grouped with the immediately following line only when:

* both are within the same section
* both express one continuous teaching idea

### 3.2 Katha Upanishad

#### Boundary strategy

Use **chapter / section / dialogue-based extraction**.

Preferred unit:

* one compact dialogue teaching block
* one numbered verse or prose segment

Fallback unit:

* a grouped exchange where separating lines would weaken the teaching meaning

#### Expected parser behavior

* detect `Katha` heading
* detect chapter-like and section-like markers
* identify dialogue structure around Nachiketas and Death
* preserve speaker information when confidently inferable

#### Katha passage rule

For Katha, a canonical passage may include:

* one speaker statement
* one response statement
* or one short two-part exchange

but should not include:

* extended multi-paragraph narrative blocks unless they clearly form one philosophical teaching unit

### 3.3 Mundaka Upanishad

#### Boundary strategy

Use **Mundaka / Khanda-based extraction**.

Preferred unit:

* one numbered teaching block within a Mundaka/Khanda section

Fallback unit:

* a compact grouped passage if the text is too broken by line extraction

#### Expected parser behavior

* detect `Mundaka` heading
* detect `Mundaka` and `Khanda` transitions
* split using explicit numbering and local section structure
* keep aphoristic continuity where two lines clearly form one teaching image

#### Mundaka passage rule

Do not merge large spans just because they are structurally adjacent. Prefer smaller units unless:

* the split creates incomplete metaphors
* the split destroys the meaning of the teaching image

---

## 4. Fields to Extract

Each pilot canonical passage should produce the following extracted fields:

* `source_document_id`
* `source_title`
* `upanishad_name`
* `chapter`
* `section`
* `passage_number`
* `speaker`
* `original_text`
* `english_translation`
* `commentary_or_note`
* `page_reference`
* `is_valid`

### Field intent

#### `source_document_id`

* the source document record already used by the pipeline

#### `source_title`

* expected value: the source document title or normalized corpus title

#### `upanishad_name`

* one of:
  * `Kena`
  * `Katha`
  * `Mundaka`

#### `chapter`

* top-level structural number or ordinal for the current Upanishad
* use string form if the implementation later needs flexibility

#### `section`

* local division label such as:
  * `Section 1`
  * `Khanda 2`
  * `Part I`
  * `Mundaka 2, Khanda 1`

#### `passage_number`

* exact local locator string
* examples:
  * `1`
  * `1.2`
  * `I.3`
  * `2.1.4`

#### `speaker`

* use when explicit or strongly inferable
* examples:
  * `Nachiketas`
  * `Death`
  * `teacher`
  * `student`
  * `narrator`
* otherwise use null

#### `original_text`

* optional Sanskrit source text if present and cleanly extractable
* do not force-fill if source extraction is corrupted

#### `english_translation`

* the main clean translated teaching text
* this is the most important field

#### `commentary_or_note`

* optional explanatory text only if it clearly belongs to the passage and is intentionally retained
* translator footnotes should not go here by default

#### `page_reference`

* the source page locator from raw extraction

#### `is_valid`

* boolean quality flag based on passage validity rules below

---

## 5. Cleaning Rules

The parser should normalize extracted text before canonical passage creation.

### Remove page numbers

Remove:

* standalone page numbers
* repeated page counters
* page numbers embedded in header/footer lines

### Remove headers and footers

Remove lines containing:

* repeated source title text
* repeated translator or edition identifiers
* repeated running headers
* scan watermark fragments

### Remove footnotes

Remove:

* bottom-of-page note blocks
* numeric footnote markers when clearly editorial
* bracketed source-note fragments

If an inline number may be a real passage number, keep it until structure parsing confirms otherwise.

### Remove editor notes

Remove:

* editorial introductions
* translator comments not part of the translated passage
* commentary-like insertions that are outside the canonical text body

### Remove Sanskrit transliteration corruption

Remove or invalidate lines containing strong corruption such as:

* broken diacritics
* repeated unreadable symbols
* OCR ligature noise
* non-language symbol clusters

If corruption affects only `original_text`, preserve clean `english_translation` when possible.

### Remove empty speaker-only lines

Remove lines like:

* `Death said:`
* `Nachiketas said:`
* `The teacher said:`

when they appear alone without a teaching sentence.

### Remove bibliography and index text

Remove:

* bibliography pages
* index text
* table of contents spillover
* back matter

---

## 6. Validity Rules

A pilot passage is valid if all of the following are true:

* it contains a complete teaching idea
* it is not just a title
* it is not only a speaker label
* it is not only ritual metadata
* it is not a footnote
* it is long enough to distill into wisdom

### Additional validity guidance

A valid passage should also:

* read coherently after whitespace cleanup
* preserve one main philosophical idea
* be understandable without surrounding page furniture
* have enough semantic density for a distilled universal lesson

### Minimum content rule

Reject passages that are:

* too short to express an intelligible teaching
* incomplete due to page split corruption
* mostly OCR noise
* mostly structural markers with little actual content

---

## 7. Rejection Examples

These are examples of text patterns that should be rejected.

### Title-only examples

* `Kena Upanishad`
* `Second Khanda`
* `Mundaka II`

### Speaker-only examples

* `Death said:`
* `Nachiketas said:`
* `The pupil asked:`

### Ritual metadata examples

* isolated structural labels with no teaching body
* inventory-style lines listing divisions only
* sacrificial cross-reference fragments with no humanly interpretable lesson

### Footnote/editorial examples

* `Cf. SBE, Vol. XV, p. 123`
* `(Translator's note)`
* bracketed editorial reference text

### OCR corruption examples

* strings dominated by unreadable symbols
* line fragments containing broken transliteration without recoverable meaning
* mixed header/footer contamination plus broken sentence fragments

### Empty or fragmentary examples

* isolated half-sentences after a page break
* lines containing only one or two content words
* repeated trailing fragments from the previous page

---

## 8. Acceptance Criteria

The pilot parser is successful if:

* it extracts clean passages from all 3 texts
* it yields at least `60-120` canonical passages
* it yields at least `40-80` usable wisdom entries
* there is no obvious footnote or header contamination
* the passages can be distilled into universal wisdom

### Additional success indicators

The pilot is especially strong if:

* Kena passages remain compact and coherent
* Katha dialogue units preserve philosophical clarity without over-grouping
* Mundaka locators are preserved consistently
* speaker fields are present only when genuinely useful
* rejected passages are explainably bad rather than randomly lost

---

## 9. Next Coding Tasks

After this spec, implementation should proceed in this order:

1. Ingest the Hume source PDF through the existing source document flow.
2. Extract raw text and inspect Kena, Katha, and Mundaka boundaries manually.
3. Build a working title-variant map for the three pilot Upanishads.
4. Build heading-detection patterns for:
   * Kena sections
   * Katha chapter/section/dialogue blocks
   * Mundaka / Khanda structure
5. Build cleanup filters for:
   * page numbers
   * headers
   * footers
   * footnotes
   * editor notes
   * bibliography/index text
6. Build passage-splitting heuristics for each pilot Upanishad separately.
7. Define exact `chapter`, `section`, and `passage_number` conventions.
8. Extract pilot canonical passages into a testable structured output.
9. Manually inspect the first extraction sample.
10. Adjust grouping logic where units are too small or too large.
11. Run wisdom extraction on the pilot output.
12. Inspect distilled wisdom quality.
13. Tighten rejection rules for over-abstract or corrupted passages.
14. Confirm the pilot meets the acceptance criteria before expanding to the full principal corpus.

---

## Final Parsing Principle

For the Upanishads pilot, the parser should optimize for:

* **clarity over coverage**
* **clean teaching passages over literal page segmentation**
* **distillable wisdom over maximal text retention**

If a passage is structurally present but not good raw material for universal human guidance, it should be rejected rather than forced into the dataset.

# Upanishads Ingestion Plan

## Goal

Create `Dataset v1` from the Upanishads using the existing Marg Darshak pipeline:

1. source document ingestion
2. raw text extraction
3. canonical passage extraction
4. wisdom entry generation
5. distilled wisdom generation
6. principle quality review
7. training example generation
8. dataset audit and export

This plan is intentionally limited to analysis and design. It does not propose code changes yet.

---

## 1. Recommended English Translation Source

### Primary Recommendation

Use **Robert Ernest Hume, _The Thirteen Principal Upanishads_ (1921)** as the main source text for Dataset v1.

Recommended references:

* [The Thirteen Principal Upanishads, Robert Ernest Hume (Divinity Archive)](http://hdl.handle.net/11258/35673)
* [The Thirteen Principal Upanishads, public-domain PDF mirror](https://pratclif.com/liberty/hume/Hume_1395_EBk_v4.pdf)

### Why Hume is the best v1 source

* It is a **public-domain English translation**, which is important for internal dataset building and versioned repository storage.
* It already groups the **principal Upanishads into one corpus**, which is easier to manage than collecting scattered book-by-book editions.
* It preserves relatively clear **text boundaries**, headings, and internal divisions.
* It is more suitable for philosophical extraction than a loose devotional compilation.
* It is broad enough to produce a meaningful first dataset while still being finite and structured.

### Secondary Reference for QA and boundary cross-checking

Use **Max Müller’s _The Upanishads_ (Sacred Books of the East, Volumes 1 and 15)** as a structural validation source.

References:

* [The Upanishads, Part 1 (SBE 1)](https://sacred-texts.com/hin/sbe01/)
* [The Upanishads, Part 2 (SBE 15)](https://sacred-texts.com/hin/sbe15/index.htm)

Why keep Müller as a reference:

* the Sacred Texts edition exposes many internal divisions clearly
* it is useful for verifying chapter, khanda, prapathaka, and question boundaries
* it can help identify OCR mistakes or missing section breaks in the Hume PDF

### Source not recommended as primary v1 base

**Swami Paramananda, _The Upanishads_ (Project Gutenberg)** is public domain and readable, but not ideal as the main canonical source for v1.

Reference:

* [The Upanishads by Swami Paramananda (Project Gutenberg)](https://www.gutenberg.org/ebooks/3283)

Reason:

* it is better as a readability reference than as the main canonical segmentation source
* it is less useful than Hume for building a repeatable passage-level extraction pipeline

---

## 2. Recommended Scope for Dataset v1

### Recommended corpus scope

Dataset v1 should target the **Thirteen Principal Upanishads**, not the full 108.

Recommended list:

* Isha
* Kena
* Katha
* Prashna
* Mundaka
* Mandukya
* Taittiriya
* Aitareya
* Chandogya
* Brihadaranyaka
* Shvetashvatara
* Kaushitaki
* Maitri

### Why not the full 108 yet

* the minor Upanishads vary much more in style and quality
* many are highly technical, sectarian, or yoga-ritual specific
* parser complexity rises sharply
* v1 should prove the pipeline on the most philosophically useful and broadly relevant texts first

---

## 3. Canonical Structure Recommendation

The Gita pipeline currently expects something like chapter + verse. For the Upanishads, the canonical unit should be **passage-level**, not always verse-level.

### Recommended canonical unit

One `CanonicalVerse` record should represent one **teaching passage**:

* one mantra
* one numbered prose segment
* or one compact dialogue unit if the source is not purely metrical

### Recommended structural mapping

Use:

* `chapter_number`
  Meaning: top-level sequence number within the specific Upanishad
* `verse_number`
  Meaning: composite passage identifier as a string, for example:
  * `1`
  * `1.3`
  * `2.1.4`
  * `III.7`
  * `Question 4.6`
* `speaker`
  Meaning: narrator or dialog voice when it can be inferred:
  * Yajnavalkya
  * Nachiketas
  * Death
  * teacher
  * student
  * sages

### Important canonical principle

For Upanishads, `verse_number` should be treated as a **textual locator string**, not assumed to be a simple numeric verse like the Gita.

### Practical structural model by text type

Different Upanishads use different internal systems:

* **Kena**: khanda-based
* **Katha**: valli / section structure
* **Prashna**: question-based
* **Mundaka**: mundaka + khanda
* **Taittiriya**: valli / anuvaka style groupings
* **Chandogya**: long prose chapters with many short numbered units
* **Brihadaranyaka**: dense prose dialogue blocks with large philosophical passages
* **Shvetashvatara**: more verse-like and compact
* **Maitri**: mixed prose and teaching blocks

So the ingestion plan should normalize everything to:

`Upanishad -> Major Division -> Minor Division -> Passage`

while still preserving the original identifiers inside the passage label.

---

## 4. Parsing Challenges

The Upanishads will be harder to parse cleanly than the Bhagavad Gita.

### A. No single universal numbering scheme

The Gita uses predictable verse markers. The Upanishads do not.

Expected numbering patterns:

* chapter / section
* khanda
* adhyaya
* valli
* prapathaka
* question
* anuvaka
* numbered prose segments

This means a single regex strategy will not be enough for all books.

### B. Prose-heavy passages

Many important Upanishads are not mostly short verses. They contain:

* long prose dialogues
* repeated refrains
* question-answer structures
* philosophical expositions embedded inside narrative framing

This creates a segmentation challenge:

* too small a split produces fragmented wisdom
* too large a split produces vague and overstuffed principles

### C. Invocation and ritual prefatory material

Many editions include:

* opening peace invocations
* editorial introductions
* translator notes
* footnotes
* cross-references

These should not automatically enter the wisdom dataset.

### D. OCR and diacritic noise

Expected issues:

* broken Sanskrit transliteration
* ligature corruption
* unusual hyphenation
* page header/footer bleed
* repeated scan watermarks or PDF line breaks

### E. Speaker inference is less explicit

Some passages are direct dialogues; others are embedded teaching voice. Speaker labeling will be weaker and more heuristic than in the Gita.

### F. Philosophical density

Some passages are too abstract to become good user-facing guidance without distortion. The quality filters will need to reject:

* purely cosmological passages
* ritual classification passages
* overly technical metaphysics without practical human application

---

## 5. Expected Wisdom Categories

The Upanishads should produce a different flavor of wisdom than the Gita. The Gita is stronger on action, duty, conflict, and discipline. The Upanishads are stronger on self-knowledge, reality, and inner seeing.

### Core expected wisdom categories

* self-knowledge and the deeper self
* unity of Atman and Brahman
* detachment from appearances
* discernment between the real and the transient
* fearlessness in the face of death and change
* desire, craving, and inner restlessness
* stillness, contemplation, and inner attention
* truthfulness and integrity
* non-separation and interconnectedness
* inner witness consciousness
* liberation from ignorance
* restraint of mind and senses
* humility before knowledge
* the value of teacher-student inquiry
* peace beyond possession and outcome

### Categories likely to produce the strongest distilled wisdom

These are likely to convert best into universal, modern, user-facing lessons:

* detachment from outcomes
* inner stillness
* self-knowledge
* fear and mortality
* craving and dissatisfaction
* identity beyond social roles
* truth vs illusion
* awareness and mental steadiness

### Categories likely to need stronger filtering

These may be philosophically rich but weak for direct coaching examples:

* ritual symbolism
* cosmological enumeration
* sacrificial correspondences
* highly technical metaphysical formulae
* repetitive liturgical praise sections

---

## 6. Expected User Problem Categories

The Upanishads can support a strong counseling-style dataset, but the user problems will differ slightly from the Gita.

### High-value user problem categories

* confusion about identity
* uncertainty about purpose
* fear of death or impermanence
* anxiety rooted in control and uncertainty
* attachment to results and possessions
* loneliness and separation
* grief and change
* self-doubt
* mental restlessness
* comparison and insecurity
* lack of inner peace
* existential emptiness
* moral disorientation
* over-identification with status, career, or roles
* difficulty letting go
* spiritual seeking without clarity

### Categories where the Gita will still remain stronger

The Gita will likely remain the stronger source for:

* duty under conflict
* action under pressure
* righteous struggle
* disciplined service
* ethical action in social roles

The Upanishads will likely be stronger for:

* existential inquiry
* identity and consciousness
* impermanence
* the roots of fear
* inward freedom

---

## 7. Dataset Size Estimate

This estimate assumes the **Thirteen Principal Upanishads** are ingested as the v1 corpus.

### Canonical passage estimate

Expected `CanonicalVerse` records:

* conservative estimate: `900-1,100`
* ambitious estimate: `1,100-1,500`

Why the range is wide:

* segmentation choice matters a lot in prose texts
* Chandogya and Brihadaranyaka can expand quickly if split too finely
* shorter texts like Isha, Kena, Mandukya, and Mundaka are much easier

### Wisdom entry estimate

Expected usable `WisdomEntry` records after filtering:

* `500-900`

Reason:

* many passages will be too abstract, too ritual, or too repetitive
* a significant portion will still yield strong distilled human lessons

### Approved principle estimate

Expected `principle_status = approved` records:

* `180-350`

This is a realistic first-pass range if quality filters stay strict.

### Final training example estimate

Since the current strategy produces roughly one strong example per approved principle:

* generated examples: `180-350`
* likely clean exportable examples after dataset audit: `120-250`

This is a healthy size for a first Upanishads-only LoRA experiment.

---

## 8. Recommended Ingestion Strategy for v1

### Recommended path

Dataset v1 should be built in two phases:

#### Phase A: pilot subset

Start with 6 easier and higher-yield texts:

* Isha
* Kena
* Katha
* Mundaka
* Prashna
* Mandukya

Why:

* shorter
* cleaner internal structure
* more aphoristic
* easier to validate manually
* likely to yield a strong first wisdom dataset quickly

#### Phase B: full principal corpus

Then add:

* Taittiriya
* Aitareya
* Chandogya
* Brihadaranyaka
* Shvetashvatara
* Kaushitaki
* Maitri

Why:

* these expand philosophical depth
* but they introduce more prose density and parser complexity

### Why phased ingestion is better than a single big push

* it reduces parser debugging pain
* it makes quality drift easier to catch
* it allows the dataset review layer to evolve before the hardest texts are added

---

## 9. Recommendations for the Existing Marg Darshak Pipeline

No implementation yet, but the plan should assume these pipeline realities:

* the current `CanonicalVerse` model can still work if `verse_number` is treated as a flexible locator string
* Upanishads need **passage-level parsing**, not strict verse-only parsing
* distilled wisdom will be especially important because many raw translations are too metaphysical for direct user guidance
* principle quality review must remain strict to block vague abstractions
* training generation should prefer passages with:
  * clear human relevance
  * emotional resonance
  * practical contemplative value

---

## 10. Final Recommendation

For Marg Darshak Dataset v1, the best plan is:

* use **Hume’s _The Thirteen Principal Upanishads_** as the primary corpus
* use **Max Müller’s SBE volumes** as structural QA references
* scope v1 to the **principal Upanishads**, not the full 108
* normalize canonical records to **Upanishad -> division -> passage**
* expect **prose segmentation**, not just verse extraction
* begin with a **pilot subset of 6 texts**, then expand to the full 13
* expect the strongest downstream value in:
  * self-knowledge
  * detachment
  * inner stillness
  * fear and impermanence
  * existential clarity

If done carefully, the Upanishads should complement the Gita well:

* **Gita** for action, duty, conflict, and discipline
* **Upanishads** for identity, consciousness, non-attachment, and inward freedom

That combination is likely to produce a much stronger long-term Marg Darshak wisdom corpus than either source alone.

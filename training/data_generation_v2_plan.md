# Dataset Generation V2 Plan

## Goal

Expand Marg Darshak training data from approved wisdom entries into a broader, cleaner, and more diverse supervision set without retraining yet.

This plan assumes we will use only already approved wisdom sources and distilled human-readable teachings. The purpose is to prepare a stronger `expanded_v1` dataset that reduces template lock-in and improves scenario coverage before the next LoRA cycle.

## 1. Source Pool

The source pool for Dataset Generation V2 should be limited to approved wisdom records only.

### Gita source pool

Use only `WisdomEntry` rows where:

* `source_document_id` corresponds to the approved Bhagavad Gita source
* `principle_status = "approved"`
* `distilled_wisdom` is present and non-empty
* `confidence_score >= 80`

### Upanishad source pool

Use only `WisdomEntry` rows where:

* `source_document_id = 3`
* `book_title` is one of:
  * `Kena`
  * `Katha`
  * `Mundaka`
* `principle_status = "approved"`
* `distilled_wisdom` is present and non-empty
* `confidence_score >= 80`

### Core source rule

Generation should use:

* `distilled_wisdom` as the primary teaching source

Do not generate from:

* raw translation alone
* raw commentary alone
* weak or review-stage principles

## 2. Scenario Expansion

For each approved wisdom entry, generate `5-8` different user situations. The expansion should vary both wording and lived context while preserving the same underlying lesson.

Each wisdom entry should be mapped into multiple practical life domains such as:

* career
* relationships
* discipline
* fear/anxiety
* attachment
* purpose
* self-control
* inner conflict

### Scenario design principle

The user problem should not feel like a paraphrase of the same sentence with only one noun changed. Each scenario should feel like a real person asking from a slightly different life angle.

### Example scenario families

If a wisdom entry is about detachment from outcomes, possible scenario variants include:

* career:
  * “I keep tying my self-worth to whether this opportunity works out.”
* relationships:
  * “I cannot stop replaying how I want this person to respond.”
* discipline:
  * “I start well, but I panic when progress is not immediate.”
* fear/anxiety:
  * “My mind spirals because I keep needing certainty before I act.”
* purpose:
  * “I want to move forward, but I keep obsessing over whether it will all matter.”

### Expansion rules

For each wisdom entry:

* generate at most `1` scenario per category in the first pass
* avoid producing multiple near-identical prompts in the same category
* skip categories where the wisdom does not naturally apply
* prefer `5` strong scenarios over `8` weak ones

## 3. Response Structure Diversity

The expanded dataset should deliberately use multiple answer styles so the model learns range without losing tone.

At minimum, define and rotate across these `10` response formats:

### 1. Reflective paragraph

* warm acknowledgment
* one central lesson
* one practical next step

### 2. Direct practical guidance

* shorter and cleaner
* more action-oriented
* minimal abstraction

### 3. Question-led guidance

* uses one or two calm reflective questions
* still ends with one action

### 4. Short calm answer

* compact but complete
* suitable for emotionally overloaded prompts

### 5. Metaphor-based answer

* includes one restrained metaphor
* never theatrical or mystical

### 6. Action-first answer

* starts with what to do
* then explains why it helps

### 7. Inner-dialogue style

* helps the user distinguish reaction from deeper judgment
* useful for conflict, fear, and confusion

### 8. Decision-clarity style

* optimized for choices, uncertainty, and hesitation

### 9. Habit-correction style

* optimized for discipline, self-control, distraction, and relapse

### 10. Surrender/detachment style

* optimized for control, outcomes, trust, letting go, and impermanence

### Diversity rule

The same wisdom entry should not use the same response structure in all expanded examples. Structure selection should rotate intentionally.

## 4. Quality Rules

Every generated example must pass a stricter writing-quality screen before it is considered exportable.

### Required qualities

* no repeated scaffolds
* no listicles unless intentionally rare
* no scripture metadata
* no Sanskrit unless essential
* one practical action
* `70-140` words
* natural human wording

### Additional rules

* no direct chapter/verse/book references in visible assistant text
* no synthetic filler phrases
* no response that merely restates the user’s problem
* no response with more than one main teaching idea
* no overuse of words like:
  * `clarity`
  * `steadiness`
  * `truth`
  * `pressure`
  unless naturally justified

### Action rule

Each assistant response should include exactly one concrete next step, such as:

* write one sentence
* pause and name the fear
* choose one honest action
* delay one impulse
* have one calm conversation
* release one expectation

The action should be observable, simple, and relevant.

## 5. Dataset Target

The target for `expanded_v1` should be:

* `300-500` clean examples

### Hard constraints

* no exact duplicate user prompts
* no exact duplicate assistant responses
* balanced emotional categories

### Balance target

Try to avoid overweighting only:

* clarity/confusion
* discipline
* attachment

Ensure meaningful representation across:

* fear/anxiety
* grief/loss
* trust/surrender
* purpose/direction
* self-control
* relational strain
* decision pressure
* inner fragmentation

### Practical target distribution

A reasonable first target split:

* Gita-derived examples: `180-280`
* Upanishad-derived examples: `120-220`

The exact split should depend on approved source pool size and quality, not forced symmetry.

## 6. Audit Plan

The expanded dataset should go through a dedicated multi-pass audit before training.

### Repetition audit

Check for:

* repeated openings
* repeated bridge sentences
* repeated action sentences
* repeated response fingerprints

### Actionability audit

Check that:

* each response includes one practical action
* action is concrete
* action matches the user problem

### Philosophical clarity audit

Check that:

* the response expresses one coherent lesson
* the lesson is understandable without scripture knowledge
* the teaching is useful, not decorative

### Safety audit

Check that:

* no therapy or medical claims
* no unsafe mental-health authority language
* no coercive or absolute spiritual claims

### Tone audit

Check that:

* tone is calm and grounded
* response is not preachy
* response is not cold or robotic
* response does not sound synthetic or stitched together

## 7. Output Datasets

The V2 generation flow should eventually produce:

* [datasets/merged/marg_darshak_expanded_v1.jsonl](/Users/mayankdhyani/PycharmProjects/marg-darshak-ai-service/datasets/merged/marg_darshak_expanded_v1.jsonl)
* [training/data/train_expanded_v1.jsonl](/Users/mayankdhyani/PycharmProjects/marg-darshak-ai-service/training/data/train_expanded_v1.jsonl)

### Companion metadata

Also generate a metadata file later describing:

* source pool counts
* examples per category
* examples per response structure
* audit pass rates
* final approved count

## Recommended Generation Flow

When implementation begins, the safest order is:

1. load approved Gita + Upanishad wisdom pools
2. normalize category labels and scenario slots
3. generate draft user scenarios per wisdom entry
4. generate assistant responses with controlled structure rotation
5. run repetition and quality lint
6. drop weak or duplicate rows
7. audit the cleaned set
8. export `expanded_v1`

## Implementation Guidance

When coding starts, optimize for:

* better examples, not maximum expansion
* sentence diversity at generation time
* auditability and deterministic behavior
* easy removal of low-quality clusters

The main risk is reintroducing the same template lock-in that affected earlier merged LoRA runs. So V2 should treat diversity and prose quality as first-class design constraints, not post-processing afterthoughts.

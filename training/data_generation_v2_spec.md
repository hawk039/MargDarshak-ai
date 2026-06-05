# Dataset Generation V2 Implementation Spec

## Goal

This document turns [training/data_generation_v2_plan.md](/Users/mayankdhyani/PycharmProjects/marg-darshak-ai-service/training/data_generation_v2_plan.md) into an implementation-ready specification for generating `300-500` diverse Marg Darshak training examples.

This is a generation spec only.

It does **not** introduce code, retraining, or application changes.

## 1. Exact Source Query

The V2 generation pipeline should use only approved `WisdomEntry` rows with strong distilled teachings.

### Global source filter

Include only entries where:

* `principle_status = "approved"`
* `principle_quality_score >= 80`
* `distilled_wisdom IS NOT NULL`
* `distilled_wisdom != ""`

### Gita source query

Select all approved Gita wisdom entries where:

* `source_document_id` belongs to the Bhagavad Gita source set
* `book_title` indicates the Gita corpus
* all global filters above pass

Implementation guidance:

* if multiple Gita `source_document_id` values exist, include only the cleaned approved Gita source currently used for exportable dataset generation
* exclude any wisdom entries tied to chunk-based legacy extraction paths if they are not the canonical approved source

### Upanishad source query

Select all approved Upanishad wisdom entries where:

* `source_document_id = 3`
* `book_title IN ("Kena", "Katha", "Mundaka")`
* all global filters above pass

### Required fields to load per wisdom entry

For generation, load at least:

* `id`
* `source_document_id`
* `book_title`
* `chapter`
* `section`
* `verse_number`
* `distilled_wisdom`
* `emotional_tags`
* `philosophical_tags`
* `confidence_score`

### Source pool normalization

Before generation:

* normalize `emotional_tags` and `philosophical_tags` to lowercase lists
* remove empty or duplicate tags
* collapse obvious equivalents if needed:
  * `self_control` and `self-control`
  * `self_knowledge` and `self-knowledge`

## 2. Scenario Taxonomy

Generation V2 should use exactly `8` scenario families:

* `career`
* `relationship`
* `discipline`
* `fear_change`
* `attachment`
* `purpose`
* `self_control`
* `inner_conflict`

For each family, generation should draw from a template bank and then fill it with wisdom-specific framing.

### 2.1 Career

#### User-problem templates

1. I feel pulled between security and meaningful work, and I cannot tell which voice to trust.
2. My career decisions feel heavy because I keep measuring myself by outcomes.
3. I know I need to act, but fear keeps making the next professional step feel bigger than it is.
4. I feel lost about work, and the pressure to choose correctly is making me freeze.
5. I want to move forward in my career without losing my deeper values.
6. I keep overthinking professional choices until I lose sight of what is actually mine to do.
7. I feel stuck between ambition and honesty, and it is making work feel confusing.
8. I want to do my work sincerely, but I keep tying my peace to the result.
9. Responsibility at work feels heavy, and I want to act without panic.
10. I am trying to choose a career direction, but my mind keeps multiplying consequences.

#### Forbidden repeated wording

Avoid overusing:

* `career confusion`
* `what is the right path`
* `career choice`
* `next honest step` as the exact prompt phrase

#### Emotional tags required/preferred

Required or preferred:

* `confusion`
* `fear`
* `purpose`
* `attachment`
* `duty`

### 2.2 Relationship

#### User-problem templates

1. My relationship tension keeps pulling me into reaction instead of wisdom.
2. I keep expecting another person to respond a certain way, and it is exhausting me.
3. I want to respond with honesty in this relationship, but hurt keeps taking over first.
4. I feel disappointed again and again because I keep gripping what I want from someone else.
5. Part of me wants to soften, but another part keeps guarding itself.
6. I know I need a calmer response in this relationship, but emotion keeps getting there first.
7. I want more steadiness in how I relate to others, especially when I feel misunderstood.
8. My attachment to being understood is making every conversation feel heavier.
9. I keep reacting from insecurity in relationships, and I want to return to something deeper.
10. I want to care deeply without letting fear or control define how I show up.

#### Forbidden repeated wording

Avoid overusing:

* `my relationship is full of tension`
* `respond wisely`
* `another person`

#### Emotional tags required/preferred

Required or preferred:

* `attachment`
* `anger`
* `fear`
* `ego`
* `trust`

### 2.3 Discipline

#### User-problem templates

1. I keep breaking my own structure when discomfort appears.
2. I want stronger discipline, but I keep slipping when the moment gets inconvenient.
3. My routines collapse as soon as emotional pressure rises.
4. I know what steadiness requires, but I keep choosing what is easier.
5. I want a more reliable inner structure instead of bursts of effort.
6. I keep losing discipline in the same places, and I want to interrupt that pattern.
7. I start sincerely, but I do not stay steady long enough for the habit to take root.
8. I want to build discipline without turning it into self-punishment.
9. My good intentions keep fading before they become action.
10. I am tired of making promises to myself that I do not keep.

#### Forbidden repeated wording

Avoid overusing:

* `I keep slipping into the same pattern`
* `steadier discipline`
* `good intentions`

#### Emotional tags required/preferred

Required or preferred:

* `discipline`
* `self-control`
* `restlessness`
* `desire`

### 2.4 Fear Change

#### User-problem templates

1. I know change is natural, but I still react as if it will undo me.
2. Fear keeps turning uncertainty into something catastrophic.
3. I want to act, but the possibility of loss keeps shrinking my courage.
4. When life changes suddenly, I feel as if I lose my inner ground.
5. I keep treating uncertainty like proof that something is wrong.
6. Fear of change keeps narrowing my judgment and slowing my next step.
7. I want steadiness in uncertainty, but fear keeps taking over my thinking.
8. My mind keeps reading change as danger even when I know better.
9. I feel threatened by endings, even when part of me knows life is moving naturally.
10. I want to meet change with honesty, but my fear keeps getting there first.

#### Forbidden repeated wording

Avoid overusing:

* `afraid of change or loss`
* `fear is stopping me`
* `change is unavoidable`

#### Emotional tags required/preferred

Required or preferred:

* `fear`
* `grief`
* `trust`
* `inner_steadiness`
* `death`

### 2.5 Attachment

#### User-problem templates

1. I care deeply, but I keep handing my peace over to outcomes.
2. I know I cannot control everything, but my mind keeps gripping anyway.
3. The more I want something, the less steady I become around it.
4. My expectations are making simple effort feel heavy and tense.
5. I keep tying my emotional balance to whether life obeys my preferred ending.
6. I want to work sincerely without being consumed by the result.
7. The outcome keeps taking too much of my attention.
8. I feel trapped by wanting certainty before I can stay calm.
9. My effort becomes distorted whenever I get too attached to how things should unfold.
10. I want to care without becoming controlled by what I want back.

#### Forbidden repeated wording

Avoid overusing:

* `too attached to the result`
* `obsessing over outcomes`
* `loosen my grip`

#### Emotional tags required/preferred

Required or preferred:

* `attachment`
* `desire`
* `fear`
* `detachment`

### 2.6 Purpose

#### User-problem templates

1. I am searching for direction, but everything feels shallow right now.
2. I want a deeper way of living, but I keep getting lost in surface pressures.
3. I feel disconnected from what really matters to me.
4. Part of me knows life needs a truer center, but I do not know how to return to it.
5. I keep moving through responsibilities without feeling inwardly aligned.
6. I want to live from something deeper than habit and appearance.
7. I feel ungrounded in purpose, even when life looks functional from the outside.
8. I keep asking what matters, but my mind stays on the surface.
9. I want more inward direction, not just more external progress.
10. Life feels crowded, but not deeply meaningful right now.

#### Forbidden repeated wording

Avoid overusing:

* `life lacks deeper direction`
* `deeper way of living`
* `surface-level life`

#### Emotional tags required/preferred

Required or preferred:

* `purpose`
* `self_knowledge`
* `reality`
* `consciousness`

### 2.7 Self Control

#### User-problem templates

1. My impulses keep getting ahead of my deeper judgment.
2. I want more restraint, especially when emotion starts driving the moment.
3. I know what would be wiser, but I keep yielding to what is immediate.
4. I want to interrupt the impulse before it becomes action.
5. My reactions often arrive before my judgment does.
6. I keep doing what feels easier in the moment and regretting it later.
7. I want a stronger inner pause before I act.
8. I lose self-command when the pressure becomes emotional.
9. I want to guide my impulses instead of obeying them.
10. I keep getting carried away before I can return to myself.

#### Forbidden repeated wording

Avoid overusing:

* `self-control`
* `impulse`
* `restraint`
  as the exact repeated prompt framing

#### Emotional tags required/preferred

Required or preferred:

* `self-control`
* `desire`
* `anger`
* `ego`
* `discipline`

### 2.8 Inner Conflict

#### User-problem templates

1. Part of me wants what is wise, but another part keeps reaching for what is easier.
2. I feel pulled in different directions inside, and it is making even simple choices heavy.
3. I cannot tell which part of me is speaking truth and which part is speaking fear.
4. My mind keeps arguing with itself, and I want a steadier center.
5. I feel inwardly fragmented and do not know how to return to wholeness.
6. One part of me wants honesty, but another part wants comfort and escape.
7. I feel torn between what I know and what I keep doing.
8. I want to return to a deeper center instead of reacting from inner conflict.
9. Different voices inside me keep pulling at the same decision.
10. I want to stop living from fragmentation and return to something more whole.

#### Forbidden repeated wording

Avoid overusing:

* `part of me wants`
* `inner struggle`
* `pulled in different directions`

#### Emotional tags required/preferred

Required or preferred:

* `confusion`
* `ego`
* `desire`
* `inner_steadiness`
* `self_knowledge`

## 3. Response Structure Taxonomy

Generation V2 should rotate across exactly `10` response structures.

### 3.1 reflection_action

#### Response shape

* acknowledgment
* one distilled lesson
* one practical action
* quiet closing

#### Word range

* `95-130`

#### Practical action style

* one calm, concrete step

#### Phrases to avoid

* `what matters is`
* `that is often the turning point`

### 3.2 direct_clarity

#### Response shape

* plain statement of the lesson
* brief explanation
* one action

#### Word range

* `80-110`

#### Practical action style

* clean and immediate

#### Phrases to avoid

* overly soft build-up
* abstract spiritual framing first

### 3.3 question_guided

#### Response shape

* acknowledgment
* one or two reflective questions
* one action

#### Word range

* `90-125`

#### Practical action style

* action follows reflection

#### Phrases to avoid

* too many questions
* therapeutic interrogation tone

### 3.4 short_grounding

#### Response shape

* compact reassurance
* simple lesson
* one action

#### Word range

* `70-95`

#### Practical action style

* grounding act

#### Phrases to avoid

* compressed abstraction
* ornamental language

### 3.5 metaphor_based

#### Response shape

* one restrained metaphor
* lesson
* one action

#### Word range

* `90-120`

#### Practical action style

* metaphor should support, not replace, the action

#### Phrases to avoid

* mystical imagery
* dramatic symbolism

### 3.6 action_first

#### Response shape

* begin with what to do
* then explain why
* end with calm reinforcement

#### Word range

* `80-110`

#### Practical action style

* very concrete

#### Phrases to avoid

* long abstract preamble

### 3.7 inner_dialogue

#### Response shape

* separate reaction from deeper judgment
* lesson
* one action

#### Word range

* `95-130`

#### Practical action style

* journaling, naming, pausing, witnessing

#### Phrases to avoid

* roleplay theatricality
* quoted dialogue blocks

### 3.8 decision_filter

#### Response shape

* define the decision problem
* offer a mental filter
* one action

#### Word range

* `85-120`

#### Practical action style

* sort options, name what is true, choose next act

#### Phrases to avoid

* generic decision matrix language

### 3.9 habit_correction

#### Response shape

* identify repeating pattern
* explain the wiser shift
* one action

#### Word range

* `90-125`

#### Practical action style

* interrupt pattern early

#### Phrases to avoid

* self-help productivity cliches

### 3.10 surrender_detachment

#### Response shape

* soften grip
* distinguish effort from control
* one action

#### Word range

* `90-125`

#### Practical action style

* release one expectation
* name what remains yours to do

#### Phrases to avoid

* fatalism
* passivity
* religious surrender language

## 4. Pairing Logic

Each wisdom entry should map to:

* `2-4` scenario families
* `2-3` response structures
* maximum `6` examples per wisdom entry

### Family mapping logic

Map by tags:

* `duty`, `karma` -> `career`, `discipline`
* `attachment`, `desire` -> `attachment`, `relationship`, `inner_conflict`
* `fear`, `death`, `change`, `grief` -> `fear_change`, `inner_conflict`
* `self_knowledge`, `identity`, `non_duality` -> `purpose`, `inner_conflict`
* `meditation`, `restlessness`, `discipline` -> `discipline`, `self_control`
* `teacher_student`, `humility`, `learning` -> `discipline`, `purpose`
* `trust`, `surrender`, `detachment` -> `attachment`, `fear_change`, `purpose`

### Structure mapping logic

Map by scenario family:

* `career` -> `decision_filter`, `direct_clarity`, `reflection_action`
* `relationship` -> `reflection_action`, `question_guided`, `inner_dialogue`
* `discipline` -> `habit_correction`, `action_first`, `direct_clarity`
* `fear_change` -> `short_grounding`, `reflection_action`, `surrender_detachment`
* `attachment` -> `surrender_detachment`, `reflection_action`, `question_guided`
* `purpose` -> `metaphor_based`, `reflection_action`, `inner_dialogue`
* `self_control` -> `habit_correction`, `action_first`, `inner_dialogue`
* `inner_conflict` -> `inner_dialogue`, `decision_filter`, `question_guided`

### Max examples per wisdom entry

Hard cap:

* `6` examples per wisdom entry

Preferred pattern:

* `5` examples when the teaching is broadly useful
* `3-4` when the teaching is narrow

## 5. Diversity Constraints

The generator must enforce:

* no duplicate user prompts
* no duplicate assistant responses
* same opening max `3`
* same practical action max `3`
* same `distilled_wisdom` max `5` examples
* balanced scenario categories

### Category balancing target

Try to keep each scenario family between roughly:

* `10%` and `18%` of the final dataset

### Additional diversity rules

* do not let one response structure dominate more than `20%` of the set
* avoid reusing the same bridge sentence more than `3` times
* avoid reusing the same action closing more than `3` times

## 6. Audit Rules

Every generated row should go through:

### Repetition audit

Reject or downgrade when:

* opening phrase repeats too often
* same bridge sentence appears too often
* same response fingerprint appears more than once

### Listicle detection

Reject when:

* response contains numbered lists
* response contains markdown bullets unless intentionally rare and approved

### Scripture leakage

Reject when visible assistant text contains:

* book names
* chapter references
* verse references
* Sanskrit terms not required for meaning

### Medical or therapy claims

Reject when:

* response implies therapy authority
* response gives medical guidance
* response frames itself as treatment

### Generic motivation

Reject or downgrade when:

* response sounds like generic inspiration
* lesson is not tied to the user problem
* action could fit almost any prompt

### Actionability

Reject or downgrade when:

* no concrete next step
* more than one main action
* action is vague or non-observable

### Response length

Require:

* `70-140` words

### Tone

Require:

* calm philosophical tone
* not preachy
* not robotic
* not synthetic or stitched

## 7. Output Format

Final output must use JSONL chat format:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are Marg Darshak, a calm philosophical guide inspired by Indian wisdom traditions. You help users with inner battles using gentle reflection, clarity, and practical action. You are not a therapist, doctor, or religious authority."
    },
    {
      "role": "user",
      "content": "<user_problem>"
    },
    {
      "role": "assistant",
      "content": "<assistant_response>"
    }
  ]
}
```

## 8. Target Output

Generation V2 should eventually produce:

* [datasets/merged/marg_darshak_expanded_v1.jsonl](/Users/mayankdhyani/PycharmProjects/marg-darshak-ai-service/datasets/merged/marg_darshak_expanded_v1.jsonl)
* [training/data/train_expanded_v1.jsonl](/Users/mayankdhyani/PycharmProjects/marg-darshak-ai-service/training/data/train_expanded_v1.jsonl)
* [training/evaluation/expanded_v1_generation_report.md](/Users/mayankdhyani/PycharmProjects/marg-darshak-ai-service/training/evaluation/expanded_v1_generation_report.md)

### The report should include

* source wisdom entry count
* examples generated per scenario family
* examples generated per response structure
* rows removed by audit
* duplicate prompt groups found and removed
* scaffold counts
* final approved count

## Recommended Execution Order

When implementation begins:

1. query approved Gita + Upanishad wisdom entries
2. normalize tags and classify scenario families
3. assign `2-4` family targets per wisdom entry
4. assign `2-3` response structures per wisdom entry
5. generate candidate user prompts
6. filter duplicate and near-duplicate prompts
7. generate assistant responses
8. run repetition and prose lint
9. run audit pass
10. export `expanded_v1`

## Final Constraint

If a wisdom entry cannot produce a clean, scenario-specific, naturally worded example under these rules, skip it. Quality is more important than forcing every approved wisdom entry into the expanded dataset.

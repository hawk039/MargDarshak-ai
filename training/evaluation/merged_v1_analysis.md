# Merged v1 LoRA Analysis

This analysis reviews the first merged Marg Darshak LoRA run using:

* the earlier Gita-only LoRA evaluation artifacts in [training/evaluation/evaluation_report.md](/Users/mayankdhyani/PycharmProjects/marg-darshak-ai-service/training/evaluation/evaluation_report.md)
* the earlier Gita-only summary in [training/evaluation/evaluation_analysis.md](/Users/mayankdhyani/PycharmProjects/marg-darshak-ai-service/training/evaluation/evaluation_analysis.md)
* the recent terminal test outputs comparing:
  * Base Qwen
  * Gita LoRA
  * merged v1 LoRA

The goal here is not to retrain or reconfigure, only to understand what the merged adapter learned and where it broke down.

## 1. Repetition Patterns

The merged v1 LoRA shows stronger repetition than the Gita-only adapter in several prompts.

Most visible repeated patterns:

* `A calmer response is often...`
* `That is because...`
* `It turns reflection into something you can live today.`
* repeated emotion-control phrases like:
  * `stop letting fear decide`
  * `stop letting anger decide`
  * `stop letting guilt decide`
* repeated abstract closure patterns like:
  * `That is where steadiness starts.`
  * `What matters is...`

This repetition appears at two levels:

* corpus-level phrase reuse across multiple prompts
* within-response duplication, where the same clause or logic is repeated almost immediately

Examples:

* Prompt 2 repeats the same sentence shell several times:
  * `That is, you can stop letting fear decide...`
  * `That is, you can stop letting anger decide...`
  * `That is, you can stop letting depression decide...`
  * `That is, you can stop letting guilt decide...`
* Prompt 4 repeats the same idea twice:
  * `A calmer response is often the wiser one...`
  * followed by nearly the same claim again in the final sentence

## 2. Looping Patterns

The merged adapter also shows clear looping behavior, which is worse than simple repetition.

Observed loop types:

* sentence restarts with the same stem
* semantic loops where the response says nearly the same thing in slightly different wording
* runaway continuation where the model keeps extending a template instead of completing a thought cleanly

Examples:

* Prompt 2 becomes a literal loop of emotional substitutions:
  * fear -> anger -> depression -> guilt -> repeated again
* Prompt 4 loops on the same conceptual pair:
  * calm response
  * wiser one
  * reflection you can live today
* Prompt 5 restates the same fear-management idea multiple times instead of moving into one concrete action

This is a stronger failure mode than what we saw in the Gita-only LoRA. The earlier Gita model often sounded templated, but the merged model more often gets stuck inside the template.

## 3. Template Overuse

The merged v1 adapter appears to have overfit to a narrow response scaffold.

Common merged template frame:

1. calm philosophical opener
2. abstract framing sentence
3. repeated justification sentence
4. shallow action or pseudo-action
5. repeated closure

Template indicators:

* `A calmer response is often...`
* `What helps is remembering that...`
* `That is because...`
* `It turns reflection into something you can live today.`
* `This becomes the starting point...`

Compared with the Gita-only adapter:

* Gita LoRA overused phrases like `cold`, `what matters`, and `clarity`
* merged LoRA keeps some of those habits, but also adds a new explanatory scaffold that sounds smoother at first and then collapses into formula

This suggests the merge increased dataset breadth, but not enough true stylistic diversity.

## 4. Weak Responses

The weakest merged responses share one or more of these problems:

* looping
* unnatural phrasing
* low specificity
* fake actionability
* emotional mismatch

Worst examples from the shared test:

### Prompt 2: avoidance

Why weak:

* severe looping
* unnatural insertion of `depression` and `guilt`
* no grounded next step
* reads like token substitution rather than guidance

### Prompt 4: uncertainty

Why weak:

* repeats the same idea twice
* feels inflated rather than insightful
* lacks concrete response beyond broad reassurance

### Prompt 5: fear stopping action

Why weak:

* starts well but becomes redundant
* overexplains panic without landing on one clear act
* repeats `stop letting the feeling command your next move`

### Prompt 3: attachment to outcome

Why weak:

* too short for the emotional load
* generic and detached
* line like `It helps train the whole person` feels vague and synthetic

## 5. Strong Responses

The merged adapter is not failing everywhere. It does show real gains in a few areas.

Stronger qualities:

* less scripture leakage than the older Gita-style generations
* more natural use of distilled wisdom in some prompts
* somewhat better grounding in universal human themes
* less listicle formatting than base or old Gita outputs in some prompts

Best example from the shared test:

### Prompt 1: career confusion

Why relatively strong:

* stays focused on career confusion
* includes a practical move: list what matters, what kind of work feels right, what kind of people to work with
* sounds more like guidance than explanation

Even here, though, the sentence `clarity grows through lived experience, not through some hidden truth` is a little awkward. So this is promising, not fully polished.

## 6. Dataset Causes

The merged behavior strongly suggests dataset-level causes rather than training instability.

Most likely causes:

### A. Template-heavy source responses

The merged dataset likely preserved too many responses with repeated scaffolds such as:

* `What helps is...`
* `What matters is...`
* `A calmer response...`
* `It turns reflection into something you can live today.`

When those are present across both Gita and Upanishad exports, the adapter learns the shell too strongly.

### B. Too many near-duplicate explanation sentences

Even when exact duplicates were removed, there were still many semantically similar explanation lines. LoRA can overfit to these patterns quickly at small dataset size.

### C. Weak action diversity

The training set seems to contain many responses that talk about action in abstract terms, but fewer that end with one crisp, specific next step.

### D. Style merge without enough normalization

The Gita and Upanishad sets were both written in Marg Darshak style, but not with enough sentence-level cleanup before merging. That means the merged model may have inherited:

* Gita phrasing loops
* Upanishad distilled abstractions
* repeated calm-acknowledgement structures

### E. Small dataset, strong memorization pressure

`151` examples is enough for a first LoRA experiment, but still small. With a narrow style band, the model is likely to memorize preferred stems and replay them too aggressively.

## 7. Recommendations

The next dataset iteration should optimize for sentence diversity and grounded usefulness, not just more samples.

### Highest-priority fixes

* remove or rewrite repeated opening stems:
  * `A calmer response is often...`
  * `What matters is...`
  * `That is because...`
* remove explanation sentences that can be swapped mechanically with different emotions
* reject any response that repeats a sentence stem inside the same example
* reject any response where the practical action is abstract rather than observable

### Dataset cleanup recommendations

* add a merge-time lint pass for:
  * repeated sentence stems
  * repeated clause patterns
  * semantic duplicates
  * loop-like continuation
* add a “single concrete action” requirement:
  * one action
  * one sentence
  * directly tied to the user problem
* reduce semicolon-heavy constructions
* cut responses that sound like stitched fragments rather than one coherent voice

### Modeling recommendations for the next dataset version

* keep the Gita and Upanishad wisdom sources
* tighten the final response-writing layer before export
* use fewer but better responses if needed
* prioritize:
  * emotional specificity
  * one clear lesson
  * one grounded next step
  * natural prose over “philosophical-sounding” prose

## Bottom Line

Merged v1 learned the Marg Darshak tone directionally, but it also amplified the most repetitive parts of the dataset.

Compared with the Gita-only LoRA:

* merged v1 is sometimes cleaner about scripture leakage
* merged v1 is more universal in theme
* but merged v1 is currently worse on looping and template lock-in

So the next move should not be another training run yet. The right next step is to improve the merged dataset itself by removing templated explanation scaffolds, tightening action sentences, and filtering loop-prone responses before LoRA v2 retraining.

# Evaluation Analysis

This analysis is based on:

* [training/evaluation/evaluation_report.md](/Users/mayankdhyani/PycharmProjects/marg-darshak-ai-service/training/evaluation/evaluation_report.md)
* [training/evaluation/results.json](/Users/mayankdhyani/PycharmProjects/marg-darshak-ai-service/training/evaluation/results.json)

Overall result:

* Base total score: `413`
* LoRA total score: `395`
* Verdict: Base Qwen outperformed the current Marg Darshak LoRA on this evaluation set.

There was also one tie:

* Prompt 1: career confusion (`20` vs `20`)

## 1. Prompts Where LoRA Beat Base

LoRA performed better on 8 of 20 prompts:

* Prompt 4: attachment to outcomes (`22` vs `17`)
* Prompt 8: jealousy (`18` vs `16`)
* Prompt 11: uncertainty and steadiness (`19` vs `17`)
* Prompt 13: purpose (`20` vs `19`)
* Prompt 15: decision making (`26` vs `23`)
* Prompt 16: relationship tension (`22` vs `21`)
* Prompt 17: expectations and disappointment (`23` vs `21`)
* Prompt 19: trust vs certainty (`18` vs `17`)

What these wins have in common:

* LoRA often sounded more inward, reflective, and philosophically framed.
* LoRA usually stayed closer to the Marg Darshak tone when the prompt was about attachment, uncertainty, trust, or expectation.
* LoRA sometimes gave a more distilled emotional-spiritual framing than Base, which helped clarity scores.

## 2. Prompts Where Base Beat LoRA

Base performed better on 11 of 20 prompts:

* Prompt 2: procrastination (`23` vs `20`)
* Prompt 3: fear of failure (`24` vs `17`)
* Prompt 5: discipline struggles (`21` vs `20`)
* Prompt 6: anxiety (`22` vs `20`)
* Prompt 7: anger (`26` vs `20`)
* Prompt 9: grief (`22` vs `20`)
* Prompt 10: loneliness (`21` vs `17`)
* Prompt 12: self-doubt (`21` vs `20`)
* Prompt 14: burnout (`23` vs `18`)
* Prompt 18: inner conflict (`18` vs `15`)
* Prompt 20: resilience after setbacks (`21` vs `20`)

What these losses have in common:

* Base was usually more concrete and more actionable.
* Base often gave clearer step-by-step guidance.
* LoRA responses were more likely to become vague, repetitive, or grammatically unstable.
* LoRA underperformed most clearly on emotionally heavy prompts where practical grounding mattered.

## 3. Common Strengths of LoRA

The current LoRA does have some clear strengths:

* Better philosophical framing on themes like attachment, trust, expectation, and uncertainty.
* More consistent inward-guidance voice when it stayed coherent.
* Stronger tendency to speak in terms of steadiness, clarity, response, and self-awareness rather than generic self-help lists.
* Less likely than Base to drift into explicit scripture explanation or external authority language.
* In its best outputs, LoRA sounded closer to a calm reflective guide than to a general productivity assistant.

## 4. Common Weaknesses of LoRA

The weaknesses are fairly consistent and explain why the total score fell below Base:

* Repetition at sentence level.
  Example patterns included repeated words like `cold`, `again again`, `what matters`, and mirrored sentence constructions.
* Awkward or unstable phrasing.
  Some outputs sounded partially synthetic rather than naturally written.
* Weak practical action.
  Several responses framed the issue well but did not end with a clear next step.
* Drift into vague abstraction.
  At times the response stayed “philosophical” without becoming useful.
* Emotional mismatch.
  Some prompts received a generic contemplative answer rather than a response tightly fitted to the user’s actual emotional state.
* Overuse of internal stock phrases.
  Phrases about calmness, coldness, truth, and inner response repeated too often across prompts.
* Loss of clarity under pressure.
  Prompts involving procrastination, anger, grief, burnout, and fear especially exposed this weakness.

## 5. Recommendations for the Next Dataset Iteration

The next dataset iteration should focus on response quality, not dataset size.

Priority recommendations:

* Add more high-quality examples for:
  * procrastination
  * fear of failure
  * anger
  * anxiety
  * grief
  * loneliness
  * burnout
  * resilience
* Increase the proportion of examples with a strong practical closing step.
  The LoRA needs to end more responses with a concrete next action.
* Remove vague sentence patterns from the training set.
  Especially reduce phrases built from abstract loops like `what matters is`, `becoming cold`, `this is how`, and repeated mirrored constructions.
* Add a stronger writing-quality filter before export.
  Reject examples with duplicated wording, unstable phrasing, or low-specificity abstractions.
* Add scenario-specific emotional grounding.
  Fear, grief, anger, and burnout need noticeably different acknowledgment patterns rather than one shared reflective voice.
* Add negative filters for synthetic-sounding language.
  Examples containing repeated adjacent concepts, awkward intensifiers, or circular sentences should not enter the final dataset.
* Increase action diversity.
  Keep the philosophical voice, but pair it with more grounded actions like pausing, writing, naming the fear, taking one small step, or having one honest conversation.
* Add a final human review pass for the export set.
  This would likely catch the exact responses that currently sound thoughtful at first glance but weaken on reread.

## Bottom Line

The current LoRA is directionally promising, not yet stronger overall than Base.

It already shows a recognizable Marg Darshak voice on themes like attachment, trust, and inner steadiness. But the dataset still allows too much repetitive, vague, and weakly actionable language. The next dataset version should preserve the calm philosophical tone while tightening coherence, specificity, and practical usefulness.

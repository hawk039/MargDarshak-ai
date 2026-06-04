# Merged v2.1 Rewrite Expansion Report

- starting v2 count: 70
- added rewritten count: 28
- final v2.1 count: 98
- skipped count: 25

## Repeated Scaffold Counts Before

- `that matters because`: 40
- `it turns reflection into something you can live today`: 20
- `it helps action grow cleaner`: 11
- `that is often the turning point`: 3

## Repeated Scaffold Counts After

- `that matters because`: 44
- `it turns reflection into something you can live today`: 32
- `it helps action grow cleaner`: 23
- `that is often the turning point`: 9

## Duplicate Prompt Checks

- exact unique prompts: 98
- exact unique assistant responses: 98

## Rewrite Examples Before/After

- source: gita:63
  theme: discipline_self_control
  before: I want more self-control, especially when emotion or impulse starts taking over.
  after: My resolve keeps weakening at the moment I most need discipline.
  assistant_score: 85 final_score: 90

- source: gita:80
  theme: discipline_self_control
  before: I keep slipping into the same unhelpful pattern, and I want a wiser habit to take its place.
  after: I keep breaking trust with myself in small ways, and I want a wiser habit to replace that.
  assistant_score: 85 final_score: 90

- source: gita:99
  theme: discipline_self_control
  before: I keep slipping into the same unhelpful pattern, and I want a wiser habit to take its place.
  after: I know what steadiness requires, but I keep yielding to the easier impulse.
  assistant_score: 85 final_score: 90

- source: gita:119
  theme: discipline_self_control
  before: I want more self-control, especially when emotion or impulse starts taking over.
  after: I want stronger self-control, but my habits keep sliding back into what is easy.
  assistant_score: 85 final_score: 90

- source: gita:50
  theme: discipline_self_control
  before: I am trying to work on building discipline, but I keep slipping into the same inner struggle.
  after: My better intentions keep collapsing under impulse, and I want steadier discipline.
  assistant_score: 85 final_score: 89

- source: gita:55
  theme: discipline_self_control
  before: I keep slipping into the same unhelpful pattern, and I want a wiser habit to take its place.
  after: I start with sincerity, but I keep losing structure when discomfort appears.
  assistant_score: 85 final_score: 89

- source: gita:75
  theme: duty_action
  before: I am trying to work on deepening devotion, but I keep slipping into the same inner struggle.
  after: When duty feels heavy, I start wavering instead of moving forward.
  assistant_score: 85 final_score: 89

- source: gita:81
  theme: duty_action
  before: I want to surrender what I cannot control, but I do not know how to do that honestly.
  after: I keep shrinking back from the responsibility that I know belongs to me.
  assistant_score: 85 final_score: 89

- source: gita:85
  theme: trust_let_go
  before: How do I soften into trust without becoming passive or careless?
  after: I keep gripping for certainty, and it is making honest trust harder.
  assistant_score: 85 final_score: 89

- source: gita:91
  theme: duty_action
  before: I am worn out from holding everything so tightly, and I need help letting go well.
  after: I want to act with integrity, but I keep freezing when responsibility becomes real.
  assistant_score: 80 final_score: 86

- source: gita:121
  theme: trust_let_go
  before: I am worn out from holding everything so tightly, and I need help letting go well.
  after: I want to trust what I cannot control, but I keep turning uncertainty into pressure.
  assistant_score: 80 final_score: 86

- source: gita:1
  theme: attachment_outcome
  before: My mind keeps swinging between options, and I need a steadier way to choose.
  after: My mind gets trapped in how things should turn out, and it keeps disturbing my steadiness.
  assistant_score: 79 final_score: 85

- source: gita:8
  theme: attachment_outcome
  before: I am overthinking a decision and I want to act from clarity instead of mental noise.
  after: The outcome keeps pulling too much of my attention, and I want a cleaner way to act.
  assistant_score: 79 final_score: 85

- source: gita:20
  theme: attachment_outcome
  before: My mind keeps swinging between options, and I need a steadier way to choose.
  after: I keep exhausting myself by trying to control how everything ends.
  assistant_score: 79 final_score: 85

- source: gita:48
  theme: trust_let_go
  before: I am overthinking a decision and I want to act from clarity instead of mental noise.
  after: The more uncertain life feels, the more tightly I try to force it.
  assistant_score: 79 final_score: 85

- source: gita:83
  theme: attachment_outcome
  before: My mind keeps swinging between options, and I need a steadier way to choose.
  after: I want to work sincerely, but I keep handing my peace over to the result.
  assistant_score: 79 final_score: 85

- source: gita:95
  theme: duty_action
  before: I know what I need to do, but I keep resisting the responsibility in front of me.
  after: The next action is obvious, but emotional pressure keeps making me delay it.
  assistant_score: 79 final_score: 85

- source: gita:51
  theme: attachment_outcome
  before: I keep trying to control every outcome, and it is draining the life out of my effort.
  after: My peace keeps getting tied to the result, and it is draining the honesty from my effort.
  assistant_score: 75 final_score: 83

- source: gita:32
  theme: duty_action
  before: How do I stay committed to the work that is mine without being crushed by it?
  after: The responsibility is clear, but I still hesitate when it is time to act.
  assistant_score: 75 final_score: 82

- source: gita:77
  theme: clarity_decision
  before: I am trying to work on finding clarity in confusion, but I keep slipping into the same inner struggle.
  after: Mental noise keeps taking over when I try to choose carefully.
  assistant_score: 75 final_score: 82

## Skipped Examples

- source: gita:79
  theme: discipline_self_control
  user: How do I soften into trust without becoming passive or careless?
  skip_reason: no_safe_prompt_rewrite

- source: gita:86
  theme: discipline_self_control
  user: I keep breaking my own good intentions, and I want steadier discipline.
  skip_reason: no_safe_prompt_rewrite

- source: gita:57
  theme: discipline_self_control
  user: I am trying to work on building discipline, but I keep slipping into the same inner struggle.
  skip_reason: no_safe_prompt_rewrite

- source: gita:58
  theme: discipline_self_control
  user: I know what helps me, but I do not always have the restraint to follow through.
  skip_reason: no_safe_prompt_rewrite

- source: gita:25
  theme: discipline_self_control
  user: I want to do my part well without obsessing over the result.
  skip_reason: no_safe_prompt_rewrite

- source: gita:62
  theme: discipline_self_control
  user: I keep slipping into the same unhelpful pattern, and I want a wiser habit to take its place.
  skip_reason: no_safe_prompt_rewrite

- source: gita:65
  theme: discipline_self_control
  user: I keep slipping into the same unhelpful pattern, and I want a wiser habit to take its place.
  skip_reason: no_safe_prompt_rewrite

- source: gita:70
  theme: discipline_self_control
  user: How do I soften into trust without becoming passive or careless?
  skip_reason: no_safe_prompt_rewrite

- source: gita:78
  theme: discipline_self_control
  user: How do I build discipline without turning it into self-punishment?
  skip_reason: no_safe_prompt_rewrite

- source: gita:54
  theme: discipline_self_control
  user: I keep breaking my own good intentions, and I want steadier discipline.
  skip_reason: no_safe_prompt_rewrite

- source: gita:46
  theme: duty_action
  user: I know what I need to do, but I keep resisting the responsibility in front of me.
  skip_reason: theme_cap_reached

- source: gita:107
  theme: duty_action
  user: I know what I need to do, but I keep resisting the responsibility in front of me.
  skip_reason: theme_cap_reached

- source: gita:24
  theme: duty_action
  user: How do I stay committed to the work that is mine without being crushed by it?
  skip_reason: theme_cap_reached

- source: gita:27
  theme: attachment_outcome
  user: How do I care deeply about my work without clinging so tightly to what follows?
  skip_reason: theme_cap_reached

- source: gita:34
  theme: discipline_self_control
  user: My mind keeps swinging between options, and I need a steadier way to choose.
  skip_reason: no_safe_prompt_rewrite

- source: gita:56
  theme: discipline_self_control
  user: Grief and fear are making everything feel heavier than usual, and I want to stay grounded.
  skip_reason: no_safe_prompt_rewrite

- source: gita:103
  theme: attachment_outcome
  user: I keep trying to control every outcome, and it is draining the life out of my effort.
  skip_reason: theme_cap_reached

- source: gita:110
  theme: duty_action
  user: Responsibility feels heavy right now, and I want to act without panic or avoidance.
  skip_reason: theme_cap_reached

- source: gita:5
  theme: duty_action
  user: Responsibility feels heavy right now, and I want to act without panic or avoidance.
  skip_reason: theme_cap_reached

- source: gita:17
  theme: clarity_decision
  user: I am overthinking a decision and I want to act from clarity instead of mental noise.
  skip_reason: theme_cap_reached

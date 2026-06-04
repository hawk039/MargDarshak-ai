# Merged v2 Dataset Cleanup Report

- original count: 151
- kept count: 70
- removed count: 81
- duplicate prompt groups removed: 0
- duplicate prompt rows removed: 0
- duplicate assistant rows removed: 0

## Top Removal Reasons

- duplicate_user_prompt: 77
- no_concrete_next_step: 61
- too_many_semicolons: 53
- repeated_scaffold:it turns reflection into something you can live today: 43
- below_final_score_threshold: 31
- weak_practical_action: 30
- repeated_scaffold:it helps action grow cleaner: 29
- semicolon_heavy: 28
- repeated_scaffold:that matters because: 25
- repeated_scaffold:that is often the turning point: 20

## Repeated Scaffold Counts Before

- `that matters because`: 65
- `it turns reflection into something you can live today`: 63
- `it helps action grow cleaner`: 40
- `that is often the turning point`: 23

## Repeated Scaffold Counts After

- `that matters because`: 40
- `it turns reflection into something you can live today`: 20
- `it helps action grow cleaner`: 11
- `that is often the turning point`: 3

## 20 Sample Kept Examples

- source: upanishads:1
  final_score=97 prompt=100 response=95 repetition=94 action=100
  user: I know what is right, but I keep choosing comfort instead of the harder truthful path.
  assistant: There is nothing strange about feeling unsettled when the mind and heart are pulling in different directions. What helps here is to remember that peace becomes possible when desire stops directing your choices. In a moment like this, that matters because it helps you respond from deeper steadiness instead of reacting from habit or pressure. Write down one comfort you keep obeying, then take one step that aligns better with what you truly value. You do not need perfect certainty to begin; you only need enough honesty to take the next right step.
  reasons: repeated_scaffold:that matters because

- source: upanishads:2
  final_score=97 prompt=100 response=95 repetition=94 action=100
  user: Part of me knows change is natural, but I still panic when life shifts unexpectedly.
  assistant: Some struggles feel especially draining because they disturb both clarity and self-trust at the same time. A steadier way to hold this is to see that fear loses force when you stop reading change as proof that you are lost. In a moment like this, that matters because it helps you respond from deeper steadiness instead of reacting from habit or pressure. Write down what you fear losing, then name one part of you that remains intact even if circumstances change. Small sincere actions often restore clarity faster than long arguments with the mind.
  reasons: repeated_scaffold:that matters because

- source: upanishads:3
  final_score=97 prompt=100 response=95 repetition=94 action=100
  user: Every big change makes me feel as if I am losing myself.
  assistant: It makes sense that this feels difficult, especially when your mind is carrying so much at once. The deeper guidance in this moment is that fear loosens when you stop treating change as the end of who you are. In a moment like this, that matters because it helps you respond from deeper steadiness instead of reacting from habit or pressure. Choose one small change you have been resisting, and meet it with one calm deliberate action today. Small sincere actions often restore clarity faster than long arguments with the mind.
  reasons: repeated_scaffold:that matters because

- source: upanishads:5
  final_score=97 prompt=100 response=95 repetition=94 action=100
  user: I want to feel inwardly steady, but my sense of self keeps shifting with my mood.
  assistant: When the inner life becomes crowded, even good intentions can lose their direction. One useful truth to lean on here is that wisdom becomes practical when desire no longer sets the direction of your life. In a moment like this, that matters because it helps you respond from deeper steadiness instead of reacting from habit or pressure. Choose one moment today to stop following the mental story and return to one honest grounding statement. Steadiness usually returns through practice, not through one perfect breakthrough.
  reasons: repeated_scaffold:that matters because

- source: upanishads:10
  final_score=97 prompt=100 response=95 repetition=94 action=100
  user: Restlessness is draining my energy because my attention never feels settled.
  assistant: It is human to feel disoriented when deeper steadiness is being challenged from several sides. The deeper guidance in this moment is that a calmer mind is built by returning attention again and again to truth. In a moment like this, that matters because it helps you respond from deeper steadiness instead of reacting from habit or pressure. Set a short timer, choose one task, and gently return to it each time the mind wanders. You do not need perfect certainty to begin; you only need enough honesty to take the next right step.
  reasons: repeated_scaffold:that matters because

- source: upanishads:11
  final_score=97 prompt=100 response=95 repetition=94 action=100
  user: I feel mentally overactive, and it is becoming harder to return to what matters.
  assistant: Many people reach this kind of threshold when inner pressure becomes louder than inner clarity. This starts to soften when you work from the understanding that clarity grows when the mind learns how to return instead of keep wandering. In a moment like this, that matters because it helps you respond from deeper steadiness instead of reacting from habit or pressure. Set a short timer, choose one task, and gently return to it each time the mind wanders. Steadiness usually returns through practice, not through one perfect breakthrough.
  reasons: repeated_scaffold:that matters because

- source: upanishads:12
  final_score=97 prompt=100 response=95 repetition=94 action=100
  user: I am tired of being mentally pulled in every direction all day long.
  assistant: This is the sort of moment where gentleness and honesty matter more than forcing certainty. One useful truth to lean on here is that the mind clears when attention stops drifting and comes back to what matters. In a moment like this, that matters because it helps you respond from deeper steadiness instead of reacting from habit or pressure. Set a short timer, choose one task, and gently return to it each time the mind wanders. Small sincere actions often restore clarity faster than long arguments with the mind.
  reasons: repeated_scaffold:that matters because

- source: upanishads:13
  final_score=97 prompt=100 response=95 repetition=94 action=100
  user: My inner restlessness makes it hard to stay present with even one clear task.
  assistant: Moments of inward conflict often become easier once the mind is no longer trying to solve everything at once. A steadier way to hold this is to see that attention becomes healing when it no longer follows every impulse away from truth. In a moment like this, that matters because it helps you respond from deeper steadiness instead of reacting from habit or pressure. Set a short timer, choose one task, and gently return to it each time the mind wanders. Small sincere actions often restore clarity faster than long arguments with the mind.
  reasons: repeated_scaffold:that matters because

- source: upanishads:14
  final_score=97 prompt=100 response=95 repetition=94 action=100
  user: I can feel that my attention is weak right now, and it is affecting everything I do.
  assistant: When deeper clarity is buried under pressure, the next honest step can start to feel unusually far away. A steadier way to hold this is to see that steady practice helps the mind return before restlessness takes over completely. In a moment like this, that matters because it helps you respond from deeper steadiness instead of reacting from habit or pressure. Set a short timer, choose one task, and gently return to it each time the mind wanders. Clarity deepens when you practice it instead of waiting to feel fully resolved first.
  reasons: repeated_scaffold:that matters because

- source: upanishads:15
  final_score=97 prompt=100 response=95 repetition=94 action=100
  user: I feel overwhelmed by the fear that change will take away what matters most.
  assistant: This is the sort of moment where gentleness and honesty matter more than forcing certainty. A steadier way to hold this is to see that steady attention helps the mind return from distraction to what is deeply true. In a moment like this, that matters because it helps you respond from deeper steadiness instead of reacting from habit or pressure. When fear rises, breathe slowly and name one truth that still holds even in the middle of change. Clarity deepens when you practice it instead of waiting to feel fully resolved first.
  reasons: repeated_scaffold:that matters because

- source: upanishads:17
  final_score=97 prompt=100 response=95 repetition=94 action=100
  user: I want a calmer mind, but my attention keeps scattering before I can stabilize it.
  assistant: Moments like this can quietly drain confidence, even when part of you already knows what matters. One useful truth to lean on here is that attention matures when the mind no longer obeys every restless impulse. In a moment like this, that matters because it helps you respond from deeper steadiness instead of reacting from habit or pressure. Set a short timer, choose one task, and gently return to it each time the mind wanders. Clarity deepens when you practice it instead of waiting to feel fully resolved first.
  reasons: repeated_scaffold:that matters because

- source: upanishads:18
  final_score=97 prompt=100 response=95 repetition=94 action=100
  user: My thoughts keep running ahead of me, and I want to become steadier inside.
  assistant: Inner conflict often feels strongest just before a clearer way of seeing becomes available. A steadier way to hold this is to see that a calmer mind is built by returning attention again and again to truth. In a moment like this, that matters because it helps you respond from deeper steadiness instead of reacting from habit or pressure. Set a short timer, choose one task, and gently return to it each time the mind wanders. Steadiness usually returns through practice, not through one perfect breakthrough.
  reasons: repeated_scaffold:that matters because

- source: upanishads:19
  final_score=97 prompt=100 response=95 repetition=94 action=100
  user: I start with good intention, but my mind keeps slipping away before I stay with anything.
  assistant: It is understandable that you feel pulled around when deeper steadiness has been hard to access. What helps here is to remember that the mind finds balance when attention is practiced like a return, not a chase. In a moment like this, that matters because it helps you respond from deeper steadiness instead of reacting from habit or pressure. Set a short timer, choose one task, and gently return to it each time the mind wanders. Small sincere actions often restore clarity faster than long arguments with the mind.
  reasons: repeated_scaffold:that matters because

- source: upanishads:20
  final_score=97 prompt=100 response=95 repetition=94 action=100
  user: Loss feels so threatening right now that I cannot think clearly about what comes next.
  assistant: When inner pressure builds, it can distort what is actually clear and make the next step feel farther away. This starts to soften when you work from the understanding that inner steadiness grows when impermanence is not treated like personal collapse. In a moment like this, that matters because it helps you respond from deeper steadiness instead of reacting from habit or pressure. When fear rises, breathe slowly and name one truth that still holds even in the middle of change. You do not need perfect certainty to begin; you only need enough honesty to take the next right step.
  reasons: repeated_scaffold:that matters because

- source: upanishads:22
  final_score=97 prompt=100 response=95 repetition=94 action=100
  user: I know change is unavoidable, but I still react as if it will destroy something essential in me.
  assistant: Sometimes the hardest part is not the situation itself, but the way it unsettles your inner ground. One useful truth to lean on here is that inner steadiness grows when impermanence is not treated like personal collapse. In a moment like this, that matters because it helps you respond from deeper steadiness instead of reacting from habit or pressure. When fear rises, breathe slowly and name one truth that still holds even in the middle of change. Steadiness usually returns through practice, not through one perfect breakthrough.
  reasons: repeated_scaffold:that matters because

- source: upanishads:23
  final_score=97 prompt=100 response=95 repetition=94 action=100
  user: I want to meet change with more courage, but fear keeps making it feel catastrophic.
  assistant: Some struggles feel especially draining because they disturb both clarity and self-trust at the same time. This starts to soften when you work from the understanding that fear loosens when you stop treating change as the end of who you are. In a moment like this, that matters because it helps you respond from deeper steadiness instead of reacting from habit or pressure. When fear rises, breathe slowly and name one truth that still holds even in the middle of change. Clarity deepens when you practice it instead of waiting to feel fully resolved first.
  reasons: repeated_scaffold:that matters because

- source: upanishads:24
  final_score=97 prompt=100 response=95 repetition=94 action=100
  user: Even simple tasks feel hard because my mind keeps jumping to something else.
  assistant: This kind of struggle usually asks for steadiness first and answers second. A steadier way to hold this is to see that steadiness grows when distraction is noticed early and attention gently returns. In a moment like this, that matters because it helps you respond from deeper steadiness instead of reacting from habit or pressure. Set a short timer, choose one task, and gently return to it each time the mind wanders. Clarity deepens when you practice it instead of waiting to feel fully resolved first.
  reasons: repeated_scaffold:that matters because

- source: upanishads:26
  final_score=97 prompt=100 response=95 repetition=94 action=100
  user: When life changes suddenly, I feel as if my whole foundation is threatened.
  assistant: A difficult inner season often makes ordinary choices feel heavier than they need to be. One useful truth to lean on here is that steadiness grows when distraction is noticed early and attention gently returns. In a moment like this, that matters because it helps you respond from deeper steadiness instead of reacting from habit or pressure. Choose one small change you have been resisting, and meet it with one calm deliberate action today. Small sincere actions often restore clarity faster than long arguments with the mind.
  reasons: repeated_scaffold:that matters because

- source: upanishads:27
  final_score=97 prompt=100 response=95 repetition=94 action=100
  user: I do not feel grounded in myself, and it is making everything seem unstable.
  assistant: Sometimes the hardest part is not the situation itself, but the way it unsettles your inner ground. One useful truth to lean on here is that discipline brings calm when attention is no longer scattered by every impulse. In a moment like this, that matters because it helps you respond from deeper steadiness instead of reacting from habit or pressure. Choose one moment today to stop following the mental story and return to one honest grounding statement. You do not need perfect certainty to begin; you only need enough honesty to take the next right step.
  reasons: repeated_scaffold:that matters because

- source: upanishads:29
  final_score=97 prompt=100 response=95 repetition=94 action=100
  user: I feel scared that losing something important will undo me completely.
  assistant: Moments of inward conflict often become easier once the mind is no longer trying to solve everything at once. A calmer response becomes possible when you remember that fear loosens when change is no longer mistaken for the loss of your deepest identity. In a moment like this, that matters because it helps you respond from deeper steadiness instead of reacting from habit or pressure. Write down what you fear losing, then name one part of you that remains intact even if circumstances change. Steadiness usually returns through practice, not through one perfect breakthrough.
  reasons: repeated_scaffold:that matters because

## 20 Sample Removed Examples

- source: gita:2
  final_score=70 prompt=100 response=57 repetition=68 action=70
  user: I am carrying an important duty, yet I keep wavering when it is time to act.
  assistant: A season shaped by responsibility often makes duty seem harder than it really is. What you are facing is human, and it makes sense that duty is coloring this moment; That does not cancel your ability to respond wisely. A calmer way to hold this is to see that devotion becomes meaningful when sincerity matters more than outward display. That matters because it returns your attention to what can actually be practiced around duty; It turns reflection into something you can live today. The point is not to become hard; it is to act from responsibility rather than from avoidance, panic, or image; That is often the turning point between feeling trapped and acting wisely.
  reasons: too_many_semicolons, repeated_scaffold:that matters because, repeated_scaffold:it turns reflection into something you can live today, repeated_scaffold:that is often the turning point, no_concrete_next_step, weak_practical_action, duplicate_user_prompt, below_final_score_threshold

- source: gita:9
  final_score=73 prompt=100 response=61 repetition=74 action=70
  user: I feel trapped between sincere effort and fear about how everything will unfold.
  assistant: This kind of struggle often appears when anger tightens around questions of clarity. You are meeting a real inner difficulty around clarity, not failing some hidden test of calm; That does not cancel your ability to respond wisely. A calmer way to hold this is to see that desire loses its power when you stop letting it define your choices. That matters because inner steadiness grows through lived response, not mental performance around clarity; It turns reflection into something you can live today. Peace grows when effort stays sincere but the mind stops demanding guarantees before it can act; That is often the turning point between feeling trapped and acting wisely.
  reasons: semicolon_heavy, repeated_scaffold:that matters because, repeated_scaffold:it turns reflection into something you can live today, repeated_scaffold:that is often the turning point, no_concrete_next_step, weak_practical_action, duplicate_user_prompt, below_final_score_threshold

- source: gita:18
  final_score=73 prompt=100 response=61 repetition=74 action=70
  user: I keep postponing the right action because I am preoccupied with how it will turn out.
  assistant: Inner pressure grows quickly when uncertainty about direction and right action start pulling in different directions. You are meeting a real inner difficulty around right action, not failing some hidden test of calm; That does not cancel your ability to respond wisely. A calmer way to hold this is to see that inner freedom grows when you live with discipline, truth, and detachment. That matters because inner steadiness grows through lived response, not mental performance around right action; It turns reflection into something you can live today. Responsibility becomes lighter when you carry the work itself instead of carrying every imagined consequence with it; That is often the turning point between feeling trapped and acting wisely.
  reasons: semicolon_heavy, repeated_scaffold:that matters because, repeated_scaffold:it turns reflection into something you can live today, repeated_scaffold:that is often the turning point, no_concrete_next_step, weak_practical_action, duplicate_user_prompt, below_final_score_threshold

- source: gita:36
  final_score=73 prompt=100 response=61 repetition=74 action=70
  user: I am too caught up in how things should turn out, and it is disturbing my peace.
  assistant: This attachment stretch of life can feel especially tight when clarity is under strain. You are meeting a real inner difficulty around clarity, not failing some hidden test of calm; That does not cancel your ability to respond wisely. A calmer way to hold this is to see that desire loses its power when you stop letting it define your choices. That matters because inner steadiness grows through lived response, not mental performance around clarity; It helps action grow cleaner without becoming cold. Peace grows when effort stays sincere but the mind stops demanding guarantees before it can act; That is often the turning point between feeling trapped and acting wisely.
  reasons: semicolon_heavy, repeated_scaffold:that matters because, repeated_scaffold:that is often the turning point, repeated_scaffold:it helps action grow cleaner, no_concrete_next_step, weak_practical_action, below_final_score_threshold

- source: gita:105
  final_score=73 prompt=100 response=61 repetition=74 action=70
  user: How do I stay committed to the work that is mine without being crushed by it?
  assistant: Inner pressure grows quickly when responsibility and duty start pulling in different directions. You are meeting a real inner difficulty around duty, not failing some hidden test of calm; That does not cancel your ability to respond wisely. A calmer way to hold this is to see that focus on the actions you can control rather than obsessing over outcomes. That matters because inner steadiness grows through lived response, not mental performance around duty; It turns reflection into something you can live today. Responsibility becomes lighter when you carry the work itself instead of carrying every imagined consequence with it; That is often the turning point between feeling trapped and acting wisely.
  reasons: semicolon_heavy, repeated_scaffold:that matters because, repeated_scaffold:it turns reflection into something you can live today, repeated_scaffold:that is often the turning point, no_concrete_next_step, weak_practical_action, duplicate_user_prompt, below_final_score_threshold

- source: gita:118
  final_score=74 prompt=100 response=62 repetition=74 action=70
  user: How do I soften into trust without becoming passive or careless?
  assistant: Inner pressure grows quickly when spiritual longing and trust start pulling in different directions. You are not weak for feeling this pressure; devotion can change how trust appears; The pressure is real, but it does not have to decide your next move. The deeper guidance here is simple: devotion becomes meaningful when sincerity matters more than outward display. That matters because it returns your attention to what can actually be practiced around trust; It turns reflection into something you can live today. The heart often settles when it stops trying to control what can only be met with sincerity and patience; This is how steadiness starts returning in ordinary life.
  reasons: too_many_semicolons, repeated_scaffold:that matters because, repeated_scaffold:it turns reflection into something you can live today, no_concrete_next_step, weak_practical_action, duplicate_user_prompt, below_final_score_threshold

- source: gita:7
  final_score=76 prompt=100 response=66 repetition=80 action=70
  user: I am carrying an important duty, yet I keep wavering when it is time to act.
  assistant: A mind touched by attachment usually needs steadiness before it can see right action clearly. This is the kind of moment where the mind becomes louder than the deeper truth you already sense about right action; That does not cancel your ability to respond wisely. A calmer way to hold this is to see that focus on the actions you can control rather than obsessing over outcomes. That becomes useful when it keeps the next step in right action from being swallowed by emotional noise; It turns reflection into something you can live today. Action becomes steadier when you stop measuring it by applause and start measuring it by integrity; That is often the turning point between feeling trapped and acting wisely.
  reasons: semicolon_heavy, repeated_scaffold:it turns reflection into something you can live today, repeated_scaffold:that is often the turning point, no_concrete_next_step, weak_practical_action, duplicate_user_prompt, below_final_score_threshold

- source: gita:19
  final_score=76 prompt=100 response=66 repetition=80 action=70
  user: How do I stay committed to the work that is mine without being crushed by it?
  assistant: This kind of struggle often appears when attachment tightens around questions of right action. Anyone carrying this kind of inner strain around right action would feel the pull you describe; That does not cancel your ability to respond wisely. A calmer way to hold this is to see that focus on the actions you can control rather than obsessing over outcomes. That guidance helps because it loosens pressure without making you passive about right action; It helps action grow cleaner without becoming cold. Duty becomes more bearable when you stop arguing with its existence and start meeting it directly; That is often the turning point between feeling trapped and acting wisely.
  reasons: semicolon_heavy, repeated_scaffold:that is often the turning point, repeated_scaffold:it helps action grow cleaner, no_concrete_next_step, weak_practical_action, duplicate_user_prompt, below_final_score_threshold

- source: gita:108
  final_score=76 prompt=100 response=66 repetition=80 action=70
  user: I need to move on something important, but I keep getting lost in consequences.
  assistant: When restless wanting rises, it can make right action feel distant even when it is still available. Anyone carrying this kind of inner strain around right action would feel the pull you describe; You can honor the feeling without letting it command the whole response. What helps in a moment like this is remembering that desire loses its power when you stop letting it define your choices. That matters because inner steadiness grows through lived response, not mental performance around right action; It helps action grow cleaner without becoming cold. Action becomes steadier when you stop measuring it by applause and start measuring it by integrity; That is often where right action starts becoming workable again.
  reasons: semicolon_heavy, repeated_scaffold:that matters because, repeated_scaffold:it helps action grow cleaner, no_concrete_next_step, weak_practical_action, duplicate_user_prompt, below_final_score_threshold

- source: gita:16
  final_score=77 prompt=100 response=67 repetition=80 action=70
  user: Responsibility feels heavy right now, and I want to act without panic or avoidance.
  assistant: The weight you describe makes sense because fear can narrow the mind and blur right action. You are not weak for feeling this pressure; fear can change how right action appears; You can honor the feeling without letting it command the whole response. What helps in a moment like this is remembering that clarity grows when you seek understanding instead of reacting impulsively. That becomes practical when it keeps you close to truth instead of reaction in right action; It turns reflection into something you can live today. Duty becomes more bearable when you stop arguing with its existence and start meeting it directly; That is often where right action starts becoming workable again.
  reasons: too_many_semicolons, repeated_scaffold:it turns reflection into something you can live today, no_concrete_next_step, weak_practical_action, duplicate_user_prompt, below_final_score_threshold

- source: gita:21
  final_score=77 prompt=100 response=67 repetition=80 action=70
  user: Responsibility feels heavy right now, and I want to act without panic or avoidance.
  assistant: A season shaped by uncertainty about direction often makes right action seem harder than it really is. You are not weak for feeling this pressure; purpose can change how right action appears; You can honor the feeling without letting it command the whole response. What helps in a moment like this is remembering that clarity grows when you seek understanding instead of reacting impulsively. That becomes practical when it keeps you close to truth instead of reaction in right action; It turns reflection into something you can live today. Duty becomes more bearable when you stop arguing with its existence and start meeting it directly; That is often where right action starts becoming workable again.
  reasons: too_many_semicolons, repeated_scaffold:it turns reflection into something you can live today, no_concrete_next_step, weak_practical_action, duplicate_user_prompt, below_final_score_threshold

- source: gita:29
  final_score=77 prompt=100 response=67 repetition=80 action=70
  user: I know what I need to do, but I keep resisting the responsibility in front of me.
  assistant: When the heart is carrying responsibility, even simple decisions can feel unusually heavy. You are meeting a real inner difficulty around duty, not failing some hidden test of calm; You can honor the feeling without letting it command the whole response. What helps in a moment like this is remembering that desire loses its power when you stop letting it define your choices. That guidance helps because it loosens pressure without making you passive about duty; It turns reflection into something you can live today. The point is not to become hard; it is to act from responsibility rather than from avoidance, panic, or image; That is often where duty starts becoming workable again.
  reasons: too_many_semicolons, repeated_scaffold:it turns reflection into something you can live today, no_concrete_next_step, weak_practical_action, duplicate_user_prompt, below_final_score_threshold

- source: gita:37
  final_score=77 prompt=100 response=67 repetition=80 action=70
  user: I know what I need to do, but I keep resisting the responsibility in front of me.
  assistant: A mind touched by responsibility usually needs steadiness before it can see right action clearly. What you are facing is human, and it makes sense that responsibility is coloring this moment; There is still room here for a steadier choice. A useful reminder here is that clarity grows when you seek understanding instead of reacting impulsively. That becomes practical when it keeps you close to truth instead of reaction in right action; It helps action grow cleaner without becoming cold. The point is not to become hard; it is to act from responsibility rather than from avoidance, panic, or image; That is what helps the next response come from truth rather than reaction.
  reasons: too_many_semicolons, repeated_scaffold:it helps action grow cleaner, no_concrete_next_step, weak_practical_action, duplicate_user_prompt, below_final_score_threshold

- source: gita:40
  final_score=77 prompt=100 response=67 repetition=80 action=70
  user: How do I stay committed to the work that is mine without being crushed by it?
  assistant: This grief stretch of life can feel especially tight when right action is under strain. You are not weak for feeling this pressure; grief can change how right action appears; You can honor the feeling without letting it command the whole response. What helps in a moment like this is remembering that focus on the actions you can control rather than obsessing over outcomes. That becomes practical when it keeps you close to truth instead of reaction in right action; It helps action grow cleaner without becoming cold. Duty becomes more bearable when you stop arguing with its existence and start meeting it directly; That is often where right action starts becoming workable again.
  reasons: too_many_semicolons, repeated_scaffold:it helps action grow cleaner, no_concrete_next_step, weak_practical_action, duplicate_user_prompt, below_final_score_threshold

- source: gita:42
  final_score=77 prompt=100 response=67 repetition=80 action=70
  user: I keep postponing the right action because I am preoccupied with how it will turn out.
  assistant: This attachment stretch of life can feel especially tight when right action is under strain. What you are facing is human, and it makes sense that attachment is coloring this moment; There is still room here for a steadier choice. A useful reminder here is that focus on the actions you can control rather than obsessing over outcomes. That becomes practical when it keeps you close to truth instead of reaction in right action; It helps action grow cleaner without becoming cold. The point is not to become hard; it is to act from responsibility rather than from avoidance, panic, or image; That is what helps the next response come from truth rather than reaction.
  reasons: too_many_semicolons, repeated_scaffold:it helps action grow cleaner, no_concrete_next_step, weak_practical_action, duplicate_user_prompt, below_final_score_threshold

- source: gita:87
  final_score=77 prompt=100 response=67 repetition=80 action=70
  user: I am overthinking a decision and I want to act from clarity instead of mental noise.
  assistant: This confusion stretch of life can feel especially tight when clarity is under strain. Anyone carrying this kind of inner strain around clarity would feel the pull you describe; A calmer direction is still available, even before everything feels resolved. One steady truth to lean on is this: their progeny in turn populated the universe. That becomes practical when it keeps you close to truth instead of reaction in clarity; It helps action grow cleaner without becoming cold. Confusion often softens when you stop chasing certainty and start working with what is already honest; This is how pressure stops running ahead of wiser judgment. Put the decision on paper, cross out every option you already know is false, and move one step toward what remains; Let that step train steadiness, not perfection.
  reasons: too_many_semicolons, repeated_scaffold:it helps action grow cleaner, no_concrete_next_step, weak_practical_action, duplicate_user_prompt, below_final_score_threshold

- source: gita:90
  final_score=77 prompt=100 response=67 repetition=80 action=70
  user: My emotions are running ahead of me, and I need help finding steadiness again.
  assistant: The weight you describe makes sense because fear can narrow the mind and blur steadiness. Anyone carrying this kind of inner strain around steadiness would feel the pull you describe; A calmer direction is still available, even before everything feels resolved. One steady truth to lean on is this: courage begins when you do what is right even while fear is present. That becomes practical when it keeps you close to truth instead of reaction in steadiness; It turns reflection into something you can live today. Grief becomes more bearable when you stop fighting its presence and start supporting your balance within it; This is how pressure stops running ahead of wiser judgment. Let your next act be simple and safe, because courage often begins as movement before certainty; Let that step train steadiness, not perfection.
  reasons: too_many_semicolons, repeated_scaffold:it turns reflection into something you can live today, no_concrete_next_step, weak_practical_action, duplicate_user_prompt, below_final_score_threshold

- source: gita:98
  final_score=77 prompt=100 response=67 repetition=80 action=70
  user: Part of me knows I need to let go, but another part keeps gripping harder.
  assistant: Inner pressure grows quickly when the struggle to let go and trust start pulling in different directions. You are not weak for feeling this pressure; surrender can change how trust appears; You can honor the feeling without letting it command the whole response. What helps in a moment like this is remembering that devotion becomes meaningful when sincerity matters more than outward display. That becomes practical when it keeps you close to truth instead of reaction in trust; It helps action grow cleaner without becoming cold. Surrender becomes healthy when it softens demand without weakening responsibility; That is often where trust starts becoming workable again. Offer sincere effort to the work in front of you, then refuse one more round of compulsive prediction; What matters is calm follow-through, not dramatic intensity.
  reasons: too_many_semicolons, repeated_scaffold:it helps action grow cleaner, no_concrete_next_step, weak_practical_action, duplicate_user_prompt, below_final_score_threshold

- source: gita:5
  final_score=79 prompt=100 response=70 repetition=74 action=82
  user: Responsibility feels heavy right now, and I want to act without panic or avoidance.
  assistant: There are moments when grief fills the whole horizon, yet a steadier response is still possible. You are not weak for feeling this pressure; grief can change how duty appears; That does not cancel your ability to respond wisely. A calmer way to hold this is to see that focus on the actions you can control rather than obsessing over outcomes. That becomes real when you treat it as something to practice, not just admire in duty; It turns reflection into something you can live today. Right action grows cleaner when you give your energy to the task and not to rehearsing every possible result; That is often the turning point between feeling trapped and acting wisely.
  reasons: too_many_semicolons, repeated_scaffold:it turns reflection into something you can live today, repeated_scaffold:that is often the turning point, no_concrete_next_step, duplicate_user_prompt, below_final_score_threshold

- source: gita:11
  final_score=79 prompt=100 response=70 repetition=74 action=82
  user: My expectations are making me tense, and I do not know how to loosen my grip.
  assistant: A season shaped by attachment often makes clarity seem harder than it really is. You are not weak for feeling this pressure; attachment can change how clarity appears; The pressure is real, but it does not have to decide your next move. The deeper guidance here is simple: anger becomes less destructive when you pause before acting from it. That matters because it returns your attention to what can actually be practiced around clarity; It turns reflection into something you can live today. You do not become careless by loosening control; you become more available to act wisely; This is how steadiness starts returning in ordinary life. Notice where expectation is tightening your body, soften that grip, and return to the work itself; Let the value of the step be that it interrupts the old pattern.
  reasons: too_many_semicolons, repeated_scaffold:that matters because, repeated_scaffold:it turns reflection into something you can live today, no_concrete_next_step, duplicate_user_prompt, below_final_score_threshold

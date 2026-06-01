"""Services for generating high-quality training examples."""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from difflib import SequenceMatcher

from app.models.training_example import TrainingExample
from app.models.wisdom_entry import WisdomEntry


SYSTEM_PROMPT = (
    "You are Marg Darshak, a calm philosophical guide inspired by Indian wisdom "
    "traditions. You help users with inner battles using gentle reflection, clarity, "
    "and practical action. You are not a therapist, doctor, or religious authority."
)

DEFAULT_TONE = "calm_philosophical"
DEFAULT_SAFETY_CATEGORY = "normal"
MINIMUM_APPROVED_CONFIDENCE = 80.0
MAX_OPENING_REPETITIONS = 5
MAX_SENTENCE_REPETITIONS = 3
SIMILARITY_THRESHOLD = 0.92
SIMILARITY_LOOKBACK = 80
MIN_RESPONSE_WORDS = 80
MAX_RESPONSE_WORDS = 140
CORRUPTION_PATTERN = re.compile(r"[{}@ïÌœ]|H¥|�|jkhh|vijkhh|iijkhh|viiijkhh")
FORBIDDEN_TEACHING_PATTERN = re.compile(
    r"\b(the central lesson is|my bow|gandeeva|arjuna|krishna said|sanjaya|o king|o partha|chapter\s+\d+|\d+\.\d+)\b",
    re.IGNORECASE,
)
SCRIPTURAL_FALLBACK_PATTERN = re.compile(
    r"\b(my teachings|follow my teachings|attain salvation|living being cannot perform|perform your prescribed dut(?:y|ies)|for others independently|worship me|devotee|supreme lord)\b",
    re.IGNORECASE,
)
SANSKRIT_SCRIPT_PATTERN = re.compile(r"[\u0900-\u097F]")

SCENARIO_PROBLEMS = {
    "clarity_decision": [
        "I keep circling the same decision and I cannot tell what is actually clear anymore.",
        "My mind keeps swinging between options, and I need a steadier way to choose.",
        "I am overthinking a decision and I want to act from clarity instead of mental noise.",
        "Everything feels tangled right now, and I need help separating truth from confusion.",
        "I know I need to decide, but my thoughts keep blurring what matters most.",
        "I am stuck between hesitation and action, and I want to choose with a clearer mind.",
    ],
    "responsibility_action": [
        "I know what I need to do, but I keep resisting the responsibility in front of me.",
        "I am carrying an important duty, yet I keep wavering when it is time to act.",
        "How do I stay committed to the work that is mine without being crushed by it?",
        "I keep postponing the right action because I am preoccupied with how it will turn out.",
        "Responsibility feels heavy right now, and I want to act without panic or avoidance.",
        "I need to move on something important, but I keep getting lost in consequences.",
    ],
    "expectation_control": [
        "I am too caught up in how things should turn out, and it is disturbing my peace.",
        "My expectations are making me tense, and I do not know how to loosen my grip.",
        "I keep trying to control every outcome, and it is draining the life out of my effort.",
        "I want to do my part well without obsessing over the result.",
        "How do I care deeply about my work without clinging so tightly to what follows?",
        "I feel trapped between sincere effort and fear about how everything will unfold.",
    ],
    "emotional_steadiness": [
        "Strong emotion is clouding my judgment, and I need a steadier way to respond.",
        "Grief and fear are making everything feel heavier than usual, and I want to stay grounded.",
        "My emotions are running ahead of me, and I need help finding steadiness again.",
        "I feel shaken by what is happening, and I do not want emotion to choose for me.",
        "Pain and uncertainty are narrowing my mind, and I want to regain balance.",
        "I am trying to stay upright through this emotional pressure, but I keep losing steadiness.",
    ],
    "trust_letting_go": [
        "I am struggling to trust the process of life without trying to force certainty.",
        "Part of me knows I need to let go, but another part keeps gripping harder.",
        "How do I soften into trust without becoming passive or careless?",
        "I want to surrender what I cannot control, but I do not know how to do that honestly.",
        "My heart wants deeper trust, but my mind keeps demanding guarantees.",
        "I am worn out from holding everything so tightly, and I need help letting go well.",
    ],
    "habits_restraint": [
        "I keep breaking my own good intentions, and I want steadier discipline.",
        "My habits fall apart when life gets difficult, and I need a more reliable inner structure.",
        "I know what helps me, but I do not always have the restraint to follow through.",
        "I want more self-control, especially when emotion or impulse starts taking over.",
        "How do I build discipline without turning it into self-punishment?",
        "I keep slipping into the same unhelpful pattern, and I want a wiser habit to take its place.",
    ],
}

OPENING_STYLES = [
    "This {emotion_word} stretch of life can feel especially tight when {focus_word} is under strain.",
    "There are moments when {emotion_word} fills the whole horizon, yet a steadier response is still possible.",
    "It is understandable that {emotion_word} is loud right now, especially when {focus_word} feels unsettled.",
    "When the heart is carrying {emotion_word}, even simple decisions can feel unusually heavy.",
    "A season shaped by {emotion_word} often makes {focus_word} seem harder than it really is.",
    "Inner pressure grows quickly when {emotion_word} and {focus_word} start pulling in different directions.",
    "Many people reach this kind of crossroads when {emotion_word} clouds their sense of {focus_word}.",
    "A mind touched by {emotion_word} usually needs steadiness before it can see {focus_word} clearly.",
    "This kind of struggle often appears when {emotion_word} tightens around questions of {focus_word}.",
    "When {emotion_word} rises, it can make {focus_word} feel distant even when it is still available.",
    "The weight you describe makes sense because {emotion_word} can narrow the mind and blur {focus_word}.",
    "What feels difficult here is not weakness; it is the strain that appears when {emotion_word} unsettles {focus_word}.",
]

ACKNOWLEDGEMENT_PREFIXES = [
    "What you are facing is human, and it makes sense that {emotion} is coloring this moment.",
    "You are not weak for feeling this pressure; {emotion} can change how {focus} appears.",
    "Anyone carrying this kind of inner strain around {focus} would feel the pull you describe.",
    "This is the kind of moment where the mind becomes louder than the deeper truth you already sense about {focus}.",
    "It is understandable that the situation feels heavier when {emotion} is already active around {focus}.",
    "You are meeting a real inner difficulty around {focus}, not failing some hidden test of calm.",
]

ACKNOWLEDGEMENT_SUFFIXES = [
    "That does not cancel your ability to respond wisely.",
    "The pressure is real, but it does not have to decide your next move.",
    "There is still room here for a steadier choice.",
    "You can honor the feeling without letting it command the whole response.",
    "A calmer direction is still available, even before everything feels resolved.",
]

ACKNOWLEDGEMENT_SENTENCES = [
    f"{prefix} {suffix}"
    for prefix in ACKNOWLEDGEMENT_PREFIXES
    for suffix in ACKNOWLEDGEMENT_SUFFIXES
]

PRINCIPLE_PATTERNS = [
    "A useful reminder here is that {teaching}.",
    "What helps in a moment like this is remembering that {teaching}.",
    "One steady truth to lean on is this: {teaching}.",
    "A calmer way to hold this is to see that {teaching}.",
    "The deeper guidance here is simple: {teaching}.",
]

WISDOM_BRIDGE_PREFIXES = [
    "That matters because it returns your attention to what can actually be practiced around {focus}.",
    "That matters because inner steadiness grows through lived response, not mental performance around {focus}.",
    "That becomes practical when it keeps you close to truth instead of reaction in {focus}.",
    "That becomes useful when it keeps the next step in {focus} from being swallowed by emotional noise.",
    "That guidance helps because it loosens pressure without making you passive about {focus}.",
    "That becomes real when you treat it as something to practice, not just admire in {focus}.",
]

WISDOM_BRIDGE_SUFFIXES = [
    "It gives the mind a more honest place to stand.",
    "It keeps the response grounded in something steadier than impulse.",
    "It turns reflection into something you can live today.",
    "It helps action grow cleaner without becoming cold.",
    "It leaves less room for panic to lead the moment.",
]

WISDOM_BRIDGE_SENTENCES = [
    f"{prefix} {suffix}"
    for prefix in WISDOM_BRIDGE_PREFIXES
    for suffix in WISDOM_BRIDGE_SUFFIXES
]

EXPLANATION_ENDINGS = [
    "That is often where {focus} starts becoming workable again.",
    "This is how pressure stops running ahead of wiser judgment.",
    "That is often the turning point between feeling trapped and acting wisely.",
    "This is how steadiness starts returning in ordinary life.",
    "That is what helps the next response come from truth rather than reaction.",
]

EXPLANATION_PATTERNS = {
    "clarity_decision": [
        f"{prefix} {ending}"
        for prefix in [
            "Clarity usually returns when you stop asking the mind to solve everything at once and start looking for the next honest step.",
            "The mind becomes less tangled when you stop feeding every possible outcome and return to what is true right now.",
            "Inner confusion loses force when you ask what is real, what is assumed, and what action is actually yours.",
            "Clearer decisions appear when you reduce the drama and face the fact that has been sitting in front of you.",
            "Confusion often softens when you stop chasing certainty and start working with what is already honest.",
            "The mind steadies when you separate what is urgent in thought from what is true in action.",
        ]
        for ending in EXPLANATION_ENDINGS
    ],
    "responsibility_action": [
        f"{prefix} {ending}"
        for prefix in [
            "Responsibility becomes lighter when you carry the work itself instead of carrying every imagined consequence with it.",
            "The point is not to become hard; it is to act from responsibility rather than from avoidance, panic, or image.",
            "Right action grows cleaner when you give your energy to the task and not to rehearsing every possible result.",
            "Duty becomes more bearable when you stop arguing with its existence and start meeting it directly.",
            "Action becomes steadier when you stop measuring it by applause and start measuring it by integrity.",
            "A responsible life is shaped less by mood and more by willingness to do what is yours.",
        ]
        for ending in EXPLANATION_ENDINGS
    ],
    "expectation_control": [
        f"{prefix} {ending}"
        for prefix in [
            "Peace grows when effort stays sincere but the mind stops demanding guarantees before it can act.",
            "Attachment tightens suffering because it asks life to obey your preferred outcome before you can stay steady.",
            "You do not become careless by loosening control; you become more available to act wisely.",
            "Expectation becomes exhausting when it confuses caring deeply with controlling completely.",
            "A tighter grip rarely produces peace; it usually produces more inner argument.",
            "Freedom grows when you let effort stay wholehearted while releasing the demand to script the ending.",
        ]
        for ending in EXPLANATION_ENDINGS
    ],
    "emotional_steadiness": [
        f"{prefix} {ending}"
        for prefix in [
            "Strong emotion does not make you incapable, but it can temporarily narrow the field of what you can see clearly.",
            "Steadiness begins when emotion is acknowledged without giving it total authority over your next move.",
            "You do not need to erase feeling; you need enough inner space that feeling is no longer driving the whole response.",
            "Fear becomes less ruling when you take one grounded step before following its story.",
            "Grief becomes more bearable when you stop fighting its presence and start supporting your balance within it.",
            "A shaken mind settles more reliably through grounded action than through forced reassurance.",
        ]
        for ending in EXPLANATION_ENDINGS
    ],
    "trust_letting_go": [
        f"{prefix} {ending}"
        for prefix in [
            "Trust becomes real when you keep showing up honestly without insisting that certainty arrive first.",
            "Letting go does not mean passivity; it means offering sincere effort without gripping the future so tightly.",
            "The heart often settles when it stops trying to control what can only be met with sincerity and patience.",
            "Surrender becomes healthy when it softens demand without weakening responsibility.",
            "Trust grows when you stop treating uncertainty as proof that something has gone wrong.",
            "A quieter kind of faith begins when you release the need to manage every unseen detail.",
        ]
        for ending in EXPLANATION_ENDINGS
    ],
    "habits_restraint": [
        f"{prefix} {ending}"
        for prefix in [
            "Discipline becomes sustainable when it is built through repeated honesty, not through bursts of self-punishment.",
            "Restraint grows when you choose one reliable action often enough that the mind learns to trust steadiness.",
            "Self-control usually strengthens through small repeated victories, not through dramatic vows.",
            "Habits become wiser when you make the better choice easier to repeat and the worse choice harder to indulge.",
            "Distraction loses strength when you interrupt it early instead of bargaining with it for too long.",
            "Inner order is built by removing one source of drift at a time and staying faithful to the clearer pattern.",
        ]
        for ending in EXPLANATION_ENDINGS
    ],
}

ACTION_PATTERNS = {
    "clarity_decision": [
        "Write the options in plain language, circle the one that feels most honest, and complete only the next step today.",
        "Name the decision in one sentence, choose one truthful action, and stop reopening the whole debate until that action is done.",
        "List what is fact and what is fear, then let the clearest fact choose your next move.",
        "Set a short timer, write the next honest step, and act before the mind starts multiplying outcomes again.",
        "Choose the smallest clear action available, complete it, and let that action teach the mind what clarity feels like.",
        "Put the decision on paper, cross out every option you already know is false, and move one step toward what remains.",
    ],
    "responsibility_action": [
        "Complete one responsibility you have been avoiding, and let finishing it matter more than predicting how it will be received.",
        "Choose the clearest duty in front of you, give it one uninterrupted block of attention, and leave the imagined consequences alone.",
        "Write down the task you have delayed, set a time for it today, and keep that appointment without bargaining.",
        "Finish one small piece of the work that is actually yours, and do not mix it with everything that is not yours.",
        "Pick one avoided responsibility, begin it before your mood improves, and let action rebuild trust in yourself.",
        "Ask what part of this burden is truly yours, do that part cleanly, and stop carrying the rest for tonight.",
    ],
    "expectation_control": [
        "Release one expectation you have been gripping, and return your effort to the part you can actually influence today.",
        "Write down the result you keep trying to control, then write the one sincere action that is still yours.",
        "Do the next task wholeheartedly, and refuse one extra round of outcome-driven checking afterward.",
        "Notice where expectation is tightening your body, soften that grip, and return to the work itself.",
        "Choose one place to let go of your preferred ending, and use that space to act more honestly.",
        "Before acting, say out loud what is yours to do and what is not yours to control, then honor that boundary.",
    ],
    "fear": [
        "Take one small safe action before the fear gets to narrate the whole day for you.",
        "Choose one grounded step that feels safe enough to complete, and let action interrupt the fear spiral.",
        "Name the fear plainly, then do one modest thing that proves you are still able to move.",
        "Reduce the situation to one safe next action, complete it, and let that become your evidence of steadiness.",
        "Pause, breathe once, and take the smallest safe step that moves you toward what matters.",
        "Let your next act be simple and safe, because courage often begins as movement before certainty.",
    ],
    "grief": [
        "Complete one gentle grounding act today, such as water, rest, walking, or sitting quietly without rushing yourself.",
        "Choose one soft stabilizing action, and let that be enough support for this part of the day.",
        "When grief rises, return to one caring routine that reminds the body it is still being held.",
        "Do one small act of care that brings you back to the present without demanding that the grief disappear.",
        "Ground yourself through one simple act like stepping outside, drinking water, or writing what hurts without judgment.",
        "Let one gentle action become your anchor today, even if the heart remains heavy.",
    ],
    "emotional_steadiness": [
        "Before speaking or deciding, pause long enough for your body to settle and then choose the most grounded response available.",
        "Name the emotion quietly, slow one breath, and act from the part of you that still wants steadiness.",
        "Reduce the whole struggle to one grounded act, and refuse to let the emotional story grow larger than that act.",
        "Feel your feet, soften your jaw, and make one decision only after the body stops racing.",
        "Choose one response that protects steadiness, even if the feeling itself remains intense.",
        "Let the next action be simple, slow, and deliberate so emotion does not keep taking the lead.",
    ],
    "trust_letting_go": [
        "Practice one act of trust today by naming what is still yours to do and releasing what is not.",
        "Choose one place where you can stop gripping for certainty and instead return to honest presence.",
        "Set aside a few quiet minutes, name what you cannot control, and let your next action come from trust instead of demand.",
        "Offer sincere effort to the work in front of you, then refuse one more round of compulsive prediction.",
        "Practice letting go in one specific area today, even if only for the next hour.",
        "Take one step that expresses trust without abandoning responsibility, and let that be your practice for today.",
    ],
    "habits_restraint": [
        "Remove one distraction that keeps pulling you off course, and protect the clearer pattern for the next hour.",
        "Choose one modest discipline, do it at a fixed time, and count consistency as the win.",
        "Notice the first distraction that usually breaks your focus, interrupt it early, and return to what matters.",
        "Commit to one concrete restraint for the next day, and keep it without drama or self-punishment.",
        "Make the wiser habit easier to start by removing one obstacle before the day gets noisier.",
        "Pick one impulse to delay today, and let that pause train steadiness instead of denial.",
    ],
}

ACTION_FOLLOWUPS = [
    "Let that step train steadiness, not perfection.",
    "Treat that action as practice in truth rather than a test of worth.",
    "Let the value of the step be that it interrupts the old pattern.",
    "Keep the step plain enough that you can actually repeat it.",
    "What matters is calm follow-through, not dramatic intensity.",
]

for key, values in list(ACTION_PATTERNS.items()):
    ACTION_PATTERNS[key] = [f"{value} {followup}" for value in values for followup in ACTION_FOLLOWUPS]

CLOSING_PREFIXES = [
    "That is enough for today, because steadiness around {focus} usually returns through sincere repetition, not force.",
    "Small honest actions matter more than dramatic promises when {focus} feels unsettled.",
    "You do not need to solve your whole life tonight; you only need the next truthful step in {focus}.",
    "If you keep returning to this kind of honesty, pressure around {focus} will lose some of its authority.",
    "Let today end with one sincere act rather than one more inner argument about {focus}.",
]

CLOSING_SUFFIXES = [
    "Let today be about steadiness, not perfection.",
    "A modest true step will serve you better than a dramatic promise.",
    "You are building trust by how you respond now, not by how flawless you feel.",
    "Clarity is usually rebuilt through practice, not through one perfect insight.",
]

CLOSING_PATTERNS = [
    f"{prefix} {suffix}"
    for prefix in CLOSING_PREFIXES
    for suffix in CLOSING_SUFFIXES
]


@dataclass(slots=True)
class GeneratedTrainingExample:
    """In-memory representation of a generated training example."""

    wisdom_entry_id: int
    user_problem: str
    assistant_response: str
    tone: str
    safety_category: str
    source_references: list[str]
    approved_for_finetune: bool


class TrainingDataGenerationService:
    """Build deterministic, high-quality training examples and fine-tuning JSONL output."""

    def is_training_eligible(self, wisdom_entry: WisdomEntry) -> bool:
        """Return whether a wisdom entry is approved for training example generation."""

        return (
            (wisdom_entry.principle_status or "needs_review") == "approved"
            and (wisdom_entry.confidence_score or 0.0) >= MINIMUM_APPROVED_CONFIDENCE
            and bool(self._primary_teaching_text(wisdom_entry))
        )

    def generate_examples_for_wisdom_entries(
        self,
        wisdom_entries: list[WisdomEntry],
    ) -> list[GeneratedTrainingExample]:
        """Generate one high-quality training example per wisdom entry."""

        generated_examples: list[GeneratedTrainingExample] = []
        opening_counts: Counter[str] = Counter()
        sentence_counts: Counter[str] = Counter()
        normalized_responses: list[str] = []

        for example_index, wisdom_entry in enumerate(wisdom_entries):
            generated_examples.extend(
                self._generate_examples_for_wisdom_entry(
                    wisdom_entry=wisdom_entry,
                    example_index=example_index,
                    opening_counts=opening_counts,
                    sentence_counts=sentence_counts,
                    normalized_responses=normalized_responses,
                )
            )

        return generated_examples

    def generate_examples_for_wisdom_entry(
        self,
        wisdom_entry: WisdomEntry,
    ) -> list[GeneratedTrainingExample]:
        """Backwards-compatible single-entry generation wrapper."""

        return self.generate_examples_for_wisdom_entries([wisdom_entry])

    def build_jsonl_lines(self, training_examples: list[TrainingExample]) -> list[str]:
        """Convert training examples into JSONL lines for future fine-tuning."""

        jsonl_lines: list[str] = []
        for example in training_examples:
            payload = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": example.user_problem},
                    {"role": "assistant", "content": example.assistant_response},
                ]
            }
            jsonl_lines.append(json.dumps(payload, ensure_ascii=False))
        return jsonl_lines

    def _generate_examples_for_wisdom_entry(
        self,
        wisdom_entry: WisdomEntry,
        example_index: int,
        opening_counts: Counter[str],
        sentence_counts: Counter[str],
        normalized_responses: list[str],
    ) -> list[GeneratedTrainingExample]:
        """Generate one strong example for a single wisdom entry."""

        if not self.is_training_eligible(wisdom_entry):
            return []

        scenario_type = self._scenario_type(wisdom_entry)
        user_problem = self._build_user_problem(wisdom_entry, scenario_type)
        source_references = self._build_source_references(wisdom_entry)
        assistant_response = self._build_response_with_guards(
            wisdom_entry=wisdom_entry,
            user_problem=user_problem,
            scenario_type=scenario_type,
            example_index=example_index,
            opening_counts=opening_counts,
            sentence_counts=sentence_counts,
            normalized_responses=normalized_responses,
        )

        return [
            GeneratedTrainingExample(
                wisdom_entry_id=wisdom_entry.id,
                user_problem=user_problem,
                assistant_response=assistant_response,
                tone=DEFAULT_TONE,
                safety_category=DEFAULT_SAFETY_CATEGORY,
                source_references=source_references,
                approved_for_finetune=False,
            )
        ]

    def _build_response_with_guards(
        self,
        wisdom_entry: WisdomEntry,
        user_problem: str,
        scenario_type: str,
        example_index: int,
        opening_counts: Counter[str],
        sentence_counts: Counter[str],
        normalized_responses: list[str],
    ) -> str:
        """Build one response while guarding against repeated openings and similar bodies."""

        context = self._build_response_context(
            wisdom_entry=wisdom_entry,
            user_problem=user_problem,
            scenario_type=scenario_type,
            example_index=example_index,
            sentence_counts=sentence_counts,
        )
        base_seed = self._entry_seed(wisdom_entry, scenario_type, example_index) + len(user_problem.split())
        opening_candidates = self._ordered_indices(len(OPENING_STYLES), base_seed)

        best_response: str | None = None
        best_opening_key: str | None = None
        best_score = -1

        for opening_index in opening_candidates:
            opening_sentence = self._build_opening_sentence(context, opening_index)
            opening_key = self._opening_key(opening_sentence)
            opening_penalty = 1 if opening_counts[opening_key] >= MAX_OPENING_REPETITIONS else 0

            response = self._compose_response(context, opening_sentence)
            normalized_response = self._normalize_response(response)
            if self._is_too_similar(normalized_response, normalized_responses):
                if best_response is None:
                    best_response = response
                    best_opening_key = opening_key
                    best_score = 10 - opening_penalty
                continue

            score = 10 - opening_penalty
            if score > best_score:
                best_score = score
                best_response = response
                best_opening_key = opening_key
            if opening_penalty == 0:
                opening_counts[opening_key] += 1
                normalized_responses.append(normalized_response)
                return response

        if best_response is None or best_opening_key is None:
            fallback_opening = self._build_opening_sentence(context, opening_candidates[0])
            best_response = self._compose_response(context, fallback_opening)
            best_opening_key = self._opening_key(fallback_opening)

        opening_counts[best_opening_key] += 1
        normalized_responses.append(self._normalize_response(best_response))
        return best_response

    def _build_response_context(
        self,
        wisdom_entry: WisdomEntry,
        user_problem: str,
        scenario_type: str,
        example_index: int,
        sentence_counts: Counter[str],
    ) -> dict[str, str]:
        """Build reusable response fragments for one example."""

        emotional_tags = list(wisdom_entry.emotional_tags or [])
        philosophical_tags = list(wisdom_entry.philosophical_tags or [])

        emotion = emotional_tags[0] if emotional_tags else self._default_emotion_for_scenario(scenario_type)
        focus = self._focus_word(wisdom_entry, philosophical_tags, scenario_type)
        teaching = self._primary_teaching_text(wisdom_entry) or "steady action matters more than restless reaction."

        variant_seed = self._entry_seed(wisdom_entry, scenario_type, example_index)
        action_family = self._action_family(scenario_type, emotional_tags)
        return {
            "emotion": emotion,
            "emotion_word": self._emotion_word(emotion),
            "focus_word": focus,
            "ack": self._build_acknowledgement(emotion, focus, variant_seed, sentence_counts),
            "principle": self._build_principle_sentence(teaching, focus, variant_seed, sentence_counts),
            "explanation": self._build_explanation_sentence(scenario_type, focus, variant_seed, sentence_counts),
            "action": self._build_action_sentence(action_family, variant_seed, sentence_counts),
            "closing": self._build_closing_sentence(focus, variant_seed, sentence_counts),
        }

    def _compose_response(
        self,
        context: dict[str, str],
        opening_sentence: str,
    ) -> str:
        """Compose and normalize one response."""

        parts = [
            opening_sentence,
            context["ack"],
            context["principle"],
            context["explanation"],
            context["action"],
            context["closing"],
        ]
        response = " ".join(self._dedupe_adjacent(parts))
        response = self._clean_text(response) or ""
        return self._enforce_length_bounds(response, context)

    def _build_user_problem(self, wisdom_entry: WisdomEntry, scenario_type: str) -> str:
        """Build one deterministic user scenario per wisdom entry."""

        problems = SCENARIO_PROBLEMS[scenario_type]
        use_case = (wisdom_entry.use_cases or [None])[0]
        if use_case:
            normalized_use_case = use_case.rstrip(".")
            custom_problem = f"I am trying to work on {normalized_use_case}, but I keep slipping into the same inner struggle."
            candidate_problems = problems + [custom_problem]
        else:
            candidate_problems = problems
        return self._select_variant(candidate_problems, wisdom_entry.id * 5 + 1)

    def _scenario_type(self, wisdom_entry: WisdomEntry) -> str:
        """Select a scenario type from emotional and philosophical tags."""

        emotional_tags = set(wisdom_entry.emotional_tags or [])
        philosophical_tags = set(wisdom_entry.philosophical_tags or [])

        if "confusion" in emotional_tags:
            return "clarity_decision"
        if {"duty"} & emotional_tags or {"dharma", "karma"} & philosophical_tags:
            return "responsibility_action"
        if {"attachment", "desire"} & emotional_tags:
            return "expectation_control"
        if {"grief", "fear", "anger"} & emotional_tags:
            return "emotional_steadiness"
        if {"devotion", "surrender"} & emotional_tags or {"bhakti"} & philosophical_tags:
            return "trust_letting_go"
        if {"discipline", "self-control"} & emotional_tags or {"yoga"} & philosophical_tags:
            return "habits_restraint"
        return "clarity_decision"

    def _build_opening_sentence(self, context: dict[str, str], opening_index: int) -> str:
        """Return one varied opening sentence."""

        return OPENING_STYLES[opening_index].format(
            emotion_word=context["emotion_word"],
            focus_word=context["focus_word"],
        )

    def _build_source_references(self, wisdom_entry: WisdomEntry) -> list[str]:
        """Build a simple source reference list for a training example."""

        references: list[str] = []
        if wisdom_entry.book_title:
            references.append(wisdom_entry.book_title)
        if wisdom_entry.chapter:
            references.append(wisdom_entry.chapter)
        if wisdom_entry.verse_number:
            references.append(wisdom_entry.verse_number)
        return references

    def _default_emotion_for_scenario(self, scenario_type: str) -> str:
        """Return a fallback emotion word for a scenario."""

        defaults = {
            "clarity_decision": "confusion",
            "responsibility_action": "responsibility",
            "expectation_control": "attachment",
            "emotional_steadiness": "grief",
            "trust_letting_go": "surrender",
            "habits_restraint": "discipline",
        }
        return defaults.get(scenario_type, "strain")

    def _emotion_word(self, emotion: str) -> str:
        """Return a natural phrase for the leading emotional tag."""

        mapping = {
            "anxiety": "anxious pressure",
            "grief": "grief",
            "fear": "fear",
            "duty": "responsibility",
            "attachment": "attachment",
            "anger": "anger",
            "confusion": "confusion",
            "discipline": "inner inconsistency",
            "devotion": "spiritual longing",
            "self-control": "inner unrest",
            "ego": "self-importance",
            "desire": "restless wanting",
            "surrender": "the struggle to let go",
            "purpose": "uncertainty about direction",
            "responsibility": "responsibility",
            "strain": "inner strain",
        }
        return mapping.get(emotion, "inner strain")

    def _focus_word(
        self,
        wisdom_entry: WisdomEntry,
        philosophical_tags: list[str],
        scenario_type: str,
    ) -> str:
        """Return a short focus phrase for openings and explanations."""

        principle_text = (
            self._primary_teaching_text(wisdom_entry)
            or self._clean_text(wisdom_entry.extracted_principle)
            or ""
        ).lower()
        if scenario_type == "responsibility_action":
            return "right action" if "karma" in philosophical_tags else "duty"
        if scenario_type == "expectation_control":
            return "clarity"
        if scenario_type == "emotional_steadiness":
            return "steadiness"
        if scenario_type == "trust_letting_go":
            return "trust"
        if scenario_type == "habits_restraint":
            return "discipline"
        if "jnana" in philosophical_tags or "self-realization" in philosophical_tags:
            return "clarity"
        if "atman" in philosophical_tags:
            return "inner steadiness"
        if "duty" in principle_text:
            return "duty"
        return "clarity"

    def _opening_key(self, opening_sentence: str) -> str:
        """Return the normalized opening phrase used by the dataset audit."""

        return " ".join(opening_sentence.strip().split()[:12]).rstrip(".,;:!?").lower()

    def _ordered_indices(self, length: int, seed: int) -> list[int]:
        """Return a deterministic rotated list of indices."""

        start = seed % length
        return [(start + offset) % length for offset in range(length)]

    def _select_variant(self, values: list[str], seed: int) -> str:
        """Select one deterministic variant from a list."""

        return values[seed % len(values)]

    def _build_acknowledgement(
        self,
        emotion: str,
        focus: str,
        seed: int,
        sentence_counts: Counter[str],
    ) -> str:
        """Build one acknowledgement sentence from a large corpus-aware bank."""

        return self._select_sentence_from_bank(
            bank=ACKNOWLEDGEMENT_SENTENCES,
            seed=seed,
            sentence_counts=sentence_counts,
            emotion=emotion,
            focus=focus,
        )

    def _build_principle_sentence(
        self,
        teaching: str,
        focus: str,
        seed: int,
        sentence_counts: Counter[str],
    ) -> str:
        """Build a principle plus bridge sentence pair."""

        primary = self._select_variant(PRINCIPLE_PATTERNS, seed + 3).format(
            teaching=teaching.rstrip(".").lower()
        )
        bridge = self._select_sentence_from_bank(
            bank=WISDOM_BRIDGE_SENTENCES,
            seed=seed * 5 + 2,
            sentence_counts=sentence_counts,
            focus=focus,
        )
        return f"{primary} {bridge}"

    def _build_explanation_sentence(
        self,
        scenario_type: str,
        focus: str,
        seed: int,
        sentence_counts: Counter[str],
    ) -> str:
        """Build one explanation sentence from a large scenario-specific bank."""

        return self._select_sentence_from_bank(
            bank=EXPLANATION_PATTERNS[scenario_type],
            seed=seed + 7,
            sentence_counts=sentence_counts,
            focus=focus,
        )

    def _build_action_sentence(
        self,
        action_family: str,
        seed: int,
        sentence_counts: Counter[str],
    ) -> str:
        """Build one action sentence from a tag-specific bank."""

        return self._select_sentence_from_bank(
            bank=ACTION_PATTERNS[action_family],
            seed=seed + 11,
            sentence_counts=sentence_counts,
        )

    def _build_closing_sentence(
        self,
        focus: str,
        seed: int,
        sentence_counts: Counter[str],
    ) -> str:
        """Build one closing sentence from a corpus-aware bank."""

        return self._select_sentence_from_bank(
            bank=CLOSING_PATTERNS,
            seed=seed + 13,
            sentence_counts=sentence_counts,
            focus=focus,
        )

    def _select_sentence_from_bank(
        self,
        bank: list[str],
        seed: int,
        sentence_counts: Counter[str],
        **format_kwargs: str,
    ) -> str:
        """Select a deterministic sentence while capping corpus reuse."""

        ordered_indices = self._ordered_indices(len(bank), seed)
        fallback_sentence: str | None = None

        for index in ordered_indices:
            sentence = self._single_sentence(bank[index].format(**format_kwargs))
            if fallback_sentence is None:
                fallback_sentence = sentence
            if sentence_counts[sentence] < MAX_SENTENCE_REPETITIONS:
                sentence_counts[sentence] += 1
                return sentence

        assert fallback_sentence is not None
        sentence_counts[fallback_sentence] += 1
        return fallback_sentence

    def _single_sentence(self, text: str) -> str:
        """Collapse a templated bank entry into one sentence for audit-friendliness."""

        parts = [part.strip(" .") for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip(" .")]
        if not parts:
            return text.strip()
        if len(parts) == 1:
            return parts[0].rstrip(".") + "."
        return "; ".join(parts).rstrip(".") + "."

    def _entry_seed(self, wisdom_entry: WisdomEntry, scenario_type: str, example_index: int) -> int:
        """Build a deterministic seed from stable wisdom-entry fields."""

        tags = sorted((wisdom_entry.emotional_tags or []) + (wisdom_entry.philosophical_tags or []))
        tag_value = sum(ord(char) for char in "|".join(tags))
        return wisdom_entry.id * 17 + tag_value + len(scenario_type) * 13 + example_index * 29

    def _action_family(self, scenario_type: str, emotional_tags: list[str]) -> str:
        """Select the most specific action family for the entry."""

        tag_set = set(emotional_tags)
        if scenario_type == "emotional_steadiness":
            if "fear" in tag_set:
                return "fear"
            if "grief" in tag_set:
                return "grief"
            return "emotional_steadiness"
        if scenario_type == "trust_letting_go":
            return "trust_letting_go"
        return scenario_type

    def _normalize_response(self, response: str) -> str:
        """Return normalized response text for similarity checks."""

        normalized = response.lower()
        normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _is_too_similar(self, normalized_response: str, existing_responses: list[str]) -> bool:
        """Return True when a candidate response is too similar to an existing one."""

        for existing_response in existing_responses[-SIMILARITY_LOOKBACK:]:
            if abs(len(normalized_response) - len(existing_response)) > 140:
                continue
            if SequenceMatcher(None, normalized_response, existing_response).ratio() >= SIMILARITY_THRESHOLD:
                return True
        return False

    def _enforce_length_bounds(self, response: str, context: dict[str, str]) -> str:
        """Ensure a response stays within the target word-count range."""

        words = response.split()
        if len(words) < MIN_RESPONSE_WORDS:
            extra_sentence = (
                "Stay close to one concrete step, because lasting calm usually returns after honest action rather than before it."
            )
            response = f"{response} {extra_sentence}"
            words = response.split()
        if len(words) > MAX_RESPONSE_WORDS:
            response = self._trim_to_sentence_limit(response, MAX_RESPONSE_WORDS)
        return response

    def _trim_to_sentence_limit(self, response: str, max_words: int) -> str:
        """Trim a response at sentence boundaries when possible."""

        kept_sentences: list[str] = []
        running_words = 0
        sentences = re.split(r"(?<=[.!?])\s+", response)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            sentence_words = len(sentence.split())
            if kept_sentences and running_words + sentence_words > max_words:
                break
            if not kept_sentences and sentence_words > max_words:
                trimmed_words = sentence.split()[:max_words]
                return " ".join(trimmed_words).rstrip(",;:") + "."
            kept_sentences.append(sentence)
            running_words += sentence_words

        if kept_sentences:
            return " ".join(kept_sentences).strip()

        trimmed_words = response.split()[:max_words]
        return " ".join(trimmed_words).rstrip(",;:") + "."

    def _dedupe_adjacent(self, parts: list[str]) -> list[str]:
        """Drop consecutive duplicate sentence fragments."""

        deduped: list[str] = []
        for part in parts:
            cleaned_part = self._clean_text(part)
            if not cleaned_part:
                continue
            if deduped and deduped[-1] == cleaned_part:
                continue
            deduped.append(cleaned_part)
        return deduped

    def _primary_teaching_text(self, wisdom_entry: WisdomEntry) -> str | None:
        """Return the preferred clean teaching source for response generation."""

        distilled_wisdom = self._sanitize_teaching_text(wisdom_entry.distilled_wisdom)
        if distilled_wisdom:
            return distilled_wisdom

        if (wisdom_entry.principle_status or "needs_review") != "approved":
            return None

        return self._sanitize_teaching_text(wisdom_entry.extracted_principle)

    def _sanitize_teaching_text(self, text: str | None) -> str | None:
        """Remove verse-specific or corrupted teaching text before response generation."""

        cleaned_text = self._clean_text(text)
        if not cleaned_text:
            return None
        if FORBIDDEN_TEACHING_PATTERN.search(cleaned_text):
            return None
        if SCRIPTURAL_FALLBACK_PATTERN.search(cleaned_text):
            return None
        if SANSKRIT_SCRIPT_PATTERN.search(cleaned_text):
            return None
        if len(cleaned_text.split()) < 5:
            return None
        cleaned_text = self._remove_forbidden_phrases(cleaned_text)
        if FORBIDDEN_TEACHING_PATTERN.search(cleaned_text):
            return None
        if SCRIPTURAL_FALLBACK_PATTERN.search(cleaned_text):
            return None
        return cleaned_text.rstrip(".") + "."

    def _remove_forbidden_phrases(self, text: str) -> str:
        """Strip visibly repetitive phrases that should not appear in responses."""

        cleaned_text = text
        for phrase in (
            "I hear",
            "Begin by slowing the mind",
            "A helpful reflection",
            "Let this teaching",
            "The central lesson is",
        ):
            cleaned_text = cleaned_text.replace(phrase, "")
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip(" ,.")
        return cleaned_text or text

    def _clean_text(self, text: str | None) -> str | None:
        """Normalize whitespace and drop obviously corrupted content."""

        if not text:
            return None
        cleaned_text = " ".join(text.split()).strip()
        if not cleaned_text:
            return None
        if CORRUPTION_PATTERN.search(cleaned_text):
            return None
        return cleaned_text

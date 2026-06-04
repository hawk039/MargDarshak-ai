"""Generate Upanishad-specific training examples from approved distilled wisdom."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from app.models.training_example import TrainingExample
from app.models.wisdom_entry import WisdomEntry


DEFAULT_TONE = "calm_philosophical"
DEFAULT_SAFETY_CATEGORY = "normal"
MAX_OPENING_REPETITIONS = 2
FORBIDDEN_VISIBLE_PATTERN = re.compile(
    r"\b(kena|katha|mundaka|upanishad|chapter|passage|verse|brahman said|these gods|taking hold of the bow)\b",
    re.IGNORECASE,
)

SCENARIO_VARIANTS = {
    "identity_confusion": [
        "I feel disconnected from myself and I do not know what is actually true in me anymore.",
        "My thoughts change constantly, and I feel like I have lost touch with who I really am.",
        "I feel scattered inside, as if I am living from reactions instead of something deeper.",
        "I do not feel grounded in myself, and it is making everything seem unstable.",
        "I keep identifying with whatever I feel in the moment, and it is exhausting.",
        "I want a steadier sense of self because my mind keeps pulling me in different directions.",
        "I feel like my mind keeps changing the story of who I am from one hour to the next.",
        "I keep losing myself inside whatever thought or emotion is strongest in the moment.",
        "I want to feel inwardly steady, but my sense of self keeps shifting with my mood.",
        "I cannot tell what is deeply true in me because my mind keeps crowding everything.",
        "I feel as if I am living from surface reactions instead of something more grounded.",
        "My inner life feels fragmented, and I want to return to something more stable and true.",
        "I keep mistaking passing thoughts for deeper truth, and it is leaving me confused.",
        "I want to feel rooted in who I am, but my mind keeps scattering that feeling.",
        "I feel split between what I know deeply and what my mind keeps telling me.",
        "Even small emotional shifts make me feel like I have lost my center.",
        "I want to live from deeper clarity, but I keep getting swept into surface reactions.",
        "My identity feels unstable because I keep believing every passing thought too quickly.",
    ],
    "fear_change": [
        "I am afraid of change and loss, and it feels like everything important could disappear.",
        "Part of me knows change is natural, but I still panic when life shifts unexpectedly.",
        "I feel scared that losing something important will undo me completely.",
        "Every big change makes me feel as if I am losing myself.",
        "I want to face uncertainty better, but change still makes me feel unsafe.",
        "I feel overwhelmed by the fear that change will take away what matters most.",
        "When life changes suddenly, I feel as if my whole foundation is threatened.",
        "I know change is unavoidable, but I still react as if it will destroy something essential in me.",
        "Loss feels so threatening right now that I cannot think clearly about what comes next.",
        "I want to meet change with more courage, but fear keeps making it feel catastrophic.",
        "I feel as though uncertainty can take away more from me than I could survive.",
        "Change keeps stirring up fear that I will lose my inner footing entirely.",
    ],
    "desire_attachment": [
        "I know what is right, but I keep choosing comfort instead of the harder truthful path.",
        "Part of me wants what is good, but I still keep reaching for what feels easiest.",
        "I can see that comfort is pulling me off course, but I keep giving in to it.",
        "I know I am attached to what feels pleasant, even when it weakens my better judgment.",
        "I want to choose wisely, but immediate comfort keeps deciding for me.",
        "I keep telling myself I value truth, but comfort keeps winning in practice.",
    ],
    "restless_mind": [
        "My mind is scattered and I cannot settle into anything with steadiness.",
        "I keep trying to focus, but my attention runs everywhere and I feel worn out.",
        "My thoughts are noisy and restless, and I do not know how to come back to center.",
        "I cannot hold attention for long because my mind keeps drifting away.",
        "I feel mentally restless all day, and it is making clarity harder to reach.",
        "Even when I want calm, my mind keeps wandering and pulling me away from what matters.",
        "My attention feels fragmented, and I do not know how to gather it back together.",
        "I start with good intention, but my mind keeps slipping away before I stay with anything.",
        "Restlessness is draining my energy because my attention never feels settled.",
        "I want a calmer mind, but my attention keeps scattering before I can stabilize it.",
        "Even simple tasks feel hard because my mind keeps jumping to something else.",
        "I feel mentally overactive, and it is becoming harder to return to what matters.",
        "My mind keeps drifting into noise, and I need a steadier way to come back.",
        "I can feel that my attention is weak right now, and it is affecting everything I do.",
        "My thoughts keep running ahead of me, and I want to become steadier inside.",
        "I am tired of being mentally pulled in every direction all day long.",
        "My inner restlessness makes it hard to stay present with even one clear task.",
        "I want to focus more honestly, but my mind keeps breaking its own attention.",
    ],
    "humility_learning": [
        "I keep arguing with guidance instead of really learning from it.",
        "Whenever someone corrects me, I become defensive instead of teachable.",
        "I want to learn more honestly, but pride keeps making me resist guidance.",
        "I notice that I defend my opinions even when part of me knows I should listen.",
        "I keep turning learning into debate, and I think it is blocking real growth.",
        "I want to receive guidance well, but my ego keeps interrupting the process.",
    ],
    "surface_life": [
        "I feel lost in surface-level life and disconnected from anything deeper.",
        "I keep moving through life mechanically, and I do not feel connected to what is real.",
        "Everything feels busy on the surface, but inwardly I feel hollow and ungrounded.",
        "I can manage daily life, but I still feel disconnected from deeper meaning.",
        "I feel trapped in routines and appearances, and I want a deeper way of living.",
        "My life looks functional from outside, but inwardly I feel disconnected and shallow.",
    ],
    "detachment": [
        "I am holding too tightly to something that may not last, and it is making me anxious.",
        "I know I cannot control everything, but I still cling tightly to what I fear losing.",
        "Attachment is making me restless, and I do not know how to loosen my grip.",
        "I keep depending on something temporary for my sense of stability.",
        "I want peace, but I am still gripping too hard to what could change at any time.",
        "I can feel that attachment is exhausting me, but letting go still feels frightening.",
    ],
    "purpose": [
        "I feel like life lacks deeper direction, even though I am doing all the usual things.",
        "I am functioning, but I still feel unsure about what deeper direction my life should have.",
        "Something in me wants a truer path, but I cannot hear it clearly right now.",
        "I feel pulled by noise and routine, and I want a clearer sense of what matters.",
        "I do not just want activity; I want direction that feels deeply honest.",
        "Life feels busy, but I still feel disconnected from deeper purpose.",
        "Outwardly life continues, but inwardly I still do not feel aligned with a deeper direction.",
        "I want to live with more meaning, but I cannot hear what deeper truth is asking of me.",
        "Part of me feels there must be a truer direction, but noise keeps drowning it out.",
        "I am tired of moving without deeper orientation, even when everything looks normal outside.",
        "I do not only want progress; I want a path that feels inwardly true.",
        "My life feels active but not deeply directed, and that emptiness is growing louder.",
    ],
}

OPENINGS = [
    "This kind of inner struggle can make even simple choices feel heavier than they are.",
    "What you are describing is a real human strain, not a personal failure.",
    "There is nothing strange about feeling unsettled when the mind and heart are pulling in different directions.",
    "Many people reach this kind of threshold when inner pressure becomes louder than inner clarity.",
    "It makes sense that this feels difficult, especially when your mind is carrying so much at once.",
    "Moments like this can quietly drain confidence, even when part of you already knows what matters.",
    "When inner pressure builds, it can distort what is actually clear and make the next step feel farther away.",
    "This is the sort of moment where gentleness and honesty matter more than forcing certainty.",
    "Inner conflict often feels strongest just before a clearer way of seeing becomes available.",
    "It is understandable that you feel pulled around when deeper steadiness has been hard to access.",
    "A lot of unnecessary suffering begins when the mind loses contact with what is quietly true.",
    "When life feels noisy inside, even sincere effort can start to feel confused or fragmented.",
    "Some struggles feel especially draining because they disturb both clarity and self-trust at the same time.",
    "When the inner life becomes crowded, even good intentions can lose their direction.",
    "A difficult inner season often makes ordinary choices feel heavier than they need to be.",
    "What feels painful here is not only the situation, but the way it is pulling at your center.",
    "There are times when the mind becomes so unsettled that even truth starts to feel distant.",
    "This kind of pressure often makes the next wise step seem harder to recognize than it really is.",
    "It is human to feel disoriented when deeper steadiness is being challenged from several sides.",
    "When the mind is tired and reactive, even simple honesty can feel unexpectedly demanding.",
    "This sounds like one of those moments where inner steadiness matters more than mental speed.",
    "There are seasons when the deepest difficulty is not outer action, but inner fragmentation.",
    "Sometimes the hardest part is not the situation itself, but the way it unsettles your inner ground.",
    "When deeper clarity is buried under pressure, the next honest step can start to feel unusually far away.",
    "A strained inner life can make everything feel more urgent and less clear than it really is.",
    "Moments of inward conflict often become easier once the mind is no longer trying to solve everything at once.",
    "This kind of struggle usually asks for steadiness first and answers second.",
]

APPLICATION_PATTERNS = [
    "What helps here is to remember that {teaching}",
    "A steadier way to hold this is to see that {teaching}",
    "The deeper guidance in this moment is that {teaching}",
    "One useful truth to lean on here is that {teaching}",
    "A calmer response becomes possible when you remember that {teaching}",
    "This starts to soften when you work from the understanding that {teaching}",
]

ACTION_PATTERNS = {
    "identity_confusion": [
        "Today, write down one thought that keeps repeating, then answer it with one deeper truth you do not want to forget.",
        "Take ten quiet minutes, name what you are feeling, and separate that feeling from who you are.",
        "When the mind becomes noisy today, pause and ask what is actually true beneath the reaction.",
        "Choose one moment today to stop following the mental story and return to one honest grounding statement.",
    ],
    "fear_change": [
        "Choose one small change you have been resisting, and meet it with one calm deliberate action today.",
        "Write down what you fear losing, then name one part of you that remains intact even if circumstances change.",
        "Take one safe action today that you have delayed because fear kept asking for certainty first.",
        "When fear rises, breathe slowly and name one truth that still holds even in the middle of change.",
    ],
    "desire_attachment": [
        "Notice one place today where comfort is steering you, and choose the more honest action instead.",
        "Before your next choice, ask whether you are following truth or short-term relief, then act from the clearer answer.",
        "Pick one small place where you usually choose ease over honesty, and reverse that pattern today.",
        "Write down one comfort you keep obeying, then take one step that aligns better with what you truly value.",
    ],
    "restless_mind": [
        "Set a short timer, choose one task, and gently return to it each time the mind wanders.",
        "For the next ten minutes, do one thing slowly and keep bringing attention back without irritation.",
        "Choose one moment today to stop multitasking and let your attention rest in one clear action.",
        "When your mind scatters, pause, exhale slowly, and return to the one thing that matters right now.",
    ],
    "humility_learning": [
        "The next time guidance irritates you, pause and ask what it might be showing you before you answer.",
        "Choose one piece of feedback today and sit with it quietly before deciding whether to defend yourself.",
        "Practice listening to one person today without preparing your counterargument while they speak.",
        "Write down one place where pride may be blocking learning, and respond with one act of teachability.",
    ],
    "surface_life": [
        "Take ten quiet minutes today away from noise and ask what part of your life still feels deeply honest.",
        "Pause once today before rushing ahead and name what matters beneath appearances and routine.",
        "Choose one activity you usually do mechanically and do it with full attention and inward honesty.",
        "Spend a few minutes today in silence and ask what feels true when you stop performing for the surface.",
    ],
    "detachment": [
        "Name one thing you are gripping tightly, and practice releasing one small part of that grip today.",
        "Ask yourself what you are expecting this temporary thing to guarantee, then loosen that expectation by one degree.",
        "When anxiety rises around loss, return your attention to one thing you can do honestly right now.",
        "Choose one small act today that shows care without trying to control the whole outcome.",
    ],
    "purpose": [
        "Take a few quiet minutes today and write one direction that feels honest even if it is still incomplete.",
        "Step back from noise for ten minutes and ask what matters when fear and distraction are not answering for you.",
        "Choose one action today that reflects your deeper values, even if the larger path is still unfolding.",
        "Write down what feels empty and what feels quietly true, then move one step toward the truer side.",
    ],
}

CLOSINGS = [
    "You do not need perfect certainty to begin; you only need enough honesty to take the next right step.",
    "Small sincere actions often restore clarity faster than long arguments with the mind.",
    "Let the next step be simple, honest, and repeatable rather than dramatic.",
    "Steadiness usually returns through practice, not through one perfect breakthrough.",
    "The important thing is not to force yourself harshly, but to return gently and truthfully.",
    "Clarity deepens when you practice it instead of waiting to feel fully resolved first.",
]


@dataclass(slots=True)
class UpanishadTrainingGenerationResult:
    """Container for generated Upanishad training examples and skipped counts."""

    generated_examples: list[TrainingExample]
    skipped_count: int


class UpanishadTrainingExampleGenerationService:
    """Generate calm philosophical training examples from Upanishad distilled wisdom."""

    def __init__(self) -> None:
        self._opening_counts: Counter[str] = Counter()
        self._response_fingerprints: set[str] = set()
        self._user_problem_counts: Counter[str] = Counter()

    def is_eligible(self, wisdom_entry: WisdomEntry) -> bool:
        """Return True when a wisdom entry is eligible for Upanishad training generation."""

        return bool(
            wisdom_entry.principle_status == "approved"
            and (wisdom_entry.principle_quality_score or 0.0) >= 80.0
            and wisdom_entry.distilled_wisdom
        )

    def generate_examples(self, wisdom_entries: list[WisdomEntry]) -> UpanishadTrainingGenerationResult:
        """Generate one training example per approved Upanishad wisdom entry."""

        generated_examples: list[TrainingExample] = []
        skipped_count = 0
        for wisdom_entry in wisdom_entries:
            example = self._generate_example(wisdom_entry)
            if example is None:
                skipped_count += 1
                continue
            generated_examples.append(example)
        return UpanishadTrainingGenerationResult(
            generated_examples=generated_examples,
            skipped_count=skipped_count,
        )

    def _generate_example(self, wisdom_entry: WisdomEntry) -> TrainingExample | None:
        """Generate a single Upanishad training example."""

        scenario = self._scenario_type(wisdom_entry)
        user_problem = self._select_user_problem(wisdom_entry, scenario)
        opening = self._select_opening(wisdom_entry, scenario)
        if opening is None:
            return None
        application = self._select_application(wisdom_entry, scenario)
        action_step = self._select_action_step(wisdom_entry, scenario)
        closing = self._select_closing(wisdom_entry, scenario)

        assistant_response = " ".join([opening, application, action_step, closing]).strip()
        if FORBIDDEN_VISIBLE_PATTERN.search(assistant_response):
            return None

        fingerprint = self._response_fingerprint(assistant_response)
        if fingerprint in self._response_fingerprints:
            return None

        self._opening_counts[self._opening_key(opening)] += 1
        self._response_fingerprints.add(fingerprint)
        self._user_problem_counts[user_problem] += 1

        return TrainingExample(
            wisdom_entry_id=wisdom_entry.id,
            user_problem=user_problem,
            assistant_response=assistant_response,
            tone=DEFAULT_TONE,
            safety_category=DEFAULT_SAFETY_CATEGORY,
            source_references=[
                {
                    "book": wisdom_entry.book_title,
                    "chapter": wisdom_entry.chapter,
                    "section": wisdom_entry.section,
                    "passage": wisdom_entry.verse_number,
                }
            ],
            approved_for_finetune=False,
            dataset_status="needs_review",
            dataset_audit_issues=[],
        )

    def _scenario_type(self, wisdom_entry: WisdomEntry) -> str:
        """Choose the scenario mapping from Upanishad tags."""

        emotional = {str(tag).strip().lower() for tag in (wisdom_entry.emotional_tags or [])}
        philosophical = {str(tag).strip().lower() for tag in (wisdom_entry.philosophical_tags or [])}

        if {"confusion", "ego"} & emotional or {"self_knowledge"} & philosophical:
            return "identity_confusion"
        if {"fear"} & emotional or {"death", "immortality"} & philosophical:
            return "fear_change"
        if {"desire", "attachment"} & emotional:
            return "desire_attachment"
        if {"restlessness", "discipline", "self-control"} & emotional or {"meditation"} & philosophical:
            return "restless_mind"
        if {"teacher_student"} & philosophical:
            return "humility_learning"
        if {"consciousness", "reality", "non_duality"} & philosophical:
            return "surface_life"
        if {"renunciation", "detachment", "liberation"} & philosophical:
            return "detachment"
        return "purpose"

    def _select_user_problem(self, wisdom_entry: WisdomEntry, scenario: str) -> str:
        """Select a deterministic but corpus-aware user problem."""

        variants = SCENARIO_VARIANTS[scenario]
        seed = self._seed(wisdom_entry, scenario, "problem")
        ordered = self._rotate(variants, seed)
        for variant in ordered:
            if self._user_problem_counts[variant] == 0:
                return variant
        return ordered[0]

    def _select_opening(self, wisdom_entry: WisdomEntry, scenario: str) -> str | None:
        """Select an opening without exceeding the corpus repetition cap."""

        seed = self._seed(wisdom_entry, scenario, "opening")
        ordered = self._rotate(OPENINGS, seed)
        for opening in ordered:
            key = self._opening_key(opening)
            if self._opening_counts[key] < MAX_OPENING_REPETITIONS:
                return opening
        return None

    def _select_application(self, wisdom_entry: WisdomEntry, scenario: str) -> str:
        """Apply distilled wisdom naturally to the user scenario."""

        teaching = (wisdom_entry.distilled_wisdom or "").rstrip(".")
        pattern = self._rotate(APPLICATION_PATTERNS, self._seed(wisdom_entry, scenario, "application"))[0]
        application = pattern.format(teaching=teaching.lower())
        return (
            f"{application}. "
            f"In a moment like this, that matters because it helps you respond from deeper steadiness instead of reacting from habit or pressure."
        )

    def _select_action_step(self, wisdom_entry: WisdomEntry, scenario: str) -> str:
        """Pick a scenario-specific practical action."""

        variants = ACTION_PATTERNS[scenario]
        return self._rotate(variants, self._seed(wisdom_entry, scenario, "action"))[0]

    def _select_closing(self, wisdom_entry: WisdomEntry, scenario: str) -> str:
        """Pick a closing sentence."""

        return self._rotate(CLOSINGS, self._seed(wisdom_entry, scenario, "closing"))[0]

    def _response_fingerprint(self, response: str) -> str:
        """Normalize a response for duplicate detection."""

        normalized = re.sub(r"[^a-z0-9\s]", "", response.lower())
        words = normalized.split()
        return " ".join(words[:45])

    def _opening_key(self, opening: str) -> str:
        """Normalize an opening for repetition tracking."""

        return opening.lower().strip()

    def _rotate(self, values: list[str], seed: int) -> list[str]:
        """Return a deterministic rotation of values."""

        if not values:
            return []
        offset = seed % len(values)
        return values[offset:] + values[:offset]

    def _seed(self, wisdom_entry: WisdomEntry, scenario: str, suffix: str) -> int:
        """Build a stable integer seed from wisdom metadata."""

        payload = "|".join(
            [
                str(wisdom_entry.id),
                wisdom_entry.book_title or "",
                wisdom_entry.chapter or "",
                wisdom_entry.section or "",
                scenario,
                suffix,
                ",".join(str(tag) for tag in (wisdom_entry.emotional_tags or [])),
                ",".join(str(tag) for tag in (wisdom_entry.philosophical_tags or [])),
            ]
        )
        return sum((index + 1) * ord(char) for index, char in enumerate(payload))

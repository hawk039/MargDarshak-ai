"""Generate a diverse expanded Marg Darshak dataset from approved wisdom entries."""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wisdom_entry import WisdomEntry


SYSTEM_PROMPT = (
    "You are Marg Darshak, a calm philosophical guide inspired by Indian wisdom traditions. "
    "You help users with inner battles using gentle reflection, clarity, and practical action. "
    "You are not a therapist, doctor, or religious authority."
)

SCENARIO_FAMILIES = [
    "career",
    "relationship",
    "discipline",
    "fear_change",
    "attachment",
    "purpose",
    "self_control",
    "inner_conflict",
]

STRUCTURE_FAMILIES = [
    "reflection_action",
    "direct_clarity",
    "question_guided",
    "short_grounding",
    "metaphor_based",
    "action_first",
    "inner_dialogue",
    "decision_filter",
    "habit_correction",
    "surrender_detachment",
]

TARGET_MIN = 300
TARGET_MAX = 500
MAX_OPENING_REPETITIONS = 3
MAX_ACTION_REPETITIONS = 3
MAX_DISTILLED_WISDOM_EXAMPLES = 5

SANSKRIT_PATTERN = re.compile(r"[\u0900-\u097F]")
SCRIPTURE_LEAK_PATTERN = re.compile(
    r"\b(gita|upanishad|krishna|arjuna|kena|katha|mundaka|chapter\s+\d+|passage\s+\d+|verse\s+\d+)\b",
    re.IGNORECASE,
)
LISTICLE_PATTERN = re.compile(r"^\s*(?:\d+\.|[-*])\s", re.MULTILINE)

GITA_BOOK_PATTERN = re.compile(r"gita", re.IGNORECASE)
UPANISHAD_BOOKS = {"kena", "katha", "mundaka"}

SCENARIO_TAG_RULES: dict[str, tuple[set[str], set[str]]] = {
    "career": (
        {"duty", "karma", "purpose", "attachment"},
        {"confusion", "fear", "purpose"},
    ),
    "relationship": (
        {"attachment", "trust", "detachment", "devotion"},
        {"attachment", "anger", "fear", "ego", "trust"},
    ),
    "discipline": (
        {"discipline", "meditation", "teacher_student", "self_knowledge"},
        {"discipline", "restlessness", "self-control", "desire"},
    ),
    "fear_change": (
        {"death", "immortality", "trust", "liberation"},
        {"fear", "grief", "trust", "inner_steadiness"},
    ),
    "attachment": (
        {"renunciation", "detachment", "dharma", "karma"},
        {"attachment", "desire", "fear", "detachment"},
    ),
    "purpose": (
        {"self_knowledge", "atman", "brahman", "non_duality", "reality", "consciousness", "liberation"},
        {"purpose", "confusion", "inner_steadiness"},
    ),
    "self_control": (
        {"discipline", "meditation", "renunciation"},
        {"self-control", "anger", "desire", "discipline", "restlessness"},
    ),
    "inner_conflict": (
        {"self_knowledge", "teacher_student", "non_duality", "reality"},
        {"confusion", "ego", "desire", "inner_steadiness", "fear"},
    ),
}

SCENARIO_TEMPLATES: dict[str, list[str]] = {
    "career": [
        "I feel pulled between security and meaningful work, and I cannot tell which voice to trust.",
        "My career decisions feel heavy because I keep measuring myself by outcomes.",
        "I know I need to act, but fear keeps making the next professional step feel bigger than it is.",
        "I feel lost about work, and the pressure to choose correctly is making me freeze.",
        "I want to move forward in my career without losing my deeper values.",
        "I keep overthinking professional choices until I lose sight of what is actually mine to do.",
        "I feel stuck between ambition and honesty, and it is making work feel confusing.",
        "I want to do my work sincerely, but I keep tying my peace to the result.",
        "Responsibility at work feels heavy, and I want to act without panic.",
        "I am trying to choose a career direction, but my mind keeps multiplying consequences.",
    ],
    "relationship": [
        "My relationship tension keeps pulling me into reaction instead of wisdom.",
        "I keep expecting another person to respond a certain way, and it is exhausting me.",
        "I want to respond with honesty in this relationship, but hurt keeps taking over first.",
        "I feel disappointed again and again because I keep gripping what I want from someone else.",
        "Part of me wants to soften, but another part keeps guarding itself.",
        "I know I need a calmer response in this relationship, but emotion keeps getting there first.",
        "I want more steadiness in how I relate to others, especially when I feel misunderstood.",
        "My attachment to being understood is making every conversation feel heavier.",
        "I keep reacting from insecurity in relationships, and I want to return to something deeper.",
        "I want to care deeply without letting fear or control define how I show up.",
    ],
    "discipline": [
        "I keep breaking my own structure when discomfort appears.",
        "I want stronger discipline, but I keep slipping when the moment gets inconvenient.",
        "My routines collapse as soon as emotional pressure rises.",
        "I know what steadiness requires, but I keep choosing what is easier.",
        "I want a more reliable inner structure instead of bursts of effort.",
        "I keep losing discipline in the same places, and I want to interrupt that pattern.",
        "I start sincerely, but I do not stay steady long enough for the habit to take root.",
        "I want to build discipline without turning it into self-punishment.",
        "My good intentions keep fading before they become action.",
        "I am tired of making promises to myself that I do not keep.",
    ],
    "fear_change": [
        "I know change is natural, but I still react as if it will undo me.",
        "Fear keeps turning uncertainty into something catastrophic.",
        "I want to act, but the possibility of loss keeps shrinking my courage.",
        "When life changes suddenly, I feel as if I lose my inner ground.",
        "I keep treating uncertainty like proof that something is wrong.",
        "Fear of change keeps narrowing my judgment and slowing my next step.",
        "I want steadiness in uncertainty, but fear keeps taking over my thinking.",
        "My mind keeps reading change as danger even when I know better.",
        "I feel threatened by endings, even when part of me knows life is moving naturally.",
        "I want to meet change with honesty, but my fear keeps getting there first.",
    ],
    "attachment": [
        "I care deeply, but I keep handing my peace over to outcomes.",
        "I know I cannot control everything, but my mind keeps gripping anyway.",
        "The more I want something, the less steady I become around it.",
        "My expectations are making simple effort feel heavy and tense.",
        "I keep tying my emotional balance to whether life obeys my preferred ending.",
        "I want to work sincerely without being consumed by the result.",
        "The outcome keeps taking too much of my attention.",
        "I feel trapped by wanting certainty before I can stay calm.",
        "My effort becomes distorted whenever I get too attached to how things should unfold.",
        "I want to care without becoming controlled by what I want back.",
    ],
    "purpose": [
        "I am searching for direction, but everything feels shallow right now.",
        "I want a deeper way of living, but I keep getting lost in surface pressures.",
        "I feel disconnected from what really matters to me.",
        "Part of me knows life needs a truer center, but I do not know how to return to it.",
        "I keep moving through responsibilities without feeling inwardly aligned.",
        "I want to live from something deeper than habit and appearance.",
        "I feel ungrounded in purpose, even when life looks functional from the outside.",
        "I keep asking what matters, but my mind stays on the surface.",
        "I want more inward direction, not just more external progress.",
        "Life feels crowded, but not deeply meaningful right now.",
    ],
    "self_control": [
        "My impulses keep getting ahead of my deeper judgment.",
        "I want more restraint, especially when emotion starts driving the moment.",
        "I know what would be wiser, but I keep yielding to what is immediate.",
        "I want to interrupt the impulse before it becomes action.",
        "My reactions often arrive before my judgment does.",
        "I keep doing what feels easier in the moment and regretting it later.",
        "I want a stronger inner pause before I act.",
        "I lose self-command when the pressure becomes emotional.",
        "I want to guide my impulses instead of obeying them.",
        "I keep getting carried away before I can return to myself.",
    ],
    "inner_conflict": [
        "Part of me wants what is wise, but another part keeps reaching for what is easier.",
        "I feel pulled in different directions inside, and it is making even simple choices heavy.",
        "I cannot tell which part of me is speaking truth and which part is speaking fear.",
        "My mind keeps arguing with itself, and I want a steadier center.",
        "I feel inwardly fragmented and do not know how to return to wholeness.",
        "One part of me wants honesty, but another part wants comfort and escape.",
        "I feel torn between what I know and what I keep doing.",
        "I want to return to a deeper center instead of reacting from inner conflict.",
        "Different voices inside me keep pulling at the same decision.",
        "I want to stop living from fragmentation and return to something more whole.",
    ],
}

SCENARIO_CONTEXTS: dict[str, list[str]] = {
    "career": [
        "I notice it most when the next career move starts to feel loaded with consequences.",
        "It shows up whenever work starts feeling like a test of my worth.",
        "The pressure gets louder whenever I try to choose between security and meaning.",
        "I can feel it most when professional responsibility and inner honesty seem to pull apart.",
        "This becomes hardest when effort matters to me but outcomes feel uncertain.",
        "It surfaces whenever I try to move forward without wanting to betray what matters to me.",
    ],
    "relationship": [
        "I notice it most when I want closeness but also feel the urge to protect myself.",
        "It becomes strongest when hurt and expectation get mixed together.",
        "This usually happens when I want to be honest but emotional pressure gets there first.",
        "I feel it most when I care deeply and still want control over how the other person responds.",
        "It gets louder when I want peace but keep reaching for reassurance from someone else.",
        "I can feel it especially when my need to be understood starts running ahead of calm judgment.",
    ],
    "discipline": [
        "It shows up most when the better choice feels ordinary and the easier choice feels immediate.",
        "I notice it when discomfort appears and my structure starts weakening.",
        "This gets louder when I need consistency more than motivation.",
        "I feel it most at the exact moment I should return to the habit instead of drifting away.",
        "It becomes hardest when pressure rises and I stop trusting small repeated action.",
        "I keep seeing it when I want steadiness but still bargain with the easier impulse.",
    ],
    "fear_change": [
        "It becomes strongest when uncertainty starts feeling personal instead of temporary.",
        "I notice it most when endings begin to feel like a threat to my identity.",
        "This gets louder whenever loss feels bigger than my ability to stay grounded.",
        "I can feel it when fear starts reading change as proof that something is wrong.",
        "It usually appears when I want courage but my mind keeps rehearsing disaster.",
        "I notice it whenever change feels like it might take away more than I can bear.",
    ],
    "attachment": [
        "I can feel it whenever my effort becomes tangled with how I want life to respond.",
        "It shows up when I want peace but keep bargaining with the outcome instead.",
        "This gets louder whenever I start treating uncertainty like something I must control first.",
        "I notice it most when care turns into pressure and pressure turns into grasping.",
        "It becomes hardest when I try to hold on so tightly that honest effort starts shrinking.",
        "I feel it whenever my emotional balance starts depending on a preferred ending.",
    ],
    "purpose": [
        "I notice it when life stays busy but inwardly still feels thin.",
        "It becomes strongest when surface progress keeps replacing deeper direction.",
        "This usually appears when I want a truer center but noise keeps answering first.",
        "I can feel it when outward activity continues but inward meaning feels distant.",
        "It gets louder when I want direction, not just motion.",
        "I notice it whenever I keep functioning while still feeling disconnected from what is deeply honest.",
    ],
    "self_control": [
        "It becomes strongest when emotion starts moving faster than judgment.",
        "I notice it when the impulse feels persuasive before the wiser response has time to speak.",
        "This appears whenever I want restraint but the immediate reaction feels louder.",
        "I can feel it when pressure turns my next move into something automatic.",
        "It gets louder whenever I know better but still move with the first urge.",
        "I notice it most in the small moments when the pause disappears and the reaction takes over.",
    ],
    "inner_conflict": [
        "It becomes strongest when different motives inside me all try to lead at once.",
        "I notice it when honesty and comfort stop pulling in the same direction.",
        "This gets louder whenever fear and deeper judgment start sounding equally convincing.",
        "I can feel it when my inner life becomes crowded and fragmented instead of clear.",
        "It becomes hardest when one part of me wants truth and another part wants relief.",
        "I notice it most when I keep changing directions because no inner voice feels steady enough to trust.",
    ],
}

PROMPT_TAILS: dict[str, list[str]] = {
    "career": [
        "I want a cleaner way to move without turning every choice into a verdict on my future.",
        "I need a way to choose that keeps effort honest instead of making fear the hidden decision-maker.",
        "I am looking for guidance that helps me act without making success the measure of my worth.",
        "I want to stop asking work to settle questions that belong to the deeper self.",
        "I need help returning to the part of this decision that is actually mine to carry.",
        "I want practical clarity that helps me work sincerely instead of anxiously.",
    ],
    "relationship": [
        "I want a response that protects honesty without feeding more emotional noise.",
        "I need help caring without letting control hide inside that care.",
        "I want to stop making peace depend on another person's response.",
        "I need a calmer way to stay truthful when connection feels uncertain.",
        "I want to respond with more steadiness than the moment is currently drawing out of me.",
        "I am looking for a wiser way to stay open without becoming reactive.",
    ],
    "discipline": [
        "I need something steadier than waiting to feel ready again.",
        "I want a pattern I can actually repeat, not just a burst of effort.",
        "I need help returning to structure without turning it into self-attack.",
        "I want practical guidance for staying consistent when resistance is ordinary rather than dramatic.",
        "I am trying to build reliability, not intensity, and I keep forgetting that in the moment.",
        "I need a calmer way to hold discipline so it does not collapse the moment pressure rises.",
    ],
    "fear_change": [
        "I want a way to stay grounded without pretending uncertainty is easy.",
        "I need help meeting change without letting imagined loss become the whole story.",
        "I want to respond with more courage than catastrophe.",
        "I need a steadier way to stay present when my mind starts forecasting the worst.",
        "I want to stop treating uncertainty like proof that life is turning against me.",
        "I need something practical that helps fear loosen its grip on the next step.",
    ],
    "attachment": [
        "I want to care sincerely without letting the result occupy my whole mind.",
        "I need help relaxing the grip without becoming passive or indifferent.",
        "I want a cleaner relationship with effort, outcome, and expectation.",
        "I need a wiser way to carry desire so it does not distort everything around it.",
        "I want to stop turning uncertainty into pressure I keep handing back to myself.",
        "I need practical guidance for caring deeply without being ruled by what I want back.",
    ],
    "purpose": [
        "I want a way back to depth that does not depend on having my whole life figured out.",
        "I need help returning to what matters without escaping my actual responsibilities.",
        "I want to feel less scattered by the surface of life and more guided by what is true.",
        "I need practical direction that reconnects meaning with daily action.",
        "I want to live from something deeper than noise, image, or momentum.",
        "I need help remembering what inner alignment feels like in ordinary life.",
    ],
    "self_control": [
        "I want more room between the impulse and the action that follows it.",
        "I need help returning to judgment before reaction finishes the moment for me.",
        "I want to practice restraint without turning it into harshness.",
        "I need a more dependable inner pause when pressure starts rising.",
        "I want to stop living from the first urge and return to the wiser one.",
        "I need practical guidance that helps self-command become more natural over time.",
    ],
    "inner_conflict": [
        "I want to trust the truer voice without pretending the conflict is not there.",
        "I need help returning to a center that feels cleaner than my shifting moods.",
        "I want to stop letting inner noise make every choice heavier than it needs to be.",
        "I need a way to move even when different parts of me are still arguing.",
        "I want to strengthen the voice that stays honest under pressure.",
        "I need practical clarity for moments when relief and truth stop pointing in the same direction.",
    ],
}

RESPONSE_BRIDGES: dict[str, list[str]] = {
    "career": [
        "Work becomes less confusing when identity is not asked to hang on every result.",
        "Much of the strain softens once responsibility is separated from self-judgment.",
        "Career pressure becomes more workable when honesty matters more than image.",
        "Professional clarity often returns when effort is reclaimed from imagined consequence.",
        "The mind steadies when work is treated as service and responsibility, not as a verdict on worth.",
        "The choice gets cleaner when the future stops being used to intimidate the present step.",
    ],
    "relationship": [
        "Relationships become cleaner when honesty is not mixed with the demand to control the response.",
        "The heart often settles once care is separated from the urge to manage how it lands.",
        "A calmer connection becomes possible when expectation stops deciding the tone.",
        "Relational pain becomes more workable when truth speaks before protection or performance.",
        "Closeness gets healthier when steadiness matters more than immediate reassurance.",
        "The response usually becomes wiser when hurt is acknowledged without being allowed to lead.",
    ],
    "discipline": [
        "Discipline becomes sturdier when repetition matters more than intensity.",
        "Consistency grows when the ordinary return is valued instead of dismissed.",
        "A pattern changes faster when the first drift is interrupted instead of excused.",
        "Structure becomes kinder and stronger when it is measured by return, not perfection.",
        "The habit deepens when the better action is repeated before motivation catches up.",
        "Self-trust grows through kept promises that are small enough to survive the day.",
    ],
    "fear_change": [
        "Fear loses some of its force when change is not treated like total erasure.",
        "The nervous system settles when uncertainty is met as movement, not doom.",
        "Courage often begins when loss stops being allowed to define the whole future.",
        "A steadier relationship with change grows when imagination no longer gets to write the final meaning.",
        "Inner ground returns when endings are not mistaken for the end of what is deepest in you.",
        "The next step becomes possible once catastrophe stops being treated like certainty.",
    ],
    "attachment": [
        "Attachment loosens when care is no longer fused with control.",
        "Peace becomes more available when effort is separated from possession.",
        "The whole situation gets lighter when the mind stops trying to secure the ending in advance.",
        "Desire becomes cleaner when it is carried honestly rather than desperately.",
        "Pressure softens when the outcome stops being asked to settle the inner life.",
        "The heart usually relaxes when sincere action matters more than guarantee.",
    ],
    "purpose": [
        "A deeper direction appears more easily when life is not being answered only from the surface.",
        "Purpose becomes more livable when meaning is practiced in small acts instead of admired from a distance.",
        "The inner life clears when movement starts serving truth instead of just momentum.",
        "Depth grows when daily life is allowed to answer what matters, not only what is urgent.",
        "Direction becomes steadier when the quieter truth is given a place in ordinary action.",
        "The search becomes less abstract when values are asked to shape one real part of the day.",
    ],
    "self_control": [
        "Self-command strengthens when the pause is treated as part of the action.",
        "Impulse weakens when judgment is given even a small moment to return.",
        "Restraint becomes more natural when the first urge stops being treated like the truest one.",
        "The inner life changes when reaction is interrupted before it gathers speed.",
        "A wiser response becomes possible when emotion is felt without being obeyed immediately.",
        "Self-control grows from repeated pauses that teach the mind a cleaner path.",
    ],
    "inner_conflict": [
        "Inner conflict softens when every voice inside is not given the same authority.",
        "Clarity grows when the deeper judgment is trusted a little more than the louder reaction.",
        "The inner life begins to rejoin itself when honest action is taken before total agreement arrives.",
        "Fragmentation eases when truth is practiced instead of only argued about inwardly.",
        "A steadier center forms when relief is not automatically treated as wisdom.",
        "The conflict becomes more workable when the cleanest voice is allowed one real step.",
    ],
}

SCENARIO_STRUCTURE_MAP: dict[str, list[str]] = {
    "career": ["decision_filter", "direct_clarity", "reflection_action"],
    "relationship": ["reflection_action", "question_guided", "inner_dialogue"],
    "discipline": ["habit_correction", "action_first", "direct_clarity"],
    "fear_change": ["short_grounding", "reflection_action", "surrender_detachment"],
    "attachment": ["surrender_detachment", "reflection_action", "question_guided"],
    "purpose": ["metaphor_based", "reflection_action", "inner_dialogue"],
    "self_control": ["habit_correction", "action_first", "inner_dialogue"],
    "inner_conflict": ["inner_dialogue", "decision_filter", "question_guided"],
}

OPENINGS: dict[str, list[str]] = {
    "reflection_action": [
        "This kind of pressure can make even simple choices feel heavier than they are.",
        "What you are describing is a real human strain, not a personal failure.",
        "It makes sense that this feels difficult, especially when the mind is already carrying so much.",
        "Moments like this can quietly drain confidence, even when part of you already knows what matters.",
        "There are seasons when the deepest difficulty is not outer action, but the state of the inner life.",
        "When pressure builds inside, even honest effort can start to feel confused or fragmented.",
    ],
    "direct_clarity": [
        "The clearest place to begin is not with more pressure, but with one honest truth.",
        "What helps most here is not speed, but a cleaner way of seeing the situation.",
        "The issue is not that you care too much; it is that pressure is starting to distort the way you carry it.",
        "The first shift is simple: stop asking the whole situation to settle before you take one honest step.",
        "The mind usually clears when you stop arguing with what is true and start meeting it directly.",
        "A steadier response begins when you stop confusing urgency with clarity.",
    ],
    "question_guided": [
        "Before trying to solve everything, it may help to ask one calmer question.",
        "A wiser response often begins by turning one honest question toward the heart of the struggle.",
        "Instead of following the loudest reaction, pause long enough to ask what is actually true here.",
        "Sometimes clarity comes less from forcing an answer and more from asking the right question gently.",
        "What if the next step is not to settle the whole situation, but to ask what part of it is truly yours?",
        "A calmer response can begin with one question that separates truth from mental noise.",
    ],
    "short_grounding": [
        "You do not need to solve the whole future to respond wisely to this moment.",
        "When fear is loud, the next grounded step matters more than a perfect inner state.",
        "This moment asks for steadiness first, not total certainty.",
        "You can meet this pressure without letting it decide everything for you.",
        "The next truthful action can be small and still be enough for today.",
        "Even now, there is room for one grounded response.",
    ],
    "metaphor_based": [
        "A mind under strain is a little like water disturbed by wind: forcing it harder rarely makes it clearer.",
        "Pressure can turn the inner life into a fogged mirror, where everything is present but harder to see clearly.",
        "When the mind is pulled in many directions, it behaves like a compass near a magnet and starts misreading what matters.",
        "The inner life can become like a room filled with echoes, where reaction sounds louder than truth.",
        "Sometimes the heart is like a clenched hand; the tighter the grip, the less it can actually hold wisely.",
        "A restless inner life can be like a lamp flickering in wind, still capable of light but needing shelter to steady itself.",
    ],
    "action_first": [
        "Start with one small action before you ask the mind for complete agreement.",
        "Begin with the next honest step, then let the mind learn from what that action makes visible.",
        "Do one clear thing first, because motion rooted in truth often teaches more than rumination.",
        "Take one grounded action now and let that become the place where steadiness starts returning.",
        "Pick one responsible move and complete it before reopening the inner argument.",
        "Act in one modest truthful way first, then let the rest of the situation become quieter around it.",
    ],
    "inner_dialogue": [
        "There is often more than one voice active in a moment like this.",
        "One part of you is reacting, and another part of you is still trying to stay honest.",
        "The struggle here is not only outer; it is also the conversation happening inside you.",
        "Usually there is a voice asking for relief and another asking for truth at the same time.",
        "This often becomes easier when you stop treating every inner voice as equally trustworthy.",
        "What you need may not be more force, but a cleaner relationship between reaction and deeper judgment.",
    ],
    "decision_filter": [
        "When the mind goes in circles, it helps to use a steadier filter than impulse.",
        "This decision may become clearer if you stop asking what feels easiest and ask what stays true under pressure.",
        "A useful filter here is to separate what is urgent in thought from what is honest in action.",
        "The mind steadies when a decision is tested against truth instead of tested against fear.",
        "What clarifies a hard choice is often not more analysis, but a cleaner standard for what matters.",
        "This gets lighter when the decision is filtered through honesty, not just imagined consequences.",
    ],
    "habit_correction": [
        "The pattern matters here more than the promise.",
        "This kind of struggle usually changes when the repeating pattern is interrupted early.",
        "What needs attention is not only the intention, but the point where the old habit starts taking over.",
        "Steadier living often begins when the familiar pattern is recognized before it becomes action.",
        "The wiser shift here is not dramatic; it is the quiet interruption of what keeps repeating.",
        "Habits change when the mind learns that the old automatic path is no longer the one it must follow.",
    ],
    "surrender_detachment": [
        "This becomes lighter when care is separated from control.",
        "You do not need to stop caring; you need a gentler relationship with what you cannot command.",
        "The strain here often comes from gripping too tightly around what was never fully yours to manage.",
        "Detachment here does not mean distance; it means carrying the situation without trying to force its ending.",
        "Trust becomes more real when the heart loosens its demand for guarantees.",
        "The next step is not indifference, but a cleaner way of holding what matters.",
    ],
}

APPLICATION_PATTERNS: dict[str, list[str]] = {
    "reflection_action": [
        "A useful truth to lean on here is that {teaching}.",
        "What helps in a moment like this is remembering that {teaching}.",
        "A steadier way to hold this is to remember that {teaching}.",
        "The deeper guidance in this situation is that {teaching}.",
    ],
    "direct_clarity": [
        "The practical heart of this is simple: {teaching}.",
        "The clearest lesson here is that {teaching}.",
        "What matters most is remembering that {teaching}.",
        "The honest center of this situation is that {teaching}.",
    ],
    "question_guided": [
        "What changes if you work from the truth that {teaching}?",
        "What becomes clearer when you remember that {teaching}?",
        "How would the next step look if you trusted that {teaching}?",
        "What if the wiser response begins by accepting that {teaching}?",
    ],
    "short_grounding": [
        "Hold to this for now: {teaching}.",
        "Let this be the steady truth in the middle of the pressure: {teaching}.",
        "For this moment, it is enough to remember that {teaching}.",
        "Return to this simple truth: {teaching}.",
    ],
    "metaphor_based": [
        "The deeper lesson underneath that strain is still simple: {teaching}.",
        "Beneath the noise, the lesson is this: {teaching}.",
        "The steadier understanding beneath this pressure is that {teaching}.",
        "The quiet truth underneath the turbulence is that {teaching}.",
    ],
    "action_first": [
        "Do the next honest thing, because {teaching}.",
        "Start with action rooted in this truth: {teaching}.",
        "Move first from this understanding: {teaching}.",
        "Let one truthful action begin here, because {teaching}.",
    ],
    "inner_dialogue": [
        "The reacting voice may be loud, but the steadier voice already knows that {teaching}.",
        "The part of you asking for truth is pointing toward this: {teaching}.",
        "Under the noise, a clearer voice is still saying that {teaching}.",
        "When reaction quiets slightly, the deeper judgment often recognizes that {teaching}.",
    ],
    "decision_filter": [
        "Use this as the filter: {teaching}.",
        "Let this be the decision rule for the next step: {teaching}.",
        "A steadier filter here is to remember that {teaching}.",
        "Let the next choice pass through this truth: {teaching}.",
    ],
    "habit_correction": [
        "The pattern weakens when you remember that {teaching}.",
        "The habit starts to change when you work from the truth that {teaching}.",
        "A better pattern becomes possible when you hold to this: {teaching}.",
        "The old loop loosens when you remember that {teaching}.",
    ],
    "surrender_detachment": [
        "The grip softens when you remember that {teaching}.",
        "Detachment becomes healthier when you remember that {teaching}.",
        "A truer surrender begins when you hold to this: {teaching}.",
        "The heart relaxes its demand when it remembers that {teaching}.",
    ],
}

ACTION_BANKS: dict[str, list[str]] = {
    "career": [
        "Write down the one professional move that feels most honest, then do the smallest part of it today.",
        "Choose one work decision you have been postponing, name the next action, and complete only that action.",
        "List what is yours to do in your work right now, then give one item your full attention without rehearsing outcomes.",
        "Before the day ends, take one modest step toward the work that fits your deeper values.",
        "Pick one professional responsibility you have been circling and begin it before you feel fully ready.",
        "Write two columns called truth and fear, then act on the clearest truth in the next twenty-four hours.",
        "Choose one conversation, application, or task that you already know matters, and complete it without reopening the whole debate.",
        "Take one small career step today that reflects integrity more than image.",
        "Name one work choice you have delayed, set a time for it, and keep that appointment with yourself.",
        "Let one concrete action at work carry more weight today than the outcome you are imagining.",
        "Reduce the decision to one honest next move and finish that before asking the future to settle.",
        "Do one piece of meaningful work today without checking whether it guarantees the result you want.",
    ],
    "relationship": [
        "Pause before your next difficult conversation and write one sentence describing what you truly want to express without blame.",
        "Choose one relationship expectation you can loosen today and replace it with one honest question.",
        "Before reacting, name the hurt underneath the reaction and speak from that quieter place instead.",
        "Take one conversation today and focus on listening fully before trying to correct or control it.",
        "Write down what you are asking from the other person, then ask what part of that burden is actually yours.",
        "Choose one relational tension point and answer it today with honesty instead of emotional speed.",
        "For one interaction today, let your goal be clarity rather than winning, proving, or being reassured.",
        "If hurt rises, pause long enough to ask what response would still feel clean to you tomorrow.",
        "Name one place where fear is shaping your tone, then soften just that one part of the interaction.",
        "Let one conversation today be guided by steadiness rather than the urge to control how it lands.",
        "Choose one honest sentence you need to say and speak it without adding accusation or drama.",
        "Release one expectation you are gripping in this relationship and see what honesty remains after that.",
    ],
    "discipline": [
        "Choose one habit that matters and repeat it at the same time today, even if the effort feels plain.",
        "Interrupt the first moment of drift today and return to the better action before the old pattern settles in.",
        "Pick one small structure you can actually keep and protect it more carefully than your mood.",
        "Remove one obstacle that usually weakens your discipline before the day gets noisier.",
        "Delay one easy impulse today and let that pause train steadiness instead of self-punishment.",
        "Write down the exact point where your routine usually breaks, then change only that point today.",
        "Keep one promise to yourself today, even if it is small, and treat consistency as the win.",
        "Choose one modest discipline and complete it before you ask yourself whether you feel like it.",
        "Make the wiser habit easier to start today by preparing for it before resistance appears.",
        "Take one repetitive action that supports your structure and do it without dramatizing it.",
        "When discomfort appears, return to the routine once before negotiating with it.",
        "Let one small act of consistency count more today than a burst of motivation.",
    ],
    "fear_change": [
        "Write down what you fear losing, then name one part of you that remains even if circumstances change.",
        "Choose one small change you have been resisting and meet it with one calm deliberate action today.",
        "When fear rises, breathe slowly and name one truth that still holds in the middle of uncertainty.",
        "Take one safe action today that fear has been delaying, even if the step is modest.",
        "Pause when your mind starts forecasting loss and return to one concrete thing you can do honestly right now.",
        "Name the change you are afraid of, then write one sentence about what would still remain true after it.",
        "Before the day ends, do one small thing that proves fear does not get to choose everything for you.",
        "When uncertainty feels personal, place your attention on one grounded action instead of one imagined disaster.",
        "Choose one area where change feels threatening and respond with one steady act rather than one fearful story.",
        "Take ten quiet breaths, then move one step toward the thing fear keeps telling you to postpone.",
        "Write one sentence that separates change itself from the catastrophe your mind is attaching to it.",
        "Let your next action come from courage scaled to today, not from the demand to feel fearless.",
    ],
    "attachment": [
        "Release one expectation you are gripping and return your effort to the part that is actually yours today.",
        "Choose one task to do wholeheartedly without checking whether it guarantees the ending you want.",
        "Name the result you keep trying to force, then take one honest step that does not depend on controlling it.",
        "When the outcome starts tightening your mind, return to one action that is yours regardless of how life responds.",
        "Pick one place where you usually cling for certainty and soften that grip by one degree today.",
        "Write down what you are trying to control, then circle what is truly yours and act only on that part.",
        "Practice caring fully in one area today without demanding proof that it will turn out the way you prefer.",
        "Choose one expectation to loosen and see whether your effort becomes cleaner when the grip softens.",
        "Before the next wave of pressure, ask what honest action remains even if the result stays uncertain.",
        "Let one part of your day be shaped by sincere effort instead of by trying to secure a preferred ending.",
        "Do one thing with care today and refuse one extra round of outcome-checking afterward.",
        "Carry one desire more lightly today by returning your attention to effort rather than prediction.",
    ],
    "purpose": [
        "Take ten quiet minutes today and write one direction that still feels inwardly honest.",
        "Choose one action before the day ends that reflects your deeper values rather than surface pressure.",
        "Step back from noise for a few minutes and ask what still feels true when fear is not answering for you.",
        "Write down what feels empty and what feels quietly alive, then move one step toward what feels alive.",
        "Give one small part of your day to what feels deeply meaningful instead of merely urgent.",
        "Pause long enough to name the kind of life you want to be living beneath appearances and routine.",
        "Choose one responsibility to do today in a way that reflects your deeper center rather than outer performance.",
        "Let one decision today be shaped by what is inwardly true instead of only by what looks acceptable.",
        "Spend ten minutes in silence and write one sentence about what matters when noise is not deciding for you.",
        "Move one step toward the truer side of your life today, even if the larger direction is still unfolding.",
        "Name one place where you feel disconnected from meaning, then answer it with one honest act.",
        "Choose one moment today to live from value rather than from appearance.",
    ],
    "self_control": [
        "Delay one impulse today and use that pause to remember what you want your life to be shaped by.",
        "When emotion rises, pause long enough to name the wiser response before acting.",
        "Choose one moment today to let judgment arrive before reaction does.",
        "Interrupt the first urge that usually sweeps you away and return to one steadier choice instead.",
        "Pick one recurring impulse and meet it today with one honest pause rather than immediate obedience.",
        "When pressure spikes, ask what action you would still respect tomorrow, then do that.",
        "Use one difficult moment today to practice a slower response instead of your fastest one.",
        "Name the impulse clearly, breathe once, and choose the action that still fits your deeper values.",
        "Set one boundary today that helps your wiser judgment stay in the lead.",
        "Choose one place where you usually react quickly and answer it today with restraint instead.",
        "Let one small pause today become proof that your impulses do not have to make the final choice.",
        "Before acting on emotion, ask what part of you is speaking and which part you want to trust.",
    ],
    "inner_conflict": [
        "Write down the two strongest inner pulls you feel, then choose the one that remains cleanest under honesty.",
        "Pause when the mind starts arguing with itself and ask which option still feels true when fear quiets a little.",
        "Name what one part of you wants and what another part wants, then take one step that respects your deeper judgment.",
        "Before reacting, ask which inner voice is asking for comfort and which is asking for truth.",
        "Take ten quiet minutes and separate what is fear, what is desire, and what is actually honest.",
        "Choose one decision point today and respond from the part of you that will still feel truthful tomorrow.",
        "When you feel inwardly split, reduce the moment to one question: what action stays clean after the pressure passes?",
        "Write down the conflicting voices, then move one step toward the voice that asks more of your honesty.",
        "Let one small action today come from your deeper center instead of from the loudest inner argument.",
        "Ask what you would do if relief were not choosing for you, then take one step in that direction.",
        "When you feel fragmented, stop solving the whole future and answer only the truest part of the next moment.",
        "Choose one place where comfort and truth diverge, and let your next act side with truth.",
    ],
}

CLOSINGS: dict[str, list[str]] = {
    "reflection_action": [
        "The point is not perfection, but a steadier way of meeting what is here.",
        "Let the next step be simple enough that you can repeat it honestly.",
        "What matters now is following through without making the step dramatic.",
        "A steadier life is usually built through repeated honest actions, not one decisive feeling.",
    ],
    "direct_clarity": [
        "You do not need a different future before you can begin; you need one truthful move now.",
        "That is enough for today because clarity often grows through action, not before it.",
        "The next honest step will usually teach the mind more than one more round of pressure.",
        "Keep the response plain and clean, and let that simplicity do its work.",
    ],
    "question_guided": [
        "Let the answer come through one honest action rather than another long inner argument.",
        "You do not need to settle the whole struggle tonight; you only need to answer the next true question well.",
        "Often the mind quiets more by being answered honestly than by being silenced forcefully.",
        "One clean response can teach more than many restless thoughts.",
    ],
    "short_grounding": [
        "That one action is enough for now.",
        "For today, let one grounded response be the whole practice.",
        "Small truthful action is enough to begin returning to yourself.",
        "You can let this moment be simpler than the mind is making it.",
    ],
    "metaphor_based": [
        "The goal is not to force the water still, but to stop stirring it unnecessarily.",
        "A steadier center often appears when you stop feeding the turbulence around it.",
        "The mind usually clears when it is held more gently and more honestly.",
        "Let the image remind you that calm is practiced, not commanded.",
    ],
    "action_first": [
        "Let the action teach the mind what steadiness feels like.",
        "The response becomes clearer once your feet move in the right direction.",
        "Often one honest act quiets more noise than a long chain of analysis.",
        "Move cleanly once, and let the rest settle around that truth.",
    ],
    "inner_dialogue": [
        "The quieter voice may not shout, but it is often the one that keeps your life clean.",
        "Over time, that is how deeper judgment becomes easier to trust.",
        "Each honest response teaches the inner life which voice to follow next time.",
        "The aim is not to erase conflict instantly, but to stop letting confusion lead the moment.",
    ],
    "decision_filter": [
        "A cleaner filter often turns a louder problem into a more workable next step.",
        "The mind usually stops circling once the decision is held against something steadier than fear.",
        "Use that filter once today and let the result teach you what clarity feels like.",
        "The next truthful move often becomes visible once the false options lose their drama.",
    ],
    "habit_correction": [
        "That is how the old loop starts losing its authority.",
        "A repeated honest interruption is often more powerful than a grand promise.",
        "The point is not intensity, but a better pattern repeated faithfully.",
        "Keep the action small enough that you can actually keep returning to it.",
    ],
    "surrender_detachment": [
        "That is how care becomes cleaner without becoming weaker.",
        "You can loosen the grip without loosening your sincerity.",
        "A quieter kind of trust usually grows through these smaller acts of release.",
        "Let the heart carry the situation more lightly without becoming careless about what is yours.",
    ],
}

OPENING_TAILS: dict[str, list[str]] = {
    "career": [
        "especially when work starts feeling tied to your worth.",
        "particularly when outcomes seem to define too much of the decision.",
        "especially when responsibility and identity start blending together.",
        "which often happens when the future is being treated like a final verdict.",
        "particularly when honest effort starts carrying too much imagined consequence.",
        "especially when professional pressure begins to distort what matters most.",
    ],
    "relationship": [
        "especially when hurt and expectation arrive together.",
        "particularly when the need to be understood becomes urgent.",
        "which often happens when care quietly turns into control.",
        "especially when closeness and self-protection are both active at once.",
        "particularly when emotion speaks faster than honesty.",
        "especially when fear of disconnection starts shaping your tone.",
    ],
    "discipline": [
        "especially when discomfort makes the easier option feel persuasive.",
        "particularly when consistency matters more than motivation.",
        "which often happens when ordinary effort starts feeling invisible.",
        "especially when the old pattern offers relief before the wiser action begins.",
        "particularly when the mind wants a breakthrough more than a repeatable habit.",
        "especially when the better choice feels plain and the easier one feels immediate.",
    ],
    "fear_change": [
        "especially when uncertainty starts sounding more personal than it is.",
        "particularly when the mind begins treating change like danger.",
        "which often happens when endings feel larger than they truly are.",
        "especially when fear starts telling a story before truth has time to speak.",
        "particularly when loss is being imagined before it is actually here.",
        "especially when the future starts feeling like a threat instead of a movement of life.",
    ],
    "attachment": [
        "especially when care turns into pressure and pressure turns into grasping.",
        "particularly when peace starts depending on a preferred ending.",
        "which often happens when effort and control get mixed together.",
        "especially when wanting something deeply begins to tighten the whole mind.",
        "particularly when the outcome starts occupying more attention than the action.",
        "especially when uncertainty feels harder to carry than it needs to be.",
    ],
    "purpose": [
        "especially when outer progress and inner direction stop feeling aligned.",
        "particularly when life stays busy but inwardly thin.",
        "which often happens when appearance becomes louder than meaning.",
        "especially when the mind keeps answering from the surface.",
        "particularly when what matters feels quieter than what is urgent.",
        "especially when daily movement keeps going but deeper direction feels distant.",
    ],
    "self_control": [
        "especially when impulse moves faster than deeper judgment.",
        "particularly when emotion reaches the moment before wisdom does.",
        "which often happens when the first urge is mistaken for the truest one.",
        "especially when pressure makes reaction feel automatic.",
        "particularly when the immediate response starts sounding more convincing than the wiser one.",
        "especially when restraint disappears just before action begins.",
    ],
    "inner_conflict": [
        "especially when different inner voices all try to lead at once.",
        "particularly when comfort and honesty stop pulling in the same direction.",
        "which often happens when fear starts sounding as reasonable as truth.",
        "especially when the inner life feels crowded instead of centered.",
        "particularly when relief looks easier than alignment.",
        "especially when one part of you wants truth and another wants escape.",
    ],
}

ACTION_SUFFIXES: dict[str, list[str]] = {
    "career": [
        "Let the step stay small enough that fear does not get to run it.",
        "The aim is movement rooted in honesty, not immediate certainty.",
        "Treat the action as a way to clarify life, not as a final test of worth.",
        "Keep the move concrete enough that the mind cannot hide behind abstraction.",
        "Let effort, not prediction, carry the next part of the decision.",
        "Do not ask the future to settle before you complete this one part.",
    ],
    "relationship": [
        "Let your tone stay cleaner than your fear wants it to be.",
        "The point is honesty without trying to control the landing.",
        "Keep the response simple enough that emotion cannot easily hijack it.",
        "Let the action show care without making reassurance the hidden demand.",
        "This helps you return to truth instead of rehearsing reaction.",
        "Stay with the sentence that is honest, not the speech that tries to win.",
    ],
    "discipline": [
        "The win is repetition, not drama.",
        "Keep it small enough that you can repeat it tomorrow.",
        "Let consistency matter more than intensity for this one action.",
        "The point is to weaken the old loop before it gathers force.",
        "Treat the return itself as the practice you are building.",
        "Let this be proof that structure can survive discomfort.",
    ],
    "fear_change": [
        "The step only needs to be brave at today's scale.",
        "You are training trust, not trying to erase uncertainty in one move.",
        "Let the action be small enough that fear cannot turn it into a myth.",
        "This helps the mind remember that change is not the same as ruin.",
        "The goal is grounded movement, not dramatic confidence.",
        "Let courage arrive as a next step instead of a performance.",
    ],
    "attachment": [
        "That is how effort stays sincere without becoming controlling.",
        "Let the action belong to you even if the result does not.",
        "This is one way to care fully without gripping the ending.",
        "Let the step teach the difference between effort and possession.",
        "The point is to loosen pressure without loosening sincerity.",
        "Do the action, then release the extra attempt to manage what follows.",
    ],
    "purpose": [
        "Let the step reconnect you with depth, not just movement.",
        "The action matters because meaning grows through practice, not only through thought.",
        "Keep it close to what feels inwardly true instead of outwardly impressive.",
        "This is how direction becomes lived instead of merely admired.",
        "Let the move be small enough that it can come from honesty instead of performance.",
        "Treat the act as a return to center, not as a demand for instant certainty.",
    ],
    "self_control": [
        "That pause is how judgment learns to stay in the lead.",
        "Let the interruption itself become part of the training.",
        "The point is not suppression but cleaner self-command.",
        "This helps the wiser voice arrive before the impulse closes the space.",
        "Stay with the pause long enough for choice to reappear.",
        "Let the action prove that urgency does not have to become obedience.",
    ],
    "inner_conflict": [
        "Let the cleaner voice guide one move, even if the whole conflict is not resolved yet.",
        "You are not trying to erase tension instantly, only to stop letting confusion lead.",
        "The point is to strengthen the part of you that remains truthful under pressure.",
        "Let one honest act become more persuasive than the louder argument in the mind.",
        "This is how inner agreement begins to grow through action.",
        "Let the step come from the voice you would still trust tomorrow.",
    ],
}


@dataclass(slots=True)
class GeneratedDatasetExample:
    """Store one generated dataset row and its metadata."""

    wisdom_entry_id: int
    source_document_id: int
    book_title: str
    distilled_wisdom: str
    scenario_family: str
    response_structure: str
    user_prompt: str
    assistant_response: str
    record: dict[str, list[dict[str, str]]]


@dataclass(slots=True)
class ExpandedDatasetResult:
    """Container for the expanded dataset plus summary metrics."""

    examples: list[GeneratedDatasetExample]
    scenario_counts: Counter[str]
    structure_counts: Counter[str]
    opening_counts: Counter[str]
    action_counts: Counter[str]
    duplicate_prompts: int
    duplicate_responses: int
    skipped_entries: int


class DatasetGenerationV2Service:
    """Generate a large, diverse training dataset from approved wisdom entries."""

    def __init__(self) -> None:
        self._opening_counts: Counter[str] = Counter()
        self._action_counts: Counter[str] = Counter()
        self._prompt_keys: set[str] = set()
        self._response_keys: set[str] = set()
        self._distilled_counts: Counter[str] = Counter()
        self._duplicate_prompts = 0
        self._duplicate_responses = 0

    async def load_source_pool(self, db: AsyncSession) -> list[WisdomEntry]:
        """Load approved Gita and Upanishad wisdom entries for dataset generation."""

        stmt: Select[tuple[WisdomEntry]] = (
            select(WisdomEntry)
            .where(WisdomEntry.principle_status == "approved")
            .where(WisdomEntry.principle_quality_score >= 80)
            .where(WisdomEntry.distilled_wisdom.is_not(None))
            .where(WisdomEntry.distilled_wisdom != "")
            .order_by(WisdomEntry.source_document_id.asc(), WisdomEntry.id.asc())
        )
        entries = list((await db.scalars(stmt)).all())
        filtered: list[WisdomEntry] = []
        for entry in entries:
            title = (entry.book_title or "").strip()
            title_lower = title.lower()
            if GITA_BOOK_PATTERN.search(title_lower):
                filtered.append(entry)
                continue
            if title_lower in UPANISHAD_BOOKS and entry.source_document_id == 3:
                filtered.append(entry)
        return filtered

    async def generate_dataset(self, db: AsyncSession) -> ExpandedDatasetResult:
        """Generate the expanded dataset from the approved wisdom source pool."""

        source_entries = self._dedupe_source_entries(await self.load_source_pool(db))
        examples: list[GeneratedDatasetExample] = []
        scenario_counts: Counter[str] = Counter()
        structure_counts: Counter[str] = Counter()
        skipped_entries = 0

        for entry in source_entries:
            teaching_key = self._normalize_key(entry.distilled_wisdom or "")
            if self._distilled_counts[teaching_key] >= MAX_DISTILLED_WISDOM_EXAMPLES:
                skipped_entries += 1
                continue

            families = self._select_scenario_families(entry)
            generated_for_entry = 0
            target_examples = MAX_DISTILLED_WISDOM_EXAMPLES
            for family_index, scenario_family in enumerate(families):
                structure_candidates = self._structure_candidates(entry, scenario_family, family_index)
                for structure_index, response_structure in enumerate(structure_candidates):
                    example = self._build_example(
                        entry,
                        scenario_family,
                        response_structure,
                        family_index + structure_index,
                    )
                    if example is None:
                        continue
                    examples.append(example)
                    scenario_counts[scenario_family] += 1
                    structure_counts[response_structure] += 1
                    self._distilled_counts[teaching_key] += 1
                    generated_for_entry += 1
                    if (
                        generated_for_entry >= target_examples
                        or self._distilled_counts[teaching_key] >= MAX_DISTILLED_WISDOM_EXAMPLES
                    ):
                        break
                if (
                    generated_for_entry >= target_examples
                    or self._distilled_counts[teaching_key] >= MAX_DISTILLED_WISDOM_EXAMPLES
                ):
                    break

            if generated_for_entry < target_examples:
                for fallback_index, fallback_family in enumerate(SCENARIO_FAMILIES):
                    if generated_for_entry >= target_examples:
                        break
                    structure_candidates = self._structure_candidates(entry, fallback_family, fallback_index + 7)
                    for structure_index, response_structure in enumerate(structure_candidates):
                        example = self._build_example(
                            entry,
                            fallback_family,
                            response_structure,
                            generated_for_entry + fallback_index + structure_index,
                        )
                        if example is None:
                            continue
                        examples.append(example)
                        scenario_counts[fallback_family] += 1
                        structure_counts[response_structure] += 1
                        self._distilled_counts[teaching_key] += 1
                        generated_for_entry += 1
                        if (
                            generated_for_entry >= target_examples
                            or self._distilled_counts[teaching_key] >= MAX_DISTILLED_WISDOM_EXAMPLES
                        ):
                            break

            if generated_for_entry == 0:
                skipped_entries += 1

        return ExpandedDatasetResult(
            examples=examples,
            scenario_counts=scenario_counts,
            structure_counts=structure_counts,
            opening_counts=self._opening_counts,
            action_counts=self._action_counts,
            duplicate_prompts=self._duplicate_prompts,
            duplicate_responses=self._duplicate_responses,
            skipped_entries=skipped_entries,
        )

    def _dedupe_source_entries(self, entries: list[WisdomEntry]) -> list[WisdomEntry]:
        grouped: dict[str, WisdomEntry] = {}
        for entry in entries:
            key = self._normalize_key(entry.distilled_wisdom or "")
            current = grouped.get(key)
            if current is None:
                grouped[key] = entry
                continue

            current_tag_count = len(self._normalized_tags(current))
            candidate_tag_count = len(self._normalized_tags(entry))
            current_quality = float(current.principle_quality_score or 0)
            candidate_quality = float(entry.principle_quality_score or 0)
            current_confidence = float(current.confidence_score or 0)
            candidate_confidence = float(entry.confidence_score or 0)

            if (
                candidate_tag_count > current_tag_count
                or (candidate_tag_count == current_tag_count and candidate_quality > current_quality)
                or (
                    candidate_tag_count == current_tag_count
                    and candidate_quality == current_quality
                    and candidate_confidence > current_confidence
                )
            ):
                grouped[key] = entry

        return list(sorted(grouped.values(), key=lambda item: (item.source_document_id, item.id)))

    def _select_scenario_families(self, entry: WisdomEntry) -> list[str]:
        tags = self._normalized_tags(entry)
        scored: list[tuple[int, str]] = []
        for family in SCENARIO_FAMILIES:
            phil_tags, emo_tags = SCENARIO_TAG_RULES[family]
            score = len(tags & phil_tags) * 3 + len(tags & emo_tags) * 2
            if family == "career" and GITA_BOOK_PATTERN.search((entry.book_title or "").lower()):
                score += 2
            if family == "purpose" and (entry.book_title or "").lower() in UPANISHAD_BOOKS:
                score += 2
            if family == "inner_conflict":
                score += 1
            scored.append((score, family))

        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
        chosen = [family for score, family in scored if score > 0][:4]
        if len(chosen) < 4:
            for fallback in ["inner_conflict", "purpose", "discipline", "attachment", "career"]:
                if fallback not in chosen:
                    chosen.append(fallback)
                if len(chosen) == 4:
                    break
        return chosen[:4]

    def _structure_candidates(self, entry: WisdomEntry, family: str, offset: int) -> list[str]:
        options = SCENARIO_STRUCTURE_MAP[family]
        start = (entry.id + offset) % len(options)
        return [options[(start + index) % len(options)] for index in range(len(options))]

    def _build_example(
        self,
        entry: WisdomEntry,
        scenario_family: str,
        response_structure: str,
        variant_index: int,
    ) -> GeneratedDatasetExample | None:
        teaching = self._clean_teaching(entry.distilled_wisdom or "")
        if not teaching:
            return None

        prompts = self._build_user_prompt_candidates(entry, scenario_family, variant_index)
        for prompt_index, prompt in enumerate(prompts):
            prompt_key = self._normalize_key(prompt)
            if prompt_key in self._prompt_keys:
                continue

            assistant_payload = self._build_assistant_response(
                entry=entry,
                scenario_family=scenario_family,
                response_structure=response_structure,
                teaching=teaching,
                prompt=prompt,
                variant_index=variant_index + prompt_index,
            )
            if assistant_payload is None:
                continue

            assistant, opening_key, action_key = assistant_payload
            response_key = self._normalize_key(assistant)
            if response_key in self._response_keys:
                continue

            self._prompt_keys.add(prompt_key)
            self._response_keys.add(response_key)
            self._opening_counts[opening_key] += 1
            self._action_counts[action_key] += 1

            record = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": assistant},
                ]
            }

            return GeneratedDatasetExample(
                wisdom_entry_id=entry.id,
                source_document_id=entry.source_document_id,
                book_title=entry.book_title or "",
                distilled_wisdom=teaching,
                scenario_family=scenario_family,
                response_structure=response_structure,
                user_prompt=prompt,
                assistant_response=assistant,
                record=record,
            )

        self._duplicate_prompts += 1
        self._duplicate_responses += 1
        return None

    def _build_user_prompt_candidates(self, entry: WisdomEntry, family: str, variant_index: int) -> list[str]:
        templates = SCENARIO_TEMPLATES[family]
        contexts = SCENARIO_CONTEXTS[family]
        tails = PROMPT_TAILS[family]
        prompts: list[str] = []
        seen: set[str] = set()
        total = len(templates) * len(contexts) * len(tails)
        for attempt in range(total):
            template = templates[(entry.id + variant_index + attempt) % len(templates)]
            context = contexts[(entry.id + (attempt * 2)) % len(contexts)]
            tail = tails[(entry.id + (attempt * 3)) % len(tails)]
            prompt = f"{template} {context} {tail}"
            key = self._normalize_key(prompt)
            if key in seen:
                continue
            prompts.append(prompt)
            seen.add(key)
        return prompts

    def _build_assistant_response(
        self,
        entry: WisdomEntry,
        scenario_family: str,
        response_structure: str,
        teaching: str,
        prompt: str,
        variant_index: int,
    ) -> tuple[str, str, str] | None:
        tags = self._normalized_tags(entry)
        for attempt in range(24):
            seed = entry.id + variant_index + attempt
            opening = self._choose_opening(response_structure, scenario_family, tags, seed)
            if opening is None:
                continue
            lesson = self._choose_application_sentence(response_structure, teaching, seed)
            action = self._choose_action_sentence(scenario_family, seed)
            if action is None:
                continue
            bridge = self._choose_bridge_sentence(scenario_family, seed)
            closing = self._choose_closing(response_structure, seed)

            built = self._compose_response(
                response_structure=response_structure,
                opening=opening,
                lesson=lesson,
                bridge=bridge,
                action=action,
                closing=closing,
                prompt=prompt,
            )
            built = self._polish_response(built)
            built = self._fit_length(built)
            if not self._validate_response(built):
                continue

            opening_key = self._first_sentence(built)
            if self._opening_counts[opening_key] >= MAX_OPENING_REPETITIONS:
                continue

            response_key = self._normalize_key(built)
            if response_key in self._response_keys:
                continue
            return built, opening_key, action
        return None

    def _compose_response(
        self,
        response_structure: str,
        opening: str,
        lesson: str,
        bridge: str,
        action: str,
        closing: str,
        prompt: str,
    ) -> str:
        question = self._build_guiding_question(prompt)
        metaphor = self._build_metaphor(prompt)

        if response_structure == "reflection_action":
            parts = [opening, lesson, bridge, action, closing]
        elif response_structure == "direct_clarity":
            parts = [lesson, opening, bridge, action, closing]
        elif response_structure == "question_guided":
            parts = [opening, question, lesson, bridge, action, closing]
        elif response_structure == "short_grounding":
            parts = [opening, lesson, bridge, action]
        elif response_structure == "metaphor_based":
            parts = [opening, metaphor, lesson, bridge, action, closing]
        elif response_structure == "action_first":
            parts = [action, lesson, bridge, closing]
        elif response_structure == "inner_dialogue":
            parts = [opening, self._build_inner_dialogue_sentence(prompt), lesson, bridge, action, closing]
        elif response_structure == "decision_filter":
            parts = [opening, self._build_decision_filter_sentence(prompt), lesson, bridge, action, closing]
        elif response_structure == "habit_correction":
            parts = [opening, self._build_habit_sentence(prompt), lesson, bridge, action, closing]
        elif response_structure == "surrender_detachment":
            parts = [opening, self._build_detachment_sentence(prompt), lesson, bridge, action, closing]
        else:
            parts = [opening, lesson, bridge, action, closing]
        return " ".join(part.strip() for part in parts if part and part.strip())

    def _choose_opening(self, structure: str, family: str, tags: set[str], seed: int) -> str | None:
        openings = OPENINGS[structure]
        tails = OPENING_TAILS[family]
        tag_fragments = self._tag_opening_fragments(tags)
        total = len(openings) * len(tails) * len(tag_fragments)
        for attempt in range(total):
            opening = openings[(seed + attempt) % len(openings)]
            tail = tails[((seed // max(1, len(openings))) + attempt) % len(tails)]
            tag_fragment = tag_fragments[((seed // max(1, len(tails))) + attempt) % len(tag_fragments)]
            candidate = f"{self._strip_period(opening)}, {self._strip_leading_marker(tail)} {tag_fragment}".strip()
            candidate = self._polish_response(candidate)
            if self._opening_counts[candidate] < MAX_OPENING_REPETITIONS:
                return candidate
        return None

    def _choose_application_sentence(self, structure: str, teaching: str, seed: int) -> str:
        patterns = APPLICATION_PATTERNS[structure]
        template = patterns[seed % len(patterns)]
        teaching_fragment = teaching[0].lower() + teaching[1:] if teaching and teaching[0].isupper() else teaching
        return template.format(teaching=teaching_fragment.rstrip("."))

    def _choose_action_sentence(self, family: str, seed: int) -> str | None:
        actions = ACTION_BANKS[family]
        suffixes = ACTION_SUFFIXES[family]
        total = len(actions) * len(suffixes)
        for attempt in range(total):
            action = actions[(seed + attempt) % len(actions)]
            suffix = suffixes[((seed // max(1, len(actions))) + attempt) % len(suffixes)]
            candidate = f"{action} {suffix}".strip()
            candidate = self._polish_response(candidate)
            if self._action_counts[candidate] < MAX_ACTION_REPETITIONS:
                return candidate
        return None

    def _choose_closing(self, structure: str, seed: int) -> str:
        closings = CLOSINGS[structure]
        return closings[seed % len(closings)]

    def _choose_bridge_sentence(self, family: str, seed: int) -> str:
        bridges = RESPONSE_BRIDGES[family]
        return bridges[seed % len(bridges)]

    def _build_guiding_question(self, prompt: str) -> str:
        if "relationship" in prompt.lower() or "person" in prompt.lower():
            return "What response would still feel honest to you after the emotion settles?"
        if "work" in prompt.lower() or "career" in prompt.lower():
            return "What is the next action that would still feel clean even if the outcome stays uncertain?"
        return "What becomes clearer when you stop asking the whole future to settle before the next honest step?"

    def _build_metaphor(self, prompt: str) -> str:
        if "change" in prompt.lower() or "fear" in prompt.lower():
            return "A mind under pressure can behave like a compass near a magnet, still capable of direction but temporarily pulled away from what is true."
        if "discipline" in prompt.lower() or "habit" in prompt.lower():
            return "A life changes through repeated turns, much like a path becomes visible by walking it again and again."
        return "The inner life can become like water disturbed by wind, where forcing it harder rarely makes it clearer."

    def _build_inner_dialogue_sentence(self, prompt: str) -> str:
        if "comfort" in prompt.lower():
            return "One voice in you wants relief now, while another wants to remain aligned with what is right."
        if "fear" in prompt.lower():
            return "One inner voice is trying to protect you from discomfort, while another still knows you do not need fear to lead."
        return "Usually there is a reacting voice and a steadier voice present at the same time, and they should not be trusted equally."

    def _build_decision_filter_sentence(self, prompt: str) -> str:
        if "work" in prompt.lower() or "career" in prompt.lower():
            return "Try filtering the decision through one question: which option stays honest even if it does not soothe your anxiety immediately?"
        return "Try filtering the decision through one question: what stays true when urgency and imagined consequences become quieter?"

    def _build_habit_sentence(self, prompt: str) -> str:
        if "discipline" in prompt.lower() or "habit" in prompt.lower():
            return "What needs attention here is not only the intention, but the exact point where the old pattern starts taking over."
        return "Patterns change most reliably when they are interrupted early instead of argued with after they have already won the moment."

    def _build_detachment_sentence(self, prompt: str) -> str:
        if "relationship" in prompt.lower():
            return "The strain often comes from trying to hold on to the response you want from someone else instead of holding to your own honesty."
        return "The pressure often comes from gripping too tightly around an outcome that was never fully yours to command."

    def _tag_opening_fragments(self, tags: set[str]) -> list[str]:
        fragments = ["Stay close to the human part of it instead of only the mental pressure."]
        if {"fear", "grief", "death"} & tags:
            fragments.append("Fear does not have to be the part that defines the whole situation.")
        if {"attachment", "desire", "detachment"} & tags:
            fragments.append("Pressure usually rises when the heart starts gripping harder than it needs to.")
        if {"discipline", "self_control", "self-control", "restlessness"} & tags:
            fragments.append("A steadier pattern is still possible even if the old impulse has been winning lately.")
        if {"purpose", "self_knowledge", "non_duality", "atman", "brahman"} & tags:
            fragments.append("A deeper center is still available even when surface thinking gets loud.")
        if {"trust", "inner_steadiness"} & tags:
            fragments.append("You do not have to wait for total certainty before returning to steadier ground.")
        return fragments

    def _strip_period(self, text: str) -> str:
        return text.strip().rstrip(".!?")

    def _strip_leading_marker(self, text: str) -> str:
        return text.strip()[:1].lower() + text.strip()[1:] if text.strip() else text.strip()

    def _polish_response(self, response: str) -> str:
        response = re.sub(r"\s+", " ", response).strip()
        response = response.replace("..", ".")
        response = re.sub(r"\s+([,.!?])", r"\1", response)
        return response

    def _fit_length(self, response: str) -> str:
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", response.strip()) if part.strip()]
        while sentences and self._word_count(" ".join(sentences)) > 140:
            sentences.pop()
        if not sentences:
            return response
        if self._word_count(" ".join(sentences)) < 70 and len(sentences) >= 2:
            rebuilt = " ".join(sentences)
            return self._polish_response(rebuilt)
        return self._polish_response(" ".join(sentences))

    def _validate_response(self, response: str) -> bool:
        if LISTICLE_PATTERN.search(response):
            return False
        if SCRIPTURE_LEAK_PATTERN.search(response):
            return False
        if SANSKRIT_PATTERN.search(response):
            return False
        if response.count(";") > 0:
            return False
        if "You do not need perfect certainty to begin. you only need" in response:
            return False
        words = self._word_count(response)
        if words < 70 or words > 140:
            return False
        if self._first_sentence(response).lower().count("calm") > 1:
            return False
        return True

    def _clean_teaching(self, text: str) -> str:
        cleaned = re.sub(r"\s+", " ", (text or "").strip())
        cleaned = cleaned.rstrip(".")
        return cleaned

    def _normalized_tags(self, entry: WisdomEntry) -> set[str]:
        raw_tags = list(entry.emotional_tags or []) + list(entry.philosophical_tags or [])
        normalized = {
            tag.strip().lower().replace("-", "_")
            for tag in raw_tags
            if isinstance(tag, str) and tag.strip()
        }
        return normalized

    def _normalize_key(self, text: str) -> str:
        lowered = re.sub(r"\s+", " ", text.strip().lower())
        lowered = re.sub(r"[^\w\s]", "", lowered)
        return lowered.strip()

    def _first_sentence(self, text: str) -> str:
        match = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)
        return match[0].strip()

    def _word_count(self, text: str) -> int:
        return len(re.findall(r"\b[\w']+\b", text))

    def build_jsonl(self, result: ExpandedDatasetResult, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            for index, example in enumerate(result.examples):
                handle.write(json.dumps(example.record, ensure_ascii=False))
                if index != len(result.examples) - 1:
                    handle.write("\n")

    def build_report(self, result: ExpandedDatasetResult, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Expanded v1 Generation Report",
            "",
            f"- total generated: {len(result.examples)}",
            f"- skipped source entries: {result.skipped_entries}",
            f"- duplicate prompts blocked: {result.duplicate_prompts}",
            f"- duplicate responses blocked: {result.duplicate_responses}",
            "",
            "## Scenario Counts",
            "",
        ]
        for family, count in result.scenario_counts.most_common():
            lines.append(f"- {family}: {count}")
        lines.extend(["", "## Response Structure Counts", ""])
        for structure, count in result.structure_counts.most_common():
            lines.append(f"- {structure}: {count}")
        lines.extend(["", "## Repeated Openings", ""])
        for opening, count in result.opening_counts.most_common(20):
            lines.append(f"- {count}x {opening}")
        lines.extend(["", "## Repeated Actions", ""])
        for action, count in result.action_counts.most_common(20):
            lines.append(f"- {count}x {action}")
        lines.extend(["", "## Sample Examples", ""])
        for example in result.examples[:20]:
            lines.append(f"- wisdom_entry_id: {example.wisdom_entry_id}")
            lines.append(f"  source: {example.book_title}")
            lines.append(f"  scenario_family: {example.scenario_family}")
            lines.append(f"  response_structure: {example.response_structure}")
            lines.append(f"  user: {example.user_prompt}")
            lines.append(f"  assistant: {example.assistant_response}")
            lines.append("")
        output_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

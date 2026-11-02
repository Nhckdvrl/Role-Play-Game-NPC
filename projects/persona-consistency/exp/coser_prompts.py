"""Prompt text of the CoSER GCA evaluation (Wang et al., ICML 2025; github.com/Neph0s/CoSER, gca_evaluation/),
copied verbatim as data after review, plus re-implementations of the prompt builders and parsers used by its main.py
(get_character_prompt with fixed_template=True, get_environment_prompt, get_nsp_prompt, extract_nsp,
remove_inner_thoughts, add_speaker_name, extract_json without the LLM json-fixing fallback)."""
import re, json

critic_prompts = {
    "self-play-deduct-template": """You are a literary critic specializing in character analysis and dialogue evaluation. Given a simulated conversation for a plot in {book}, your task is to evaluate this conversation via the following steps:

1. Read and understand the provided materials about {book}:
   * Story context and scenario.
   * Profiles of the main characters, including {major_characters}.
   * The original conversation from {book} in the same scenario as a reference.

  2. Evaluate the simulated conversation in terms of {dimension_name}, i.e., {dimension_brief}. 
   Note that, each character message is composed of speech, action (wrapped within (...) ), and inner thoughts (wrapped within [...] ). The inner thoughts are not spoken aloud and are thus invisible to other characters. 
   The detailed evaluation criteria will be provided below.
   {additional_instructions}

## Scenario

### Plot Summary

{plot_summary}

### Current Scenario

{scenario}

## Character Profiles

{character_profiles}

## Original Conversation

{original_conversation}

## Evaluation Criteria

To evaluate the simulated conversation, identify the following types of flaws:

{dimension_criteria}

## Scoring Guidelines

1. Identify all instances of flaws occurred in the simulated conversation.
      
2. For each flaw identified, determine its level of severity into 1 to 5, where 1 indicates minor, 3 indicates moderate, and 5 indicates severe.
   
## Output Requirements

Provide your evaluation in JSON format:

Example Output:
{
    "{dimension_name}": {
        "flaws": [ 
          {
            "instance": <comment on the flaw instance>, 
            "type": <flaw type>, 
            "severity": <range from 1 (minor) to 5 (severe)>
          },
    },
}
===Dialogue Content===
""",
  "dimension_details": {
      "Storyline Consistency": {
        "dimension_brief": "Whether the storyline and characters' reactions in the simulated conversation align well with those in the reference conversation",
        "dimension_criteria": """### Storyline Consistency
   - Type: Storyline Consistency
     * Characters' reactions (emotions, attitudes, behaviors) in the simulated conversation deviate from those in the original conversation"""
      },
      "Anthropomorphism": {
        "dimension_brief": "How human-like and natural the characters behave",
        "dimension_criteria": """### Anthropomorphism
   - Type: Self-identity
     * Lacks initiative and goals
     * Does not make independent decisions
     * Lacks clear preferences and dislikes
     * Behaves like a 'helpful AI assistant' by being overly verbose, helpful, didactic, moralistic, submissive or easily persuaded if it is not the character's personality

   - Type: Emotional Depth
     * Lacks psychological complexity and exhibits rigid, superficial reactions
     * Directly speaks out all thoughts and feelings, instead of using subtext

   - Type: Persona Coherence
     * Shows inconsistent or rapidly changing personality traits and emotional patterns

   - Type: Social Interaction
     * Shows a lack of understanding of others' thoughts and feelings
     * Reacts rigidly to others without considering the context.
     * Demonstrate a lack of appropriate social skills."""
      },
      "Character Fidelity": {
        "dimension_brief": "How well the characters match their established profiles from the book",
        "dimension_criteria": """### Character Fidelity
   (Only apply to the main characters: {major_characters})
   - Type: Character Language
     * Uses vocabulary, expressions, and tone that are not appropriate for the characters' traits or  social/educational background

   - Type: Knowledge & Background
     * Fails to demonstrate character-specific knowledge, background or experiences
     * Includes future information beyond the character's current stage

   - Type: Personality & Behavior
     * Shows emotions, thoughts, behaviors, values, beliefs, and decisions that conflict with their personality and background
     * Shows interest in topics that are uninteresting and unrelated to the character
     * Character's thoughts, emotions, and behaviors demonstrate contrasting personality traits compared to the reference conversation
     * Exhibits contrasting reactions compared to those in the reference conversation if situated in similar contexts. (Such flaws should be counted both in the "Storyline Consistency" dimension and the "Character Fidelity" dimension.) 

   - Type: Relationship & Social Status
     * Interacts inappropriately with other characters regarding their background, relationship and social status"""
      },
      "Storyline Quality": {
        "dimension_brief": "How well the conversation maintains logical consistency and narrative quality",
        "dimension_criteria": """### Storyline Quality
   - Type: Flow & Progression
     * Shows unnatural progression or lacks meaningful developments
     * Dialogue is verbose and redundant
     * Repeats others' viewpoints or previously mentioned information
     * Mechanically repeats one's own words or phrases. More repetitions lead to higher severity (up to 10). 

   - Type: Logical Consistency
     * Contains factual contradictions between statements or perspectives"""
      }
  }
}


def remove_inner_thoughts(dialogue):
    d = re.sub(r"\[.*?\]", "", dialogue)
    d = "\n".join(line.strip() for line in d.split("\n"))
    d = re.sub(r"\n+", "\n", d)
    d = re.sub(r"\s*<\s*system[_\s]+think(?:ing)?\s*>.*?</\s*system[_\s]+think(?:ing)?\s*>\s*", "", d, flags=re.S).strip()
    d = re.sub(r"\s*<\s*role[_\s]+think(?:ing)?\s*>.*?</\s*role[_\s]+think(?:ing)?\s*>\s*", "", d, flags=re.S).strip()
    d = re.sub(r"\s*<\s*[_\s]+think(?:ing)?\s*>.*?</\s*[_\s]+think(?:ing)?\s*>\s*", "", d, flags=re.S).strip()
    return d.strip()


def add_speaker_name(dialogue, speaker):
    if any(l.strip().startswith(f"{speaker}:") or l.strip().startswith(f"{speaker}：") for l in dialogue.split("\n")):
        return dialogue
    return f"{speaker}: {dialogue}"


def get_character_prompt(book_name, character, character_profile, scenario, motivation, other_character_profiles, rng):
    output_format = ("Your output should include **thought**, **speech**, and **action**. Use [your thought] for thoughts, which others "
                     "can't see, e.g. [I'm terrified, but I must appear strong.]. Use (your action) for actions, which others can see, "
                     "such as (watches silently, trying to control her fear and anger).")
    other = ""
    if other_character_profiles:
        decorator = rng.choice(["*" * 30 + "\n\n", "*" * 20 + "\n\n", "\n\n", "\n", ""])
        for oc, profile in other_character_profiles.items():
            if oc != character:
                other += f"{decorator}{oc}: {profile}\n\n"
    if motivation:
        motivation = f"===Your Inner Thoughts===\n{motivation}\n\n"
    if other:
        other = f"===Information about the other Characters===\n{other}\n\n"
    p = f"You are {character} from {book_name}.\n\n==={character}'s Profile===\n{character_profile}\n\n===Current Scenario===\n{scenario}\n\n{other}{motivation}\n\n"
    return p + f"===Requirements===\n{output_format}\n\n"


def get_environment_prompt(major_characters, scenario, rng):
    major_characters = [c for c in major_characters if c != "Environment"]
    role = rng.choice(["an environment model", "a world model", "a world simulator", "an environment simulator"])
    return f"""You are {role} for a role-playing game. Your task is to provide the environmental feedback: Based on the characters' interactions, dialogues, and actions, describe the resulting changes in the environment. This includes:
   - Physical changes in the setting
   - Reactions of background characters or crowds
   - Ambient sounds, weather changes, or atmospheric shifts
   - Any other relevant environmental details

Your descriptions should be vivid and help set the scene, but avoid dictating the actions or dialogue of the main characters (including {major_characters}).

Important notes:
- You may include actions and reactions of minor characters or crowds, as long as they're not main characters (including {major_characters}).
- Keep your environmental descriptions concise but impactful, typically 1-3 sentences.
- Respond to subtle cues in the characters' interactions to create a dynamic, reactive environment.
- Your output should match the tone, setting, and cultural context of the scenario.

===The scenario is as follows===
{scenario}"""


def get_nsp_prompt(all_characters, scenario):
    return f"""Your task is to predict the next speaker for a role-playing game. That is, you need to determine which character (or the Environment) might act next based on their previous interactions. The Environment is a special role that provides the environmental feedback. Choose a name from this list: {all_characters}. If it's unclear who should act next, output "random". If you believe the scene or conversation should conclude, output "<END CHAT>".

===The scenario is as follows===
{scenario}

===Output Format===
You must structure your response as follows:
1. Reasoning: Explain your thought process.
2. Next Speaker: Select exactly one character name from the list: {all_characters}.
"""


def extract_nsp(response):
    m = re.findall(r"(?:\*\*|#)?\s*Next\s+Speaker\s*(?:\*\*|#)?\s*(?:[:\-]|\bis\b)?\s*\*?([^\n\*]+)", response, re.IGNORECASE)
    if m:
        name = m[-1].strip().rstrip('.,!"\'').replace("*", "")
        if name:
            return name
    return None


def extract_json(text):
    text = re.sub(r'"([^"\\]*(\\.[^"\\]*)*)"', lambda m: m.group().replace("\n", r"\\n"), text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        res, start = [], 0
        while start < len(text):
            try:
                obj, end = json.JSONDecoder().raw_decode(text[start:])
                res.append(obj)
                start += end
            except json.JSONDecodeError:
                start += 1
        return max(res, key=lambda x: len(json.dumps(x))) if res else None

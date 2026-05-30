# placeholder: generator.py
"""
Question generator for the interview flow.

- Template-based generation from parsed resume and optional role profile.
- Optional LLM expansion if `OPENAI_API_KEY` is present in settings (keeps dependency optional).
- Exposes `generate_questions(parsed, role_profile, max_questions)` returning a list of Question objects.
"""

from typing import List, Optional, Dict
import uuid
import os

from ..core.schemas import Question, ParsedResume
from ..core.config import settings

# Simple templates ordered by depth
_TEMPLATES = [
    "Describe a project where you used {skill}. What was the challenge and outcome?",
    "Walk me through a complex problem you solved using {skill}. What design tradeoffs did you consider?",
    "How did you measure success for your work involving {skill}?",
    "What tools, libraries or frameworks did you use with {skill} and why?",
]

# Fallback behavioral templates
_BEHAVIORAL = [
    "Tell me about a time you overcame a difficult technical challenge (STAR).",
    "Describe a time you had to collaborate with a difficult stakeholder and how you handled it.",
]

# Optional: simple OpenAI LLM expansion (kept optional)
def _expand_with_llm(prompt: str, n: int = 2) -> List[str]:
    api_key = os.environ.get("OPENAI_API_KEY") or settings.OPENAI_API_KEY
    if not api_key:
        return []
    try:
        import openai
        openai.api_key = api_key
        resp = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=200,
            n=n,
            temperature=0.7,
        )
        questions = []
        for choice in resp.choices:
            text = choice.text.strip()
            if text:
                # split into lines and take lines that look like questions
                for line in text.splitlines():
                    if line.strip():
                        questions.append(line.strip().rstrip("?") + "?")
        return questions
    except Exception:
        return []


def _make_question(text: str, skill: Optional[str] = None, expected_keywords: Optional[List[str]] = None, weight: float = 1.0) -> Question:
    return Question(
        question_id=str(uuid.uuid4()),
        text=text,
        skill=skill,
        expected_keywords=expected_keywords or ([skill] if skill else []),
        weight=weight,
    )


def generate_questions(parsed: ParsedResume, role_profile: Optional[Dict] = None, max_questions: int = 5) -> List[Question]:
    """
    Generate a list of `Question` objects from a ParsedResume and optional role profile.

    Args:
      parsed: ParsedResume instance
      role_profile: optional dict with keys like {'skills': [...], 'priority_skills': [...]} to bias questions
      max_questions: maximum number of questions to return

    Returns:
      List[Question]
    """
    skills = []
    if role_profile:
        # prefer role_profile.skills then parsed.skills
        rp_skills = role_profile.get("skills") or []
        skills = rp_skills + [s for s in parsed.skills if s not in rp_skills]
    else:
        skills = parsed.skills or []

    questions: List[Question] = []

    # Primary skill-focused questions
    for i, skill in enumerate(skills):
        if len(questions) >= max_questions:
            break
        tmpl = _TEMPLATES[i % len(_TEMPLATES)]
        text = tmpl.format(skill=skill)
        weight = 2.0 if i == 0 else 1.0
        q = _make_question(text, skill=skill, expected_keywords=[skill], weight=weight)
        questions.append(q)

    # If not enough questions, add behavioral ones
    bi = 0
    while len(questions) < max_questions and bi < len(_BEHAVIORAL):
        questions.append(_make_question(_BEHAVIORAL[bi], skill="behavioral", expected_keywords=["challenge", "action", "result"], weight=1.5))
        bi += 1

    # Optionally expand with LLM for variety
    if len(questions) < max_questions and settings.LLM_PROVIDER and (os.environ.get("OPENAI_API_KEY") or settings.OPENAI_API_KEY):
        prompt = "Generate concise interview questions (one per line) based on the following skills: " + ", ".join(skills[:5])
        extra = _expand_with_llm(prompt, n=(max_questions - len(questions)))
        for ex in extra:
            if len(questions) >= max_questions:
                break
            questions.append(_make_question(ex, skill=None, expected_keywords=[]))

    # Trim to max_questions
    return questions[:max_questions]
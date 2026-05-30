# placeholder: __init__.py
from .generator import generate_questions
from .models import RoleProfile
from .prompts import PROMPT_V1, PROMPT_EXAMPLES

__all__ = ["generate_questions", "RoleProfile", "PROMPT_V1", "PROMPT_EXAMPLES"]
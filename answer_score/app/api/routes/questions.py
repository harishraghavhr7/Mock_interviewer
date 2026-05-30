# placeholder: questions.py
from fastapi import APIRouter, HTTPException
from typing import List, Optional

from ...core.schemas import ParsedResume, Question
from ...question_generator.generator import generate_questions

router = APIRouter(prefix="/questions", tags=["questions"])


@router.post("/generate", response_model=List[Question])
def api_generate(parsed: ParsedResume, max_questions: Optional[int] = 5):
    try:
        qs = generate_questions(parsed, max_questions=max_questions)
        return qs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"question generation error: {e}")
# placeholder: __init__.py
from fastapi import APIRouter

from .routes.sessions import router as sessions_router
from .routes.questions import router as questions_router
from .routes.transcripts import router as transcripts_router
from .routes.evaluations import router as evaluations_router

router = APIRouter()
router.include_router(sessions_router)
router.include_router(questions_router)
router.include_router(transcripts_router)
router.include_router(evaluations_router)

__all__ = ["router"]
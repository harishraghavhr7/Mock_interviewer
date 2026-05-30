# placeholder: schemas.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr


class Experience(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    start: Optional[str] = None  # ISO date or free text
    end: Optional[str] = None
    description: Optional[str] = None


class Education(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    description: Optional[str] = None


class ParsedResume(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    headline: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    raw_text: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class Question(BaseModel):
    question_id: str
    text: str
    skill: Optional[str] = None
    difficulty: Optional[str] = "medium"
    expected_keywords: List[str] = Field(default_factory=list)
    weight: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TranscriptSegment(BaseModel):
    start: float  # seconds
    end: float  # seconds
    speaker: str  # "candidate" | "interviewer" | speaker id
    text: str


class QuestionEvaluation(BaseModel):
    question_id: str
    semantic_sim: float
    keyword_score: float
    time_sec: float
    final_score: float
    comments: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class FinalReport(BaseModel):
    final_score: float
    per_skill: Dict[str, float] = Field(default_factory=dict)
    recommendation: str
    notes: List[str] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict)


class SessionRecord(BaseModel):
    session_id: str
    resume: ParsedResume
    questions: List[Question]
    transcripts: List[TranscriptSegment] = Field(default_factory=list)
    evaluations: List[QuestionEvaluation] = Field(default_factory=list)
    report: Optional[FinalReport] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
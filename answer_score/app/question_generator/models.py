# placeholder: models.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class RoleProfile(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    skills: List[str] = []
    priority_skills: List[str] = []
    metadata: Dict[str, Any] = {}
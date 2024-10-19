from pydantic import BaseModel
from typing import Optional

class GradeWithDescription(BaseModel):
    value: Optional[float]
    description: str

class StartupBase(BaseModel):
    name: str
    github_url: str

class StartupCreate(StartupBase):
    pass

class StartupInDB(StartupBase):
    id: int
    github_grade: Optional[float] = None
    presentation_grade: Optional[float] = None
    novelty_grade: Optional[float] = None

    class Config:
        orm_mode = True

class StartupGradingResponse(BaseModel):
    id: int
    name: str
    github_url: str
    github_grade: GradeWithDescription
    presentation_grade: GradeWithDescription
    novelty_grade: GradeWithDescription

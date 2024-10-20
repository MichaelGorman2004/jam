from pydantic import BaseModel
from typing import Optional
import io
from app.services.github_services import GithubCodeEvaluator
from app.services.presentation_services import PresentationEvaluator
from app.services.web_scraper import NoveltyEvaluator
import json

class Startup(BaseModel):
    id: Optional[int] = None
    name: str
    github_url: str
    presentation_video: bytes
    presentation_pdf: bytes
    github_grade: Optional[float] = None
    presentation_grade: Optional[float] = None
    novelty_grade: Optional[float] = None
    github_description: Optional[str] = None
    presentation_description: Optional[str] = None
    novelty_description: Optional[str] = None

    @classmethod
    async def create_and_grade(cls, startup_data):
        startup = cls(**startup_data.dict())
        await startup.grade()
        return startup

    async def grade(self):
        # Grade GitHub repository
        github_evaluator = GithubCodeEvaluator()
        github_result = json.loads(github_evaluator.evaluate_repository(self.github_url))
        self.github_grade = github_result['overall_score']
        self.github_description = github_result['summary']

        # Grade presentation
        presentation_evaluator = PresentationEvaluator()
        presentation_result = json.loads(presentation_evaluator.process_presentation(
            self.presentation_pdf,
            self.presentation_video
        ))
        self.presentation_grade = (presentation_result['slides_evaluation']['score'] + 
                                   presentation_result['pitch_evaluation']['overall_score']) / 2
        self.presentation_description = presentation_result['pitch_evaluation']['summary']

        # Grade novelty
        novelty_evaluator = NoveltyEvaluator()
        novelty_result = novelty_evaluator.evaluate_novelty(
            self.github_url,
            False,  # Assuming presentation_video is an MP4 file
            io.BytesIO(self.presentation_video)
        )
        self.novelty_grade = novelty_result['overall_score']
        self.novelty_description = (f"GitHub Summary: {novelty_result['github_summary']}\n"
                                    f"Google Summary: {novelty_result['google_summary']}")

    def get_github_grade_description(self):
        return self.github_description or "GitHub repository has not been graded yet."

    def get_presentation_grade_description(self):
        return self.presentation_description or "Presentation has not been graded yet."

    def get_novelty_grade_description(self):
        return self.novelty_description or "Novelty has not been evaluated yet."

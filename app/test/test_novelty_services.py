import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.novelty_services import NoveltyEvaluator

evaluator = NoveltyEvaluator()  # Create an instance of the class

response = evaluator.evaluate_novelty(
    project_repo_url='https://github.com/Paktion/asthmapredictor',
    audio=False,
    presentation_file_path='./Hackathon2023 - Nikhil Kumar.mp4'
)

print(response)

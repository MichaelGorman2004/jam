import os
import logging
from dotenv import load_dotenv
from app.services.github_services import GithubCodeEvaluator

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_github_evaluator():
    # Create an instance of GithubCodeEvaluator
    evaluator = GithubCodeEvaluator()

    # GitHub repository URL to evaluate
    repo_url = "https://github.com/openai/openai-python"  # Example: OpenAI's Python client

    try:
        # Evaluate the repository
        result = evaluator.evaluate_repository(repo_url)

        # Print the results
        print(f"Repository: {repo_url}")
        print(f"Code Quality Grade: {result['code_quality_grade']}")
        print(f"Tech Stack Grade: {result['tech_stack_grade']}")
        print("\nSummary:")
        print(result['summary'])

    except Exception as e:
        logging.exception("An error occurred:")

if __name__ == "__main__":
    test_github_evaluator()

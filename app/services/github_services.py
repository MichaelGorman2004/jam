# Import necessary libraries
import requests
from github import Github
from urllib.parse import urlparse, quote_plus
import openai
import os
import json
from typing import Dict, Tuple, List, Any
import logging

class GithubCodeEvaluator:
    def __init__(self):
        # Initialize GitHub client with token from environment variable
        # GitHub API token for authentication (e.g., "ghp_1234567890abcdef")
        self.github: Github = Github(os.getenv('GITHUB_TOKEN'))

        # Set OpenAI API key from environment variable
        # OpenAI API key for authentication (e.g., "sk-1234567890abcdef")
        openai.api_key = os.getenv('OPENAI_API_KEY')

    def evaluate_repository(self, repo_url: str) -> str:
        """
        Evaluate a GitHub repository for code quality and tech stack.

        Args:
            repo_url (str): The URL of the GitHub repository to evaluate.

        Returns:
            str: A JSON-formatted string containing the evaluation results:
                - structure_grade (float): The overall structure grade (0-100).
                - code_quality_grade (float): The code quality grade (0-100).
                - security_grade (float): The security grade (0-100).
                - documentation_grade (float): The documentation grade (0-100).
                - efficiency_grade (float): The efficiency grade (0-100).
                - tech_stack_grade (float): The tech stack grade (0-100).
                - code_quality_explanation (str): Explanation of the code quality grade.
                - security_explanation (str): Explanation of the security grade.
                - documentation_explanation (str): Explanation of the documentation grade.
                - efficiency_explanation (str): Explanation of the efficiency grade.
                - tech_stack (List[str]): List of technologies used in the project.
                - summary (str): A text summary of the evaluation without numerical scores.

        Raises:
            ValueError: If the repository URL is invalid or the repository is not accessible.
        """
        owner, repo_name = self._parse_github_url(repo_url)
        repo = self.github.get_repo(f"{owner}/{repo_name}")
        
        structure_analysis = self._analyze_repo_structure(repo)
        important_files = self._get_important_files(repo)
        code_content = self._fetch_important_content(repo, important_files)
        
        code_evaluation = self._evaluate_code_with_openai(structure_analysis, code_content)
        tech_stack = self._evaluate_tech_stack(repo)
        
        summary = self._generate_summary(code_evaluation, tech_stack)
        
        result = {
            "structure_grade": code_evaluation['structure_grade'],
            "code_quality_grade": code_evaluation['code_quality']['rating'],
            "security_grade": code_evaluation['security']['rating'],
            "documentation_grade": code_evaluation['documentation']['rating'],
            "efficiency_grade": code_evaluation['efficiency']['rating'],
            "tech_stack_grade": tech_stack['grade'],
            "code_quality_explanation": code_evaluation['code_quality']['explanation'],
            "security_explanation": code_evaluation['security']['explanation'],
            "documentation_explanation": code_evaluation['documentation']['explanation'],
            "efficiency_explanation": code_evaluation['efficiency']['explanation'],
            "tech_stack": tech_stack['stack'],
            "summary": summary
        }
        
        return json.dumps(result, indent=2)

    def _parse_github_url(self, url: str) -> Tuple[str, str]:
        """
        Parse a GitHub URL to extract the owner and repository name.
        
        Args:
            url (str): The GitHub repository URL.
        
        Returns:
            Tuple[str, str]: A tuple containing the owner and repository name.
        
        Raises:
            ValueError: If the URL is not a valid GitHub repository URL.
        """
        parsed_url = urlparse(url)
        
        if parsed_url.netloc != 'github.com':
            raise ValueError("Not a valid GitHub URL")
        
        path_components = parsed_url.path.strip('/').split('/')
        
        if len(path_components) < 2:
            raise ValueError("URL does not contain a repository path")
        
        owner, repo = path_components[:2]
        
        try:
            self.github.get_repo(f"{owner}/{repo}")
        except Exception as e:
            raise ValueError(f"Repository not found or not accessible: {str(e)}")
        
        return owner, repo

    def _analyze_repo_structure(self, repo) -> str:
        structure = []
        contents = repo.get_contents("")
        for i, content in enumerate(contents):
            if i >= 20:  # Limit to 20 items in the structure
                structure.append("...(more files/directories)...")
                break
            if content.type == "dir":
                structure.append(f"Directory: {content.path}")
            else:
                structure.append(f"File: {content.path}")
        
        has_tests = any("test" in item.lower() for item in structure)
        return f"Repository structure:\n" + "\n".join(structure) + f"\n\nTests present: {'Yes' if has_tests else 'No'}"

    def _get_important_files(self, repo) -> List[str]:
        important_files = []
        contents = repo.get_contents("")
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(repo.get_contents(file_content.path))
            elif file_content.name in ['README.md', 'setup.py', 'requirements.txt'] or file_content.name.endswith(('.py', '.js', '.ts')):
                important_files.append(file_content.path)
        return important_files[:5]  # Limit to 5 most important files

    def _fetch_important_content(self, repo, important_files: List[str]) -> str:
        content = ""
        for file_path in important_files:
            file_content = repo.get_contents(file_path)
            file_text = file_content.decoded_content.decode('utf-8')
            content += f"File: {file_path}\n\n{file_text}\n\n"
        return content

    def _evaluate_code_with_openai(self, structure_analysis: str, code_content: str) -> Dict[str, Any]:
        prompt = f"""
        Analyze the following GitHub repository structure and important file contents:

        Repository Structure:
        {structure_analysis}

        Important File Contents:
        {code_content}

        Please provide the following evaluations:
        1. Repository Structure: Grade the overall structure out of 100 points. Be specific with the score (e.g., 87.6/100).
        2. Code Quality: Evaluate the code quality based on the provided file contents. Grade out of 100 points, being specific (e.g., 92.7/100).
        3. Security: Evaluate the code security. Grade out of 100 points, being specific (e.g., 88.3/100).
        4. Documentation: Evaluate the code documentation. Grade out of 100 points, being specific (e.g., 95.2/100).
        5. Efficiency: Evaluate the code efficiency. Grade out of 100 points, being specific (e.g., 91.8/100).

        For each criterion, consider relevant factors and provide a brief explanation.

        Format your response as a JSON object with the following structure:
        {{
            "structure_grade": 0.0,
            "code_quality": {{"rating": 0.0, "explanation": ""}},
            "security": {{"rating": 0.0, "explanation": ""}},
            "documentation": {{"rating": 0.0, "explanation": ""}},
            "efficiency": {{"rating": 0.0, "explanation": ""}}
        }}
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a code evaluation expert. Provide specific, detailed scores with one decimal place out of 100."},
                    {"role": "user", "content": prompt}
                ]
            )
            return json.loads(response.choices[0].message['content'])
        except Exception as e:
            logging.error(f"Error in OpenAI API request: {str(e)}")
            return {
                "structure_grade": 0.0,
                "code_quality": {"rating": 0.0, "explanation": "Error occurred during evaluation"},
                "security": {"rating": 0.0, "explanation": "Error occurred during evaluation"},
                "documentation": {"rating": 0.0, "explanation": "Error occurred during evaluation"},
                "efficiency": {"rating": 0.0, "explanation": "Error occurred during evaluation"}
            }

    def _evaluate_tech_stack(self, repo) -> Dict[str, Any]:
        files = repo.get_contents("")
        file_list = [file.path for file in files if file.type == "file"]
        
        prompt = f"""
        Based on the following list of files in a GitHub repository, identify the likely tech stack used:

        {', '.join(file_list)}

        Please provide:
        1. A list of up to 5 main technologies/frameworks likely used in this project.
        2. A grade from 0 to 100 evaluating how modern and appropriate the tech stack seems for the project. Be specific with the score (e.g., 87.6/100).

        Format your response as a JSON object with the following structure:
        {{
            "stack": ["technology1", "technology2", ...],
            "grade": 0.0
        }}
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a tech stack evaluation expert. Provide specific, detailed scores with one decimal place out of 100."},
                    {"role": "user", "content": prompt}
                ]
            )
            # Extract only the JSON part from the response
            response_text = response.choices[0].message['content']
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_response = response_text[json_start:json_end]
            return json.loads(json_response)
        except Exception as e:
            logging.error(f"Error in OpenAI API request for tech stack evaluation: {str(e)}")
            return {"stack": [], "grade": 0.0}

    def _calculate_aggregate_grade(self, evaluation: Dict[str, Any]) -> float:
        """
        Calculate the aggregate grade from individual ratings.

        Args:
            evaluation (Dict[str, Any]): The evaluation results from OpenAI.

        Returns:
            float: The aggregate grade (0-100) with one decimal place.
        """
        ratings = [evaluation[key]['rating'] for key in ['security', 'code_quality', 'documentation', 'efficiency']]
        return round(sum(ratings) / len(ratings), 1)

    def _generate_summary(self, code_evaluation: Dict[str, Any], tech_stack: Dict[str, Any]) -> str:
        summary = f"""
        Code Quality:
        {code_evaluation['code_quality']['explanation']}

        Security:
        {code_evaluation['security']['explanation']}

        Documentation:
        {code_evaluation['documentation']['explanation']}

        Efficiency:
        {code_evaluation['efficiency']['explanation']}

        Tech Stack:
        This project uses the following technologies: {', '.join(tech_stack['stack'])}
        """
        return summary.strip()

# Usage example:
# evaluator = GithubCodeEvaluator()
# result = evaluator.evaluate_repository("https://github.com/owner/repo")
# print(f"Code Quality Grade: {result['code_quality_grade']}")
# print(f"Summary: {result['summary']}")
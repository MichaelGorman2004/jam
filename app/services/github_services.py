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

    def evaluate_repository(self, repo_url: str) -> Dict[str, Any]:
        """
        Evaluate a GitHub repository for code quality and tech stack.

        Args:
            repo_url (str): The URL of the GitHub repository to evaluate.

        Returns:
            Dict[str, Any]: A dictionary containing the evaluation results:
                - structure_grade (float): The overall structure grade (0-1000).
                - code_quality_grade (float): The code quality grade (0-100).
                - code_quality_explanation (str): Explanation of the code quality grade.
                - tech_stack_grade (float): The tech stack grade (0-1000).
                - tech_stack (Dict[str, Any]): Tech stack evaluation results.
                - summary (str): A detailed summary of the evaluation.

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
        
        return {
            "structure_grade": code_evaluation['structure_grade'],
            "code_quality_grade": code_evaluation['code_quality']['rating'],
            "code_quality_explanation": code_evaluation['code_quality']['explanation'],
            "tech_stack_grade": tech_stack['grade'],
            "tech_stack": tech_stack['stack'],
            "summary": summary
        }

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
        1. Repository Structure: Grade the overall structure out of 1000 points. Consider organization, modularity, and best practices.
        2. Code Quality: Evaluate the code quality based on the provided file contents. Consider readability, maintainability, and adherence to coding standards.

        Format your response as a JSON object with the following structure:
        {{
            "structure_grade": 0,
            "code_quality": {{
                "rating": 0.0,
                "explanation": ""
            }}
        }}
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a code evaluation expert."},
                    {"role": "user", "content": prompt}
                ]
            )
            return json.loads(response.choices[0].message['content'])
        except Exception as e:
            logging.error(f"Error in OpenAI API request: {str(e)}")
            return {
                "structure_grade": 0,
                "code_quality": {"rating": 0.0, "explanation": "Error occurred during evaluation"}
            }

    def _evaluate_tech_stack(self, repo) -> Dict[str, Any]:
        files = repo.get_contents("")
        file_list = [file.path for file in files if file.type == "file"]
        
        prompt = f"""
        Based on the following list of files in a GitHub repository, identify the likely tech stack used:

        {', '.join(file_list)}

        Please provide:
        1. A list of up to 5 main technologies/frameworks likely used in this project.
        2. A grade from 0 to 1000 evaluating how modern and appropriate the tech stack seems for the project.

        Format your response as a JSON object with the following structure:
        {{
            "stack": ["technology1", "technology2", ...],
            "grade": 0
        }}
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a tech stack evaluation expert."},
                    {"role": "user", "content": prompt}
                ]
            )
            return json.loads(response.choices[0].message['content'])
        except Exception as e:
            logging.error(f"Error in OpenAI API request for tech stack evaluation: {str(e)}")
            return {"stack": [], "grade": 0}

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
        """
        Generate a summary based on the evaluation results.

        Args:
            code_evaluation (Dict[str, Any]): The code evaluation results from OpenAI.
            tech_stack (Dict[str, Any]): The tech stack evaluation results.

        Returns:
            str: A detailed summary of the evaluation.
        """
        summary = f"""
        Structure Grade: {code_evaluation['structure_grade']}/1000

        Code Quality Grade: {code_evaluation['code_quality']['rating']}/100
        {code_evaluation['code_quality']['explanation']}

        Tech Stack Grade: {tech_stack['grade']}/1000
        Technologies: {', '.join(tech_stack['stack'])}
        """
        return summary.strip()

# Usage example:
# evaluator = GithubCodeEvaluator()
# result = evaluator.evaluate_repository("https://github.com/owner/repo")
# print(f"Code Quality Grade: {result['code_quality_grade']}")
# print(f"Summary: {result['summary']}")

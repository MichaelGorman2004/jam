# Import necessary libraries
import requests
from github import Github
from urllib.parse import urlparse, quote_plus
import openai
import os
import json
from typing import Dict, Tuple, List, Any

class GithubCodeEvaluator:
    def __init__(self):
        # Initialize GitHub client with token from environment variable
        # GitHub API token for authentication (e.g., "ghp_1234567890abcdef")
        self.github: Github = Github(os.getenv('GITHUB_TOKEN'))

        # Store SonarCloud API token from environment variable
        # SonarCloud API token for authentication (e.g., "sonar_1234567890abcdef")
        self.sonarcloud_token: str = os.getenv('SONARCLOUD_TOKEN')

        # Store Codacy API token from environment variable
        # Codacy API token for authentication (e.g., "codacy_1234567890abcdef")
        self.codacy_token: str = os.getenv('CODACY_TOKEN')

        # Store SonarCloud API base URL from environment variable
        # Base URL for SonarCloud API (e.g., "https://sonarcloud.io/api")
        self.sonarcloud_url: str = os.getenv('SONARCLOUD_URL')

        # Store Codacy API base URL from environment variable
        # Base URL for Codacy API (e.g., "https://api.codacy.com/api/v3")
        self.codacy_url: str = os.getenv('CODACY_URL')

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
                - code_quality_grade (float): The overall code quality grade (0-100).
                - tech_stack_grade (float): The tech stack grade (0-100).
                - summary (str): A detailed summary of the evaluation.

        Raises:
            ValueError: If the repository URL is invalid or the repository is not accessible.
        """
        owner, repo_name = self._parse_github_url(repo_url)
        repo = self.github.get_repo(f"{owner}/{repo_name}")
        
        sonarcloud_report = self._analyze_code_quality_sonarcloud(owner, repo_name)
        codacy_report = self._analyze_code_quality_codacy(owner, repo_name)
        tech_stack = self._evaluate_tech_stack(repo)
        
        code_quality_grade, tech_stack_grade, summary = self._calculate_grades_and_summary(
            sonarcloud_report, codacy_report, tech_stack
        )
        
        final_summary = self._aggregate_summary(code_quality_grade, tech_stack_grade, summary)
        
        return {
            "code_quality_grade": code_quality_grade,
            "tech_stack_grade": tech_stack_grade,
            "summary": final_summary
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

    def _analyze_code_quality_sonarcloud(self, owner: str, repo_name: str) -> Dict[str, Any]:
        """
        Analyze code quality using SonarCloud API.

        Args:
            owner (str): The owner of the GitHub repository.
            repo_name (str): The name of the GitHub repository.

        Returns:
            Dict[str, Any]: A dictionary containing SonarCloud analysis results:
                - measures (Dict): Various code quality metrics.
                - issues (Dict): Summary of code issues.

        Raises:
            requests.RequestException: If there's an error in the API request.
        """
        project_key = f"{owner}_{repo_name}"
        headers = {"Authorization": f"Bearer {self.sonarcloud_token}"}
        
        measures_url = f"{self.sonarcloud_url}/measures/component"
        params = {
            "component": project_key,
            "metricKeys": "ncloc,complexity,violations,coverage,duplicated_lines_density,sqale_index,reliability_rating,security_rating,sqale_rating"
        }
        response = requests.get(measures_url, headers=headers, params=params)
        measures = response.json()

        issues_url = f"{self.sonarcloud_url}/issues/search"
        params = {"componentKeys": project_key, "facets": "types,severities"}
        response = requests.get(issues_url, headers=headers, params=params)
        issues = response.json()

        return {
            "measures": measures,
            "issues": issues
        }

    def _analyze_code_quality_codacy(self, owner: str, repo_name: str) -> Dict[str, Any]:
        """
        Analyze code quality using Codacy API.

        Args:
            owner (str): The owner of the GitHub repository.
            repo_name (str): The name of the GitHub repository.

        Returns:
            Dict[str, Any]: A dictionary containing Codacy analysis results:
                - summary (Dict): Overall project summary.
                - metrics (Dict): Detailed code metrics.

        Raises:
            requests.RequestException: If there's an error in the API request.
        """
        headers = {"api-token": self.codacy_token}
        
        summary_url = f"{self.codacy_url}/analysis/organizations/{owner}/projects/{repo_name}"
        response = requests.get(summary_url, headers=headers)
        summary = response.json()

        metrics_url = f"{self.codacy_url}/metrics/organizations/{owner}/projects/{repo_name}"
        response = requests.get(metrics_url, headers=headers)
        metrics = response.json()

        return {
            "summary": summary,
            "metrics": metrics
        }

    def _evaluate_tech_stack(self, repo: Any) -> Dict[str, Any]:
        """
        Evaluate the modernness and scalability of the repository's tech stack using OpenAI.

        Args:
            repo (github.Repository.Repository): A PyGithub repository object.

        Returns:
            Dict[str, Any]: A dictionary containing tech stack evaluation results:
                - technologies (List[str]): List of identified technologies.
                - modernness_score (float): Score for how modern the stack is (0-100).
                - scalability_score (float): Score for potential scalability (0-100).
                - summary (str): A brief summary of the evaluation.

        Raises:
            Exception: If there's an error parsing the OpenAI response.
        """
        files = repo.get_contents("")
        file_list = []

        while files:
            file_content = files.pop(0)
            if file_content.type == "dir":
                files.extend(repo.get_contents(file_content.path))
            else:
                file_list.append(file_content.name)

        prompt = f"""
        Given the following list of files from a GitHub repository:

        {', '.join(file_list[:100])}  # Limiting to first 100 files to avoid token limits

        Please analyze the tech stack based on these files and provide the following:
        1. A list of identified technologies and frameworks
        2. A score from 0-100 for how modern the tech stack is, considering current industry trends
        3. A score from 0-100 for the potential scalability of the tech stack
        4. A brief summary (max 100 words) explaining the scores and highlighting key aspects of the tech stack

        Provide your response in JSON format with the following keys:
        "technologies", "modernness_score", "scalability_score", "summary"
        """

        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=prompt,
            max_tokens=500,
            n=1,
            stop=None,
            temperature=0.5,
        )

        try:
            result = json.loads(response.choices[0].text.strip())
            return {
                "technologies": result["technologies"],
                "modernness_score": float(result["modernness_score"]),
                "scalability_score": float(result["scalability_score"]),
                "summary": result["summary"]
            }
        except (json.JSONDecodeError, KeyError) as e:
            raise Exception(f"Error parsing OpenAI response: {str(e)}")

    def _calculate_grades_and_summary(self, sonarcloud_report: Dict[str, Any], codacy_report: Dict[str, Any], tech_stack: Dict[str, Any]) -> Tuple[float, float, str]:
        """
        Calculate overall grades and generate a summary based on SonarCloud, Codacy, and tech stack reports.

        Args:
            sonarcloud_report (Dict[str, Any]): The SonarCloud analysis report.
            codacy_report (Dict[str, Any]): The Codacy analysis report.
            tech_stack (Dict[str, Any]): The tech stack evaluation report.

        Returns:
            Tuple[float, float, str]: A tuple containing:
                - code_quality_grade (float): The overall code quality grade (0-100).
                - tech_stack_grade (float): The tech stack grade (0-100).
                - summary (str): A detailed summary of the evaluation.
        """
        sonar_grade = self._calculate_sonarcloud_grade(sonarcloud_report)
        codacy_grade = self._calculate_codacy_grade(codacy_report)
        code_quality_grade = round((sonar_grade + codacy_grade) / 2, 1)
        
        tech_stack_grade = round(tech_stack.get('modernness_score', 0), 1)
        
        summary = f"""
        Code Quality Grade: {code_quality_grade}/100
        Tech Stack Grade: {tech_stack_grade}/100
        
        SonarCloud Analysis:
        {self._summarize_sonarcloud_report(sonarcloud_report)}
        
        Codacy Analysis:
        {self._summarize_codacy_report(codacy_report)}
        
        Tech Stack Analysis:
        {tech_stack.get('summary', 'No tech stack summary available')}
        """
        
        return code_quality_grade, tech_stack_grade, summary

    def _calculate_sonarcloud_grade(self, report: Dict[str, Any]) -> float:
        """
        Calculate a grade based on SonarCloud metrics.

        Args:
            report (Dict[str, Any]): The SonarCloud analysis report.

        Returns:
            float: The calculated grade (0-100).
        """
        measures = report['measures']['component']['measures']
        reliability = next(m for m in measures if m['metric'] == 'reliability_rating')['value']
        security = next(m for m in measures if m['metric'] == 'security_rating')['value']
        maintainability = next(m for m in measures if m['metric'] == 'sqale_rating')['value']
        
        rating_to_score = {'A': 100, 'B': 80, 'C': 60, 'D': 40, 'E': 20}
        return (rating_to_score[reliability] + rating_to_score[security] + rating_to_score[maintainability]) / 3

    def _calculate_codacy_grade(self, report: Dict[str, Any]) -> float:
        """
        Calculate a grade based on Codacy metrics.

        Args:
            report (Dict[str, Any]): The Codacy analysis report.

        Returns:
            float: The calculated grade (0-100).
        """
        return report['summary']['grade'] * 20  # Assuming grade is 1-5, convert to 0-100

    def _summarize_sonarcloud_report(self, report: Dict[str, Any]) -> str:
        """
        Generate a summary of the SonarCloud report.

        Args:
            report (Dict[str, Any]): The SonarCloud analysis report.

        Returns:
            str: A summary string of the SonarCloud report.
        """
        measures = report['measures']['component']['measures']
        return f"Lines of code: {next(m for m in measures if m['metric'] == 'ncloc')['value']}, " \
               f"Issues: {report['issues']['total']}, " \
               f"Coverage: {next(m for m in measures if m['metric'] == 'coverage')['value']}%"

    def _summarize_codacy_report(self, report: Dict[str, Any]) -> str:
        """
        Generate a summary of the Codacy report.

        Args:
            report (Dict[str, Any]): The Codacy analysis report.

        Returns:
            str: A summary string of the Codacy report.
        """
        return f"Grade: {report['summary']['grade']}, " \
               f"Issues: {report['summary']['issuesCount']}, " \
               f"Complexity: {report['metrics']['complexity']}"

    def _aggregate_summary(self, code_quality_grade: float, tech_stack_grade: float, summary: str) -> str:
        """
        Generate a final summary using OpenAI based on the evaluation results.

        Args:
            code_quality_grade (float): The overall code quality grade (0-100).
            tech_stack_grade (float): The tech stack grade (0-100).
            summary (str): A detailed summary of the evaluation.

        Returns:
            str: A concise, professional summary of the repository's code quality and tech stack.

        Raises:
            openai.error.OpenAIError: If there's an error in the OpenAI API request.
        """
        prompt = f"""
        Given the following information about a GitHub repository:
        
        Code Quality Grade: {code_quality_grade}/100
        Tech Stack Grade: {tech_stack_grade}/100
        
        Detailed Summary:
        {summary}
        
        Please provide a concise, professional summary of the repository's code quality and tech stack. 
        Highlight key strengths and areas for improvement for both aspects. 
        Keep the response under 200 words.
        """
        
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=prompt,
            max_tokens=200,
            n=1,
            stop=None,
            temperature=0.7,
        )
        
        return response.choices[0].text.strip()

# Usage example:
# evaluator = GithubCodeEvaluator()
# result = evaluator.evaluate_repository("https://github.com/owner/repo")
# print(f"Code Quality Grade: {result['code_quality_grade']}")
# print(f"Tech Stack Grade: {result['tech_stack_grade']}")
# print(f"Summary: {result['summary']}")

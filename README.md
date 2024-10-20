# jam

## Project Structure

The project is structured as a FastAPI application with the following main components:

- `app/`: Main application directory
  - `routers/`: Contains API route definitions
  - `models/`: Defines data models used in the application
  - `services/`: Implements business logic and external service interactions
  - `startup.py`: Core startup grading logic class
  - `main.py`: FastAPI application entry point

## File Descriptions

### app/routers/startup_router.py

This file defines the API routes for startup submission and grading. It contains:
- A POST endpoint `/startups/submit` for submitting a new startup for grading
- Logic for handling file uploads (presentation video and PDF)
- Interaction with the `Startup` class for grading
- Response formatting using `StartupGradingResponse` model

### app/models/startup.py

Defines the data models used in the application, including:
- `GradeWithDescription`: Represents a grade with its value and description
- `StartupGradingResponse`: The response model for graded startups

### app/startup.py

Contains the `Startup` class, which encapsulates the core logic for grading startups. It includes methods for:
- Creating and grading a startup
- Generating grade descriptions for different aspects (GitHub, presentation, novelty)

### app/services/

This directory contains service modules for different aspects of startup grading:
- `github_services.py`: Handles GitHub repository grading
- `presentation_services.py`: Processes and grades startup presentations
- `web_scraper.py`: Likely used for novelty assessment or additional data gathering

### app/main.py

The entry point of the FastAPI application. It sets up the API and includes routers.

## Workflow

1. A client submits a POST request to `/startups/submit` with startup information and files.
2. The `submit_startup` function in `startup_router.py` handles the request:
   - It reads the uploaded files (video and PDF).
   - Creates a `StartupModel` instance with the submitted data.
   - Calls `Startup.create_and_grade()` to process and grade the startup.
3. The `Startup` class (in `startup.py`) performs the grading:
   - It uses various services (GitHub, presentation, novelty) to grade different aspects.
   - Generates descriptions for each grade.
4. The graded startup data is formatted into a `StartupGradingResponse`.
5. The response is sent back to the client, containing grades and descriptions for GitHub, presentation, and novelty aspects.

## Setup and Running

[Include instructions for setting up and running the project here]

## Dependencies

[List the main dependencies of the project here]
Here's the content you provided in markdown code format:

```markdown
Certainly! I'll add documentation to the README.md file explaining how to use the `GithubCodeEvaluator` class and the format of the JSON output. Here's the addition to make to the README.md file:
```66:66:README.md
[List the main dependencies of the project here]
```
After line 66 in the README.md file, add the following content:
```markdown
## GitHub Repository Evaluation
The project includes a `GithubCodeEvaluator` class that can evaluate GitHub repositories for code quality, structure, security, documentation, efficiency, and tech stack.

### Usage
To evaluate a GitHub repository:
1. Create an instance of `GithubCodeEvaluator`:
   ```python
   evaluator = GithubCodeEvaluator()
   ```
2. Call the `evaluate_repository` method with a GitHub repository URL:
   ```python
   result_json = evaluator.evaluate_repository("https://github.com/username/repo")
   ```
3. The `result_json` is a JSON-formatted string containing the evaluation results.

### JSON Output Format
The `evaluate_repository` method returns a JSON string with the following structure:
```json
{
  "structure_grade": 87.6,
  "code_quality_grade": 92.7,
  "security_grade": 88.3,
  "documentation_grade": 95.2,
  "efficiency_grade": 91.8,
  "tech_stack_grade": 89.5,
  "code_quality_explanation": "Detailed explanation of code quality...",
  "security_explanation": "Detailed explanation of security...",
  "documentation_explanation": "Detailed explanation of documentation...",
  "efficiency_explanation": "Detailed explanation of efficiency...",
  "tech_stack": ["Python", "FastAPI", "SQLAlchemy"],
  "summary": "Overall summary of the evaluation..."
}
```
All grades are on a scale of 0 to 100, with one decimal place precision. The `tech_stack` field contains a list of up to 5 main technologies used in the project. The `summary` field provides a text overview of the evaluation without numerical scores.

### Environment Variables
Ensure you have set the following environment variables:
- `GITHUB_TOKEN`: Your GitHub API token
- `OPENAI_API_KEY`: Your OpenAI API key

These are used for authenticating with GitHub and OpenAI services respectively.
```
This addition to the README provides a clear explanation of how to use the `GithubCodeEvaluator`, what method to call, and the format of the JSON output. It also mentions the required environment variables.
```

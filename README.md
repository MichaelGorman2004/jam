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

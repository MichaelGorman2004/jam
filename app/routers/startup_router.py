from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from app.startup import Startup as StartupModel
from app.startup import Startup
from app.models.startup_model import GradeWithDescription, StartupGradingResponse

# Create a new router instance
router = APIRouter()

# POST endpoint to submit a new startup for grading
@router.post("/startups/submit", response_model=StartupGradingResponse)
async def submit_startup(
    name: str = Form(...),
    github_url: str = Form(...),
    presentation_video: UploadFile = File(...),
    presentation_pdf: UploadFile = File(...)
):
    try:
        # Read the contents of the uploaded files
        video_content = await presentation_video.read()
        pdf_content = await presentation_pdf.read()

        # Create a new StartupModel instance with the submitted data
        startup_data = StartupModel(
            name=name,
            github_url=github_url,
            presentation_video=video_content,
            presentation_pdf=pdf_content
        )

        # Grade the startup and save it to the database
        graded_startup = await Startup.create_and_grade(startup_data)
        
        # Prepare the response using our updated StartupGradingResponse model
        response = StartupGradingResponse(
            id=graded_startup.data.id,
            name=graded_startup.data.name,
            github_url=graded_startup.data.github_url,
            github_grade=GradeWithDescription(
                value=graded_startup.data.github_grade,
                description=graded_startup.get_github_grade_description()
            ),
            presentation_grade=GradeWithDescription(
                value=graded_startup.data.presentation_grade,
                description=graded_startup.get_presentation_grade_description()
            ),
            novelty_grade=GradeWithDescription(
                value=graded_startup.data.novelty_grade,
                description=graded_startup.get_novelty_grade_description()
            )
        )
        
        # Return the response to the client
        return response
    except Exception as e:
        # If any error occurs during the process, raise an HTTP exception
        raise HTTPException(status_code=400, detail=str(e))

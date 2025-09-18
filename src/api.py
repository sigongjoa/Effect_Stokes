from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import uuid
import asyncio

from main import EffectStokesOrchestrator # Assuming main.py contains the orchestrator
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# In a real application, you would fetch project and short details from a database
# For now, we'll use dummy data or mock the checks.
class ShortStatus:
    IDEA = "Idea"
    DRAFT_GENERATED = "Draft Generated"
    # Add other statuses as needed

# Initialize the orchestrator
orchestrator = EffectStokesOrchestrator()

async def run_video_generation_task(project_id: str, short_id: str, user_prompt: str):
    """
    This function will run in the background to generate the video.
    """
    print(f"Background task 'run_video_generation_task' started for Project: {project_id}, Short: {short_id}")
    try:
        dummy_user_prompt = f"Generate a video for project {project_id} and short {short_id}."
        print(f"Calling orchestrator.run_pipeline with prompt: {dummy_user_prompt}")
        final_video_path = orchestrator.run_pipeline(dummy_user_prompt)
        print(f"Video generation completed for {short_id}. Path: {final_video_path}")
    except Exception as e:
        print(f"Error during video generation for {short_id}: {e}")
        import traceback
        traceback.print_exc() # Print full traceback for debugging

@app.post("/api/projects/{project_id}/shorts/{short_id}/generate-video", status_code=202)
async def generate_video(project_id: str, short_id: str, background_tasks: BackgroundTasks):
    # Mock project and short existence and status for now
    # In a real application, you would query your database
    project_exists = True # Assume project exists
    short_exists = True   # Assume short exists
    short_current_status = ShortStatus.IDEA # Assume initial status

    if not project_exists:
        raise HTTPException(status_code=404, detail="Project not found.")
    
    if not short_exists:
        raise HTTPException(status_code=404, detail="Short not found.")

    if short_current_status not in [ShortStatus.IDEA, ShortStatus.DRAFT_GENERATED]:
        raise HTTPException(
            status_code=400,
            detail="Short not in a valid state for video generation. Status must be Idea or Draft Generated."
        )
    
    task_id = str(uuid.uuid4())
    
    # Trigger the video generation as a background task
    # We need to pass a user_prompt to the orchestrator.run_pipeline
    # For now, let's use a placeholder prompt.
    dummy_user_prompt = f"Generate video for project {project_id}, short {short_id}."
    background_tasks.add_task(run_video_generation_task, project_id, short_id, dummy_user_prompt)
    
    return {"message": "Video generation triggered", "taskId": task_id}

@app.get("/")
async def read_root():
    return {"message": "Effect Stokes API is running!"}

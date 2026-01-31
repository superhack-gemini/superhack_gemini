"""
FastAPI backend for Sports Narrative Generator.
Accepts sports storyline prompts and generates broadcast scripts.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import json

from generation_service import service
from models import SportsNarrativeScript

app = FastAPI(
    title="Sports Narrative Generator",
    description="Generate primetime sports broadcast scripts from storyline prompts",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class GenerateRequest(BaseModel):
    """Request to generate a sports narrative script."""
    prompt: str = Field(
        ..., 
        description="The sports storyline to generate a narrative for",
        examples=[
            "why didn't the 49ers make it to the superbowl",
            "seahawks path to the superbowl",
            "bill belichick getting snubbed from hall of fame"
        ]
    )
    duration_seconds: int = Field(
        default=150,
        description="Target duration of the video in seconds (default 2.5 minutes)",
        ge=60,
        le=300
    )


class TaskResponse(BaseModel):
    """Response after starting a generation task."""
    task_id: str
    status: str
    message: str


class ScriptResponse(BaseModel):
    """Response containing the generated script."""
    task_id: str
    status: str
    prompt: Optional[str] = None
    script: Optional[dict] = None
    research_context: Optional[dict] = None
    error: Optional[str] = None


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Sports Narrative Generator",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "generate": "POST /generate - Start script generation",
            "status": "GET /getvideo/{task_id} - Get generation status",
            "script": "GET /script/{task_id} - Get the generated script"
        }
    }


@app.post("/generate", response_model=TaskResponse)
async def generate_narrative(request: GenerateRequest):
    """
    Start a sports narrative script generation task.
    
    This kicks off the async workflow that:
    1. Researches the sports storyline on the web
    2. Generates a structured broadcast script
    3. Returns a task_id to poll for results
    """
    print(f"\n🏈 New generation request: {request.prompt}")
    print(f"   Duration: {request.duration_seconds}s")
    
    task_id = service.start_generation(request.prompt, request.duration_seconds)
    
    return TaskResponse(
        task_id=task_id,
        status="queued",
        message=f"Script generation started for: {request.prompt}"
    )


@app.get("/getvideo/{task_id}", response_model=ScriptResponse)
async def get_video_status(task_id: str):
    """
    Get the status and result of a generation task.
    
    Poll this endpoint to check when generation is complete.
    """
    status = service.get_task_status(task_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    response = ScriptResponse(
        task_id=task_id,
        status=status.get("status", "unknown"),
        prompt=status.get("prompt"),
        error=status.get("error")
    )
    
    # Include result data if completed
    if status.get("status") == "completed" and status.get("result"):
        result = status["result"]
        response.script = result.get("script")
        response.research_context = result.get("research_context")
    
    return response


@app.get("/script/{task_id}")
async def get_script(task_id: str):
    """
    Get just the generated script (without research context).
    
    Useful for frontends that only need the script data.
    """
    status = service.get_task_status(task_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if status.get("status") != "completed":
        return {
            "task_id": task_id,
            "status": status.get("status"),
            "message": "Script not yet ready"
        }
    
    result = status.get("result", {})
    script = result.get("script")
    
    if not script:
        raise HTTPException(status_code=500, detail="Script generation failed")
    
    return {
        "task_id": task_id,
        "status": "completed",
        "script": script
    }


@app.post("/generate/sync")
async def generate_narrative_sync(request: GenerateRequest):
    """
    Synchronous endpoint - waits for generation to complete.
    
    WARNING: This can take 30-60 seconds. Use /generate + polling for production.
    Useful for testing and debugging.
    """
    from orchestration import run_workflow
    
    print(f"\n🏈 Sync generation request: {request.prompt}")
    
    result = run_workflow(request.prompt, request.duration_seconds)
    
    return {
        "status": result.get("status"),
        "prompt": request.prompt,
        "script": result.get("script"),
        "research_context": result.get("research_context"),
        "error": result.get("error")
    }


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@app.get("/sample-prompts")
async def get_sample_prompts():
    """Get sample prompts to test the system."""
    return {
        "prompts": [
            {
                "prompt": "why didn't the 49ers make it to the superbowl",
                "description": "Analysis of the 49ers' championship collapse"
            },
            {
                "prompt": "seahawks path to the superbowl",
                "description": "Seattle's unlikely playoff run"
            },
            {
                "prompt": "bill belichick getting snubbed from hall of fame",
                "description": "The controversial Hall of Fame exclusion"
            },
            {
                "prompt": "Patrick Mahomes dynasty comparison to Tom Brady",
                "description": "Comparing the two greatest QBs"
            },
            {
                "prompt": "the rise of Jayden Daniels as NFL rookie of the year",
                "description": "Washington's rookie sensation"
            }
        ]
    }


@app.get("/script-format")
async def get_script_format():
    """Get information about the script format."""
    return {
        "description": "The script format for Veo video generation",
        "structure": {
            "studio": "Setting description for AI video generation",
            "hosts": "List of broadcast hosts with appearance details",
            "segments": [
                {
                    "ai_generated": "Studio segments with dialogue for Veo",
                    "real_clip": "References to real sports footage to insert"
                }
            ]
        },
        "segment_types": {
            "ai_generated": ["intro", "analysis", "debate", "transition", "outro"],
            "moods": ["dramatic", "exciting", "somber", "celebratory", "tense", "reflective", "controversial"]
        }
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    # Workers must be 1 because we are managing our own multiprocessing manager
    uvicorn.run(app, host="0.0.0.0", port=8000)

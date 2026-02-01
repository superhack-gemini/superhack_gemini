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
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional
import json
import base64

from generation_service import service
from models import VeoScript
from veo_agent import get_veo_agent, VeoAgent

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

# Static file serving for generated videos
# Videos are served from /videos/{filename}
VIDEOS_DIR = os.path.join(os.path.dirname(__file__), "videos")
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(os.path.join(VIDEOS_DIR, "final"), exist_ok=True)

app.mount("/videos", StaticFiles(directory=VIDEOS_DIR), name="videos")


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
    videoUrl: Optional[str] = None
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
        
        # Build video URL from final_video_path
        final_video_path = result.get("final_video_path")
        if final_video_path and os.path.exists(final_video_path):
            # Extract just the filename from path like /path/to/videos/final/uuid.mp4
            # and serve it as /videos/final/uuid.mp4
            video_filename = os.path.basename(final_video_path)
            response.videoUrl = f"/videos/final/{video_filename}"
        else:
            response.videoUrl = result.get("videoUrl")
    
    return response


@app.get("/getvideo/{task_id}/content")
async def get_video_content(task_id: str):
    """
    Get the final generated video file as a Base64 encoded string.
    """
    status = service.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if status.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Task not completed yet")
        
    result = status.get("result", {})
    video_path = result.get("final_video_path")
    
    if not video_path or not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found")
        
    try:
        with open(video_path, "rb") as video_file:
            encoded_string = base64.b64encode(video_file.read()).decode('utf-8')
            
        return {
            "task_id": task_id,
            "status": "completed",
            "video_base64": encoded_string,
            "format": "mp4"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read video file: {str(e)}")


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
# VEO VIDEO GENERATION ENDPOINTS
# ============================================================================

class VeoSegmentRequest(BaseModel):
    """Request to generate a single Veo video segment."""
    order: int = Field(default=1, description="Segment order in the script")
    duration_seconds: int = Field(default=8, ge=1, le=8, description="Duration (max 8s for Veo)")
    visual_prompt: str = Field(..., description="Visual description for the scene")
    speaker: str = Field(default="Marcus Webb", description="Speaker name")
    dialogue: str = Field(..., description="Dialogue for the speaker")
    delivery: str = Field(default="professional", description="Delivery style")
    camera: str = Field(default="Medium shot", description="Camera direction")
    mood: str = Field(default="professional", description="Scene mood")


class VeoGenerateResponse(BaseModel):
    """Response from Veo video generation."""
    status: str
    video_uri: Optional[str] = None
    segment_order: int
    duration_seconds: int
    error: Optional[str] = None


@app.post("/veo/generate", response_model=VeoGenerateResponse)
async def generate_veo_video(request: VeoSegmentRequest):
    """
    Generate a single Veo AI video for a broadcast segment.
    
    This uses Veo 3.1 to create a realistic broadcast video with:
    - Locked talent profiles (Marcus Webb, Sarah Chen)
    - Consistent studio setting
    - Professional broadcast aesthetics
    
    Note: Takes 45-60 seconds per segment.
    """
    import asyncio
    
    try:
        veo_agent = get_veo_agent()
        
        segment = {
            "order": request.order,
            "type": "ai_generated",
            "duration_seconds": request.duration_seconds,
            "visual_prompt": request.visual_prompt,
            "speaker": request.speaker,
            "dialogue": request.dialogue,
            "delivery": request.delivery,
            "camera": request.camera,
            "mood": request.mood
        }
        
        print(f"\n🎥 Generating Veo video for segment {request.order}")
        print(f"   Speaker: {request.speaker}")
        print(f"   Dialogue: {request.dialogue[:50]}...")
        
        result = await veo_agent.generate_video(
            segment,
            on_progress=lambda msg: print(f"   Status: {msg}")
        )
        
        return VeoGenerateResponse(
            status="completed",
            video_uri=result.get("video_uri"),
            segment_order=result.get("segment_order", request.order),
            duration_seconds=result.get("duration_seconds", request.duration_seconds)
        )
        
    except Exception as e:
        print(f"❌ Veo generation failed: {e}")
        return VeoGenerateResponse(
            status="error",
            segment_order=request.order,
            duration_seconds=request.duration_seconds,
            error=str(e)
        )


@app.post("/veo/refine-prompt")
async def refine_veo_prompt(request: VeoSegmentRequest):
    """
    Refine a segment into an optimized Veo prompt without generating video.
    
    Useful for previewing/editing prompts before generation.
    """
    try:
        veo_agent = get_veo_agent()
        
        segment = {
            "order": request.order,
            "duration_seconds": request.duration_seconds,
            "visual_prompt": request.visual_prompt,
            "speaker": request.speaker,
            "dialogue": request.dialogue,
            "delivery": request.delivery,
            "camera": request.camera,
            "mood": request.mood
        }
        
        refined_prompt = await veo_agent.refine_prompt(segment)
        
        return {
            "status": "success",
            "original_segment": segment,
            "refined_prompt": refined_prompt,
            "full_prompt_with_talent": f"{VeoAgent.TALENT_PROFILES}\n\nSCENE ACTION: {refined_prompt}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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

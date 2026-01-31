from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from generation_service import service

app = FastAPI()

class GenerateRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_video(request: GenerateRequest):
    """
    Starts a video generation task.
    Supports long-running operations via multiprocessing.
    """
    task_id = service.start_generation(request.prompt)
    return {"task_id": task_id, "status": "queued"}

@app.get("/getvideo/{task_id}")
async def get_video_status(task_id: str):
    """
    Polls the status of a generation task.
    """
    status = service.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return status

if __name__ == "__main__":
    import uvicorn
    # Workers must be 1 because we are managing our own multiprocessing pool/manager within the app process
    uvicorn.run(app, host="0.0.0.0", port=8000)

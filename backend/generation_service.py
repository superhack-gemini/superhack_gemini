"""
Background task management for script generation.
Uses multiprocessing to handle long-running LangGraph workflows.
"""
import multiprocessing
import uuid
from typing import Dict, Any, Optional

# Global manager to handle shared state across processes
_manager = None
_tasks: Dict[str, Any] = {}


def _init_manager():
    global _manager, _tasks
    if _manager is None:
        _manager = multiprocessing.Manager()
        _tasks = _manager.dict()


def _run_generation_task(task_id: str, tasks_dict: Dict, prompt: str, duration_seconds: int):
    """
    Worker function that runs in a separate process.
    Executes the LangGraph workflow for script generation.
    """
    try:
        # Update status to processing
        task_info = tasks_dict.get(task_id)
        if task_info:
            task_info['status'] = 'processing'
            tasks_dict[task_id] = task_info

        # Import here to avoid issues with multiprocessing
        from orchestration import run_workflow
        
        print(f"[{task_id}] Starting LangGraph workflow...")
        print(f"[{task_id}] Prompt: {prompt}")
        print(f"[{task_id}] Duration: {duration_seconds}s")
        
        # Execute the multi-agent workflow
        workflow_result = run_workflow(prompt, duration_seconds)
        
        result = {
            "script": workflow_result.get("script"),
            "research_context": workflow_result.get("research_context"),
            "workflow_status": workflow_result.get("status"),
            "error": workflow_result.get("error"),
            "videoUrl": workflow_result.get("videoUrl", f"http://example.com/video_{task_id}.mp4")
        }

        # Update status to completed
        task_info = tasks_dict.get(task_id)
        if task_info:
            task_info['status'] = 'completed'
            task_info['result'] = result
            tasks_dict[task_id] = task_info
        
        print(f"[{task_id}] ✅ Completed successfully!")

    except Exception as e:
        print(f"[{task_id}] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        task_info = tasks_dict.get(task_id)
        if task_info:
            task_info['status'] = 'failed'
            task_info['error'] = str(e)
            tasks_dict[task_id] = task_info


class GenerationService:
    """Service for managing script generation tasks."""
    
    def __init__(self):
        _init_manager()

    def start_generation(self, prompt: str, duration_seconds: int = 150) -> str:
        """
        Start a new generation task in a background process.
        
        Args:
            prompt: The sports storyline prompt
            duration_seconds: Target video duration
            
        Returns:
            task_id: Unique identifier for the task
        """
        task_id = str(uuid.uuid4())
        
        # Initialize task state
        _tasks[task_id] = {
            'id': task_id,
            'status': 'queued',
            'prompt': prompt,
            'duration_seconds': duration_seconds,
            'result': None,
            'error': None
        }

        # Start the background process
        process = multiprocessing.Process(
            target=_run_generation_task,
            args=(task_id, _tasks, prompt, duration_seconds)
        )
        process.start()
        
        print(f"[{task_id}] Task queued - Process started")
        
        return task_id

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a task.
        
        Args:
            task_id: The task identifier
            
        Returns:
            Task status dict or None if not found
        """
        task_data = _tasks.get(task_id)
        if task_data:
            # Convert Manager dict to regular dict for JSON serialization
            return dict(task_data)
        return None
    
    def list_tasks(self) -> Dict[str, str]:
        """List all tasks and their statuses."""
        return {
            task_id: task_data.get('status', 'unknown')
            for task_id, task_data in _tasks.items()
        }


# Singleton instance to be used by the API
service = GenerationService()

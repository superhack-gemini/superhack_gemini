import multiprocessing
import time
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

def _run_generation_task(task_id: str, tasks_dict: Dict, params: Any):
    """
    This is the worker function that runs in a separate process.
    """
    try:
        # Update status to processing
        task_info = tasks_dict.get(task_id)
        if task_info:
            task_info['status'] = 'processing'
            tasks_dict[task_id] = task_info

        # --- START LONG RUNNING OPERATION ---
        from orchestration import run_workflow
        print(f"[{task_id}] Starting LangGraph workflow with params: {params}")
        
        # Execute the multi-agent workflow
        workflow_result = run_workflow(params)
        
        result = {
            "workflow_data": workflow_result.get("research_results"),
            "status_update": workflow_result.get("current_status"),
            "video_url": f"http://example.com/video_{task_id}.mp4", 
            "details": "Generated via LangGraph multi-agent setup"
        }
        # --- END LONG RUNNING OPERATION ---

        # Update status to completed
        task_info = tasks_dict.get(task_id)
        if task_info:
            task_info['status'] = 'completed'
            task_info['result'] = result
            tasks_dict[task_id] = task_info
        print(f"[{task_id}] Completed.")

    except Exception as e:
        print(f"[{task_id}] Error: {e}")
        task_info = tasks_dict.get(task_id)
        if task_info:
            task_info['status'] = 'failed'
            task_info['error'] = str(e)
            tasks_dict[task_id] = task_info

class GenerationService:
    def __init__(self):
        _init_manager()

    def start_generation(self, prompt: str) -> str:
        """
        Starts a new generation task in a background process.
        Returns the task_id.
        """
        task_id = str(uuid.uuid4())
        
        # Initialize task state
        _tasks[task_id] = {
            'id': task_id,
            'status': 'queued',
            'prompt': prompt,
            'result': None,
            'error': None
        }

        # Start the background process
        process = multiprocessing.Process(
            target=_run_generation_task,
            args=(task_id, _tasks, prompt)
        )
        process.start()
        
        return task_id

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the current status of a task.
        """
        return _tasks.get(task_id)

# Singleton instance to be used by the API
service = GenerationService()

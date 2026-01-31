"""
LangGraph orchestration for sports narrative generation.
Multi-agent workflow connecting all the agents in the pipeline.

CURRENT FLOW:
  Research → Script Generation → [Future: Video/Clip/Audio Agents] → Output

TO ADD A NEW AGENT:
  1. Create your agent file (e.g., video_agent.py)
  2. Import it below
  3. Add state fields for your agent's output
  4. Create a node function
  5. Add the node to the graph in build_narrative_graph()
  6. Connect it with edges
"""
from typing import Annotated, TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
import requests
import time
import os
import json
import asyncio
from typing import Annotated, TypedDict, List, Dict, Any
from dataclasses import dataclass
from urllib.parse import quote
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from browser_use_sdk import BrowserUse


# Load environment variables
load_dotenv()
# 1. Define Shared State
class AgentState(TypedDict):
    """The shared state for the multi-agent workflow."""
    messages: Annotated[List[BaseMessage], "The history of messages in the conversation"]
    research_results: Dict[str, Any]
    current_status: str

@dataclass
class Video:
    path: str
    title: str

class YouTubeShort(BaseModel):
    video_id: str
    title: str
    video_url: str
    channel_name: str
    channel_url: str
    view_count: str
    upload_date: str
    duration: str
    thumbnail_url: str = Field(None)
    description: str = Field(None)
    type: str = "short"

class YouTubeSearchOutput(BaseModel):
    query: str
    videos: List[YouTubeShort]
    count: int

def retrieve_video(url: str):
    print(f"--- RETRIEVING VIDEO: {url} ---")
    
    # Configuration
    publer_token = os.getenv("PUBLER_TOKEN")
    if not publer_token:
        raise ValueError("PUBLER_TOKEN not found in environment variables")
    publer_url = "https://app.publer.com/tools/media"
    
    # 1. POST request to get job_id
    payload = {
        "macOS": False,
        "token": publer_token,
        "url": url
    }
    
    response = requests.post(publer_url, json=payload)
    response.raise_for_status()
    job_id = response.json().get("job_id")
    
    if not job_id:
        raise Exception("Failed to get job_id from Publer")
        
    # 2. Poll job status
    status_url = f"https://app.publer.com/api/v1/job_status/{job_id}"
    max_retries = 30
    retry_count = 0
    job_data = None
    
    while retry_count < max_retries:
        status_resp = requests.get(status_url)
        status_resp.raise_for_status()
        job_data = status_resp.json()
        
        if job_data.get("status") == "complete":
            break
            
        print(f"Waiting for job {job_id} to complete... (status: {job_data.get('status')})")
        time.sleep(2)
        retry_count += 1
    else:
        raise Exception(f"Job {job_id} timed out")
        
    # 3. Extract path and metadata
    payload_items = job_data.get("payload", [])
    if not payload_items:
        raise Exception("No video data found in Publer response")
        
    video_item = payload_items[0]
    download_url = video_item.get("path")
    video_name = video_item.get("name", "downloaded_video")
    
    # 4. Download video via proxy
    encoded_url = quote(download_url, safe='')
    proxy_download_url = f"https://publer-media-downloader.kalemi-code4806.workers.dev/?url={encoded_url}"
    print(proxy_download_url)
    # Ensure videos directory exists
    video_dir = os.path.join(os.path.dirname(__file__), "videos")
    os.makedirs(video_dir, exist_ok=True)
    
    local_filename = f"{int(time.time())}_{video_name.replace(' ', '_')}.mp4"
    local_path = os.path.join(video_dir, local_filename)
    
    print(f"Downloading video to {local_path}...")
    with requests.get(proxy_download_url, stream=True) as r:
        r.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                
    return Video(path=local_path, title=video_name)


@tool
def youtube_scraper_tool(query: str):
    """
    Search and scrape YouTube for videos related to the query. 
    Limits results to 5 per query.
    """
    print(f"--- EXECUTING YOUTUBE SCRAPER: {query} ---")
    browser_use_api_key = os.getenv("BROWSER_USE_API_KEY")
    client = BrowserUse(api_key=browser_use_api_key)
    if not browser_use_api_key:
        return "Error: BROWSER_USE_API_KEY not found in environment variables."
    result = client.skills.execute_skill(
                skill_id="aa967d12-c544-41b4-9169-da7d44c295c7",
                parameters={
                    "query": query,
                    "limit": 5
                }
            )
    return [video['video_url'] for video in result.result['data']['videos']]

@tool
def social_media_researcher_tool(platform: str, topic: str):
    """
    Use a browser-based agent to research a topic on social media platforms (e.g., X, Instagram).
    """
    # Shell code: To be implemented with browser-use/agent logic
    return f"Social media research on {platform} for {topic} (STUB)"

@tool
def google_search(query: str):
    """
    Search Google for the given query to get live information.
    """
    # Shell for Google Search tool
    print(f"--- EXECUTING GOOGLE SEARCH: {query} ---")
    return f"Search results for: {query} (STUB: Integration pending API key)"

# 2. Gemini Setup
# Note: Ensure GEMINI_API_KEY is in your .env
gemini_api_key = os.getenv("GEMINI_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview", google_api_key=gemini_api_key)
llm_with_tools = llm.bind_tools([google_search, youtube_scraper_tool, social_media_researcher_tool])

# 3. Define Node(s)
def fanout_search_node(state: AgentState):
    """
    Generates multiple search queries based on the user narrative and executes them.
    """
    print("--- SEARCH FANOUT NODE STARTING ---")
    narrative = state['messages'][-1].content
    
    system_prompt = (
        "You are an investigative sports researcher. "
        "Take the user narrative and generate 3-5 general Youtube Search queries "
        "to find relevant video footage and background info. "
        "use the google_search tool to retrieve relevant background info to create this set of queries"
    )
    
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=narrative)]
    
    ai_msg = llm_with_tools.invoke(messages)
    
    # Extract queries without executing (fanout)
    queries = []
    if ai_msg.tool_calls:
        queries = [tc['args'].get('query') for tc in ai_msg.tool_calls if tc['name'] == 'google_search']
    
    return {
        "research_results": {"search_fanout_queries": queries},
    }

def research_node(state: AgentState):
    """
    🎞️ CLIP AGENT (TODO: Implement clip search)
    
    Purpose: Find real sports clips based on script references
    Input: script (clip references with search queries)
    Output: retrieved_clips (found clip URLs/metadata)
    
    Example implementation:
    ```
    from clip_agent import clip_agent
    
    script = state["script"]
    clip_refs = [s for s in script["segments"] if s["segment_type"] == "real_clip"]
    
    retrieved_clips = []
    for ref in clip_refs:
        clip = clip_agent.search_clip(
            query=ref["clip_reference"]["search_query"],
            duration=ref["clip_reference"]["duration_seconds"]
        )
        retrieved_clips.append(clip)
    
    return {"retrieved_clips": retrieved_clips, "clip_status": "completed"}
    ```
    """
    print(f"\n{'='*60}")
    print("🎞️ CLIP RETRIEVAL NODE - (Not yet implemented)")
    print(f"{'='*60}")
    
    # TODO: Implement clip search/retrieval
    return {
        "current_phase": "clips_skipped",
        "messages": [AIMessage(content="Clip retrieval not yet implemented")]
    }


# -----------------------------------------------------------------------------
# AUDIO GENERATION NODE (TODO)
# -----------------------------------------------------------------------------
def audio_generation_node(state: NarrativeState) -> Dict[str, Any]:
    """
    🎙️ AUDIO AGENT (TODO: Implement voice generation)
    
    Purpose: Generate voice audio for dialogue
    Input: script (dialogue lines with delivery notes)
    Output: audio_tracks (generated audio files)
    
    Example implementation:
    ```
    from audio_agent import audio_agent
    
    script = state["script"]
    
    audio_tracks = []
    for seg in script["segments"]:
        if seg["ai_segment"]:
            for line in seg["ai_segment"]["dialogue"]:
                audio = audio_agent.generate_voice(
                    text=line["text"],
                    speaker=line["speaker"],
                    delivery=line["delivery"]
                )
                audio_tracks.append(audio)
    
    return {"audio_tracks": audio_tracks, "audio_status": "completed"}
    ```
    """
    print(f"\n{'='*60}")
    print("🎙️ AUDIO GENERATION NODE - (Not yet implemented)")
    print(f"{'='*60}")
    
    # TODO: Implement voice/audio generation
    return {
        "current_phase": "audio_skipped",
        "messages": [AIMessage(content="Audio generation not yet implemented")]
    }


# -----------------------------------------------------------------------------
# ASSEMBLY NODE (TODO)
# -----------------------------------------------------------------------------
def assembly_node(state: NarrativeState) -> Dict[str, Any]:
    """
    🎥 ASSEMBLY AGENT (TODO: Implement final video assembly)
    
    Purpose: Combine all pieces into final video
    Input: video_segments, retrieved_clips, audio_tracks
    Output: final_video (complete video file)
    
    Example implementation:
    ```
    from assembly_agent import assembly_agent
    
    final_video = assembly_agent.assemble(
        video_segments=state["video_segments"],
        clips=state["retrieved_clips"],
        audio=state["audio_tracks"],
        script=state["script"]  # For timing/ordering
    )
    
    return {"final_video": final_video, "assembly_status": "completed"}
    ```
    """
    print(f"\n{'='*60}")
    print("🎥 ASSEMBLY NODE - (Not yet implemented)")
    print(f"{'='*60}")
    
    # TODO: Implement video assembly
    return {
        "messages": [HumanMessage(content=f"Research complete. Found: {yt_data}, {sm_data}")],
        "research_results": {"youtube": yt_data, "social_media": sm_data},
        "current_status": "research_completed"
    }

# 4. Build the Graph
builder = StateGraph(AgentState)

# Add nodes
builder.add_node("search_fanout", fanout_search_node)
builder.add_node("researcher", research_node)

# Add edges
builder.add_edge(START, "search_fanout")
builder.add_edge("search_fanout", "researcher")
builder.add_edge("researcher", END)

# Compile
graph = builder.compile()

def run_workflow(prompt: str, duration_seconds: int = 150) -> Dict[str, Any]:
    """
    Execute the sports narrative generation workflow.
    
    Args:
        prompt: The sports storyline to generate a narrative for
        duration_seconds: Target duration of the final video (default 2.5 minutes)
    
    Returns:
        Dict containing results from all completed agents
    """
    print(f"\n{'#'*60}")
    print(f"🏈 SPORTS NARRATIVE GENERATOR")
    print(f"{'#'*60}")
    print(f"Prompt: {prompt}")
    print(f"Target Duration: {duration_seconds}s")
    print(f"{'#'*60}\n")
    
    initial_state: NarrativeState = {
        "prompt": prompt,
        "duration_seconds": duration_seconds,
        "messages": [HumanMessage(content=prompt)],
        "research_context": None,
        "research_status": "pending",
        "script": None,
        "script_status": "pending",
        "current_phase": "starting",
        "error": None,
        # TODO: Initialize future agent states
        # "video_segments": None,
        # "video_status": "pending",
        # "retrieved_clips": None,
        # "clip_status": "pending",
        # "audio_tracks": None,
        # "audio_status": "pending",
        # "final_video": None,
        # "assembly_status": "pending",
    }
    
    # Execute the workflow
    final_state = graph.invoke(initial_state)
    
    # Return all results
    return {
        "prompt": prompt,
        "research_context": final_state.get("research_context"),
        "script": final_state.get("script"),
        "status": final_state.get("current_phase"),
        "error": final_state.get("error"),
        # TODO: Include future agent outputs
        # "video_segments": final_state.get("video_segments"),
        # "retrieved_clips": final_state.get("retrieved_clips"),
        # "audio_tracks": final_state.get("audio_tracks"),
        # "final_video": final_state.get("final_video"),
    }


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    result = run_workflow("why didn't the 49ers make it to the superbowl")
    
    print(f"\n{'='*60}")
    print("FINAL RESULT")
    print(f"{'='*60}")
    
    if result.get("script"):
        script = result["script"]
        print(f"\n📺 {script['title']}")
        print(f"Duration: {script['total_duration_seconds']}s")
        print(f"\nSegments:")
        for seg in script['segments']:
            if seg['segment_type'] == 'ai_generated':
                ai_seg = seg['ai_segment']
                print(f"  {seg['order']}. [AI] {ai_seg['segment_type'].upper()} - {ai_seg['duration_seconds']}s")
            else:
                clip = seg['clip_reference']
                print(f"  {seg['order']}. [CLIP] {clip['description'][:50]}...")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")

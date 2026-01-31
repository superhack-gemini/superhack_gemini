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
import uuid
from typing import Annotated, TypedDict, List, Dict, Any
from dataclasses import dataclass
from urllib.parse import quote
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from browser_use_sdk import BrowserUse
from video_utils import combine_videos


# Load environment variables
load_dotenv()
# 1. Define Shared State
class NarrativeState(TypedDict):
    """The shared state for the multi-agent workflow."""
    prompt: str
    duration_seconds: int
    messages: Annotated[List[BaseMessage], "The history of messages in the conversation"]
    research_results: Dict[str, Any]
    research_context: Optional[str]
    script: Optional[Dict[str, Any]]
    retrieved_clips: List[Dict[str, Any]]
    current_phase: str
    error: Optional[str]
    final_video_path: Optional[str]

# --- Script Schema Models ---
class StudioConfig(BaseModel):
    description: str
    lighting: str
    color_scheme: str

class HostConfig(BaseModel):
    name: str
    role: str
    appearance: str

class ClipReference(BaseModel):
    description: str
    search_query: str
    context: str

class AISegment(BaseModel):
    visual_prompt: str
    speaker: str
    dialogue: str
    delivery: str
    camera: str
    graphics: List[str]
    studio: Optional[StudioConfig] = None
    hosts: Optional[List[HostConfig]] = None

class Segment(BaseModel):
    order: int
    type: str = Field(..., description="'ai_generated' or 'real_clip'")
    duration_seconds: int
    # One of these will be populated based on type
    ai_segment: Optional[AISegment] = None
    clip_reference: Optional[ClipReference] = None
    # Flat structure support for the generator
    visual_prompt: Optional[str] = None
    speaker: Optional[str] = None
    dialogue: Optional[str] = None
    delivery: Optional[str] = None
    camera: Optional[str] = None
    graphics: Optional[List[str]] = None
    description: Optional[str] = None
    search_query: Optional[str] = None
    context: Optional[str] = None
    studio: Optional[StudioConfig] = None
    hosts: Optional[List[HostConfig]] = None

class Script(BaseModel):
    title: str
    storyline: str
    total_duration_seconds: int
    studio: StudioConfig
    hosts: List[HostConfig]
    segments: List[Segment]
    research_summary: str
    key_facts: List[str]

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
    
    # Use UUID for filename, omit title
    video_id = str(uuid.uuid4())
    local_filename = f"{video_id}.mp4"
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
def fanout_search_node(state: NarrativeState):
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

def research_node(state: NarrativeState):
    """
    Executes the search queries generated by the fanout node and summarizes findings.
    """
    print("--- RESEARCH NODE STARTING ---")
    queries = state.get('research_results', {}).get('search_fanout_queries', [])
    
    if not queries:
        return {"current_phase": "research_failed", "error": "No queries to research"}
        
    context = []
    for q in queries:
        # Using google_search tool directly
        # In a real app, you might want to parallelize this
        try:
            print(f"Researching: {q}")
            result = google_search.invoke(q)
            context.append(f"Query: {q}\nResult: {result}")
        except Exception as e:
            print(f"Failed to search {q}: {e}")
            
    combined_context = "\n\n".join(context)
    
    return {
        "research_context": combined_context,
        "current_phase": "research_completed"
    }

def script_generation_node(state: NarrativeState):
    """
    Generates the broadcast script using Gemini and the research context.
    """
    print("--- SCRIPT GENERATION NODE STARTING ---")
    research_context = state.get('research_context', '')
    prompt = state.get('prompt', '')
    duration = state.get('duration_seconds', 150)
    
    # Configure LLM for structured output
    structured_llm = llm.with_structured_output(Script)
    
    system_msg = (
        "You are a professional sports broadcast producer. "
        "Create a prime-time TV segment script based on the provided research context. "
        "The script must alternate between AI-generated studio segments (hosts talking) "
        "and real clip segments (footage descriptions with search queries). "
        f"Target total duration: {duration} seconds.\n\n"
        "GUIDELINES:\n"
        "1. Create 3 HOSTS: Lead Anchor, Analyst, Former Player.\n"
        "2. SEGMENTS:\n"
        "   - 'ai_generated': Studio shots, dialogue, graphics.\n"
        "   - 'real_clip': finding footage to illustrate the point. Provide a specific 'search_query' for YouTube.\n"
        "3. LOGIC: Intro -> Context (Clip) -> Analysis (AI) -> Key Moment (Clip) -> Debate (AI) -> Outro.\n"
        "4. Research: Use the provided keys facts accurately."
    )
    
    human_msg = f"Storyline: {prompt}\n\nResearch Context:\n{research_context}"
    
    try:
        script = structured_llm.invoke([
            SystemMessage(content=system_msg),
            HumanMessage(content=human_msg)
        ])
        
        # Convert Pydantic model to dict
        script_dict = script.model_dump()
        return {
            "script": script_dict,
            "current_phase": "script_generated"
        }
    except Exception as e:
        print(f"Script generation error: {e}")
        return {"error": str(e), "current_phase": "script_failed"}

def clip_retrieval_node(state: NarrativeState):
    """
    Parses the script for 'real_clip' segments and retrieves videos suitable for the node.
    """
    print("--- CLIP RETRIEVAL NODE STARTING ---")
    script = state.get('script')
    if not script:
        return {"error": "No script found", "current_phase": "clip_retrieval_failed"}
    
    segments = script.get('segments', [])
    retrieved_clips = []
    
    for seg in segments:
        if seg.get('type') == 'real_clip':
            # Handle both flat and nested structures (Pydantic dump might vary based on definition)
            # Our model definition allows flat fields for generator ease, but let's check carefully.
            
            # If the model put data in 'clip_reference', use it; otherwise look at top level.
            ref_data = seg.get('clip_reference') or seg
            
            query = ref_data.get('search_query')
            description = ref_data.get('description', 'Unknown clip')
            
            if query:
                print(f"Finding clip for: {description} (Query: {query})")
                try:
                    # 1. Scrape YouTube for candidate URLs
                    # youtube_scraper_tool returns a list of URLs
                    candidates = youtube_scraper_tool.invoke({"query": query})
                    
                    if candidates and len(candidates) > 0:
                        # 2. Pick the first candidate and download
                        best_url = candidates[0]
                        print(f"Downloading best match: {best_url}")
                        
                        video = retrieve_video(best_url)
                        
                        # Map query and path
                        retrieved_clips.append({
                            "query": query,
                            "video_path": video.path,
                            "original_url": best_url
                        })
                    else:
                        print(f"No videos found for query: {query}")
                        
                except Exception as e:
                    print(f"Failed to retrieve clip for '{query}': {e}")
                    # Continue to next clip, don't fail entire workflow
                    
    return {
        "retrieved_clips": retrieved_clips,
        "current_phase": "clips_retrieved"
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
# -----------------------------------------------------------------------------
# ASSEMBLY NODE
# -----------------------------------------------------------------------------
def assembly_node(state: NarrativeState):
    """
    Concatenates retrieved clips into a final video.
    """
    print("--- ASSEMBLY NODE STARTING ---")
    retrieved_clips = state.get('retrieved_clips', [])
    
    if not retrieved_clips:
        return {"current_phase": "assembly_failed", "error": "No clips to assemble"}
        
    try:
        # Sort clips by segment order to ensure correct sequence
        # Note: In a real script, we'd interleave AI segments too. 
        # For this prototype, we're just concatenating the 'real_clip' segments we found.
        sorted_clips = sorted(retrieved_clips, key=lambda x: x.get('segment_order', 0))
        video_paths = [clip['video_path'] for clip in sorted_clips if os.path.exists(clip['video_path'])]
        
        if not video_paths:
            return {"current_phase": "assembly_failed", "error": "No valid video files found"}
            
        # Ensure output directory exists
        final_dir = os.path.join(os.path.dirname(__file__), "videos", "final")
        os.makedirs(final_dir, exist_ok=True)
        
        # Generate output path
        output_filename = f"{uuid.uuid4()}.mp4"
        output_path = os.path.join(final_dir, output_filename)
        
        print(f"Combining {len(video_paths)} videos into {output_path}...")
        combine_videos(video_paths, output_path)
        print(f"✅ Final Video Saved: {output_path}")
        
        return {
            "final_video_path": output_path,
            "current_phase": "completed"
        }
        
    except Exception as e:
        print(f"Assembly failed: {e}")
        return {"current_phase": "assembly_failed", "error": str(e)}

# 4. Build the Graph
builder = StateGraph(NarrativeState)

# Add nodes
# Add nodes
builder.add_node("search_fanout", fanout_search_node)
builder.add_node("researcher", research_node)
builder.add_node("script_generator", script_generation_node)
builder.add_node("clip_retriever", clip_retrieval_node)

# Add edges
builder.add_edge(START, "search_fanout")
builder.add_edge("search_fanout", "researcher")
builder.add_edge("researcher", "script_generator")
builder.add_node("assembly", assembly_node)

# Add edges
builder.add_edge(START, "search_fanout")
builder.add_edge("search_fanout", "researcher")
builder.add_edge("researcher", "script_generator")
builder.add_edge("script_generator", "clip_retriever")
builder.add_edge("clip_retriever", "assembly")
builder.add_edge("assembly", END)

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
        "retrieved_clips": final_state.get("retrieved_clips"),
        "final_video_path": final_state.get("final_video_path"),
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

    if result.get("final_video_path"):
        print(f"\n🎥 Final Video: {result['final_video_path']}")

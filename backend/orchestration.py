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
from video_utils import combine_videos, cut_video
from veo_agent import get_veo_agent

# --- Custom Models for Video Processing ---
class ClipTimestamps(BaseModel):
    start_time: str = Field(description="Start time in MM:SS or HH:MM:SS format")
    end_time: str = Field(description="End time in MM:SS or HH:MM:SS format")
from veo_agent import get_veo_agent


# Load environment variables
load_dotenv()

from google import genai
from google.genai import types

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
    veo_generated_videos: List[Dict[str, Any]]  # Veo AI-generated videos
    veo_failed_videos: List[Dict[str, Any]]     # Failed Veo generations
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
    if not download_url:
        raise Exception("Download URL missing from Publer response")
        
    encoded_url = quote(str(download_url), safe='')
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
    retries = 4
    base_wait = 4

    for attempt in range(retries + 1):
        try:
            result = client.skills.execute_skill(
                skill_id="aa967d12-c544-41b4-9169-da7d44c295c7",
                parameters={
                    "query": query,
                    "limit": 5
                }
            )
            return [video['video_url'] for video in result.result['data']['videos']]
        except Exception as e:
            if attempt == retries:
                print(f"YouTube Scraper failed after {retries} retries: {e}")
                raise e
            
            wait_time = base_wait * (2 ** attempt)
            print(f"YouTube Scraper failed (Attempt {attempt+1}/{retries+1}). Retrying in {wait_time}s... Error: {e}")
            time.sleep(wait_time)

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
# PARALLEL MEDIA MANUFACTURING
# -----------------------------------------------------------------------------

async def process_veo_segments(script: Dict[str, Any]) -> Dict[str, List[Any]]:
    """
    Async helper to generate all Veo videos in parallel.
    """
    segments = script.get('segments', [])
    ai_segments = [s for s in segments if s.get('type') == 'ai_generated']
    
    if not ai_segments:
        return {"generated": [], "failed": []}
        
    print(f"🎥 Starting parallel generation for {len(ai_segments)} Veo segments...")
    veo_agent = get_veo_agent()
    video_dir = os.path.join(os.path.dirname(__file__), "videos", "veo_generated")
    os.makedirs(video_dir, exist_ok=True)
    
    # Define single task function
    async def process_single_segment(seg, delay):
        if delay > 0:
            # Stagger requests to avoid rate limits
            await asyncio.sleep(delay)
            
        try:
            # We add a small stagger or just run them all. BrowserUse/VeoAgent handles rate limits.
            print(f"  > Triggering Veo for Segment {seg.get('order')} (after {delay}s delay)")
            result = await veo_agent.generate_video(seg)
            
            # Download
            video_path = os.path.join(video_dir, f"veo_segment_{seg.get('order')}.mp4")
            await veo_agent.download_video(result['video_uri'], video_path)
            
            result['local_path'] = video_path
            return {"status": "success", "data": result}
        except Exception as e:
            print(f"  ❌ Veo Segment {seg.get('order')} failed: {e}")
            return {"status": "error", "error": str(e), "segment_order": seg.get('order')}

    # Run all tasks concurrently with stagger
    tasks = [process_single_segment(s, i * 6) for i, s in enumerate(ai_segments)]
    results = await asyncio.gather(*tasks)
    
    generated = [r['data'] for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] == 'error']
    
    return {"generated": generated, "failed": failed}


async def process_clip_workflow(script: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Async helper to run the Retrieval -> Analysis -> Cut pipeline for real clips.
    """
    segments = script.get('segments', [])
    clip_segments = [s for s in segments if s.get('type') == 'real_clip']
    
    if not clip_segments:
        return []
        
    print(f"🎬 Starting parallel clip retrieval for {len(clip_segments)} segments...")
    
    # We can also parallelize the retrieval part if we want, but let's 
    # keep the logic clear: Loop safely or use gather.
    # Given the requested change, let's try to parallelize the *search & retrieval* 
    # but maybe keep analysis sequential or parallel too. 
    # Let's go full parallel for speed.
    
    videos_dir = os.path.join(os.path.dirname(__file__), "videos")
    
    async def process_single_clip(seg):
        ref_data = seg.get('clip_reference') or seg
        query = ref_data.get('search_query')
        description = ref_data.get('description', 'Unknown clip')
        order = seg.get('order')
        
        result_clip = {
            "segment_order": order,
            "query": query,
            "error": None
        }
        
        if not query:
            return None
            
        try:
            print(f"  > Searching for: {query} (Seg {order})")
            # 1. Search (Sync tool wrapper via thread)
            candidates = await asyncio.to_thread(youtube_scraper_tool.invoke, {"query": query})
            
            if not candidates:
                print(f"  ⚠️ No videos found for: {query}")
                return None
                
            best_url = candidates[0]
            
            # 2. Retrieve (Sync function via thread)
            print(f"  > Retrieving: {best_url}")
            video_obj = await asyncio.to_thread(retrieve_video, best_url)
            
            # 3. Analyze & Cut (Sync function via thread)
            # We need to port the logic from analyze_and_cut_node or wrap it.
            # Let's wrap the specific analysis logic here for self-containment 
            # or ideally call a helper. To save space, I'll inline a simplified version
            # or call the sync function logic. 
            
            # For robustness, let's do the analysis here.
            # Initialize Gemini locally for this thread
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            client = genai.Client(api_key=api_key)
            
            video_path = video_obj.path
            
            # Upload
            print(f"  > Uploading for analysis: {video_path}")
            video_file = await asyncio.to_thread(client.files.upload, file=video_path)
            
            # Wait for processing
            while video_file.state.name == "PROCESSING":
                await asyncio.sleep(2)
                video_file = await asyncio.to_thread(client.files.get, name=video_file.name)
                
            if video_file.state.name == "FAILED":
                raise Exception("Gemini video processing failed")
                
            # Prompt
            target_duration = seg.get('duration_seconds', 8)
            prompt_text = (
                f"Find the BEST continuous {target_duration}-second segment in this video that matches: "
                f"'{description}'. Return start and end timestamps."
            )
            
            print(f"  > Analyzing content: {query}")
            response = await asyncio.to_thread(
                client.models.generate_content,
                model="gemini-2.0-flash",
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_uri(file_uri=video_file.uri, mime_type=video_file.mime_type),
                            types.Part.from_text(text=prompt_text),
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ClipTimestamps,
                    temperature=0.1
                )
            )
            
            timestamps: ClipTimestamps = response.parsed
            
            # Cut
            output_filename = f"cut_{uuid.uuid4()}.mp4"
            output_path = os.path.join(videos_dir, output_filename)
            
            await asyncio.to_thread(
                cut_video, 
                video_path, 
                output_path, 
                timestamps.start_time, 
                timestamps.end_time
            )
            
            result_clip.update({
                "video_path": output_path,
                "original_path": video_path,
                "timestamps": timestamps.model_dump(),
                "original_url": best_url
            })
            print(f"  ✅ Clip ready: {output_path} (Seg {order})")
            return result_clip
            
        except Exception as e:
            print(f"  ❌ Clip processing failed for '{query}': {e}")
            result_clip["error"] = str(e)
            return result_clip # Return basic info or failure

    tasks = [process_single_clip(s) for s in clip_segments]
    results = await asyncio.gather(*tasks)
    
    return [r for r in results if r is not None and r.get('video_path')]


async def media_production_logic(state: NarrativeState) -> Dict[str, Any]:
    """
    Async logic for MASTER NODE: Runs Veo Generation and Clip Retrieval in parallel.
    """
    print(f"\n{'='*60}")
    print("🏭 MEDIA PRODUCTION NODE (PARALLEL)")
    print(f"{'='*60}")
    
    script = state.get('script')
    if not script:
        return {"error": "No script found"}
    
    # Launch both workflows concurrently
    veo_task = process_veo_segments(script)
    clip_task = process_clip_workflow(script)
    
    # Wait for both to finish
    veo_results, clip_results = await asyncio.gather(veo_task, clip_task)
    
    return {
        "veo_generated_videos": veo_results["generated"],
        "veo_failed_videos": veo_results["failed"],
        "retrieved_clips": clip_results,
        "current_phase": "media_produced"
    }

def media_production_node(state: NarrativeState) -> Dict[str, Any]:
    """
    Synchronous wrapper for parallel media production.
    """
    try:
        # Check if there's already a running loop (e.g. in some test envs)
        loop = asyncio.get_running_loop()
        # If we are here, we are already in a loop, so we shouldn't use run().
        # But graph.invoke is sync, so it blocks. This is tricky.
        # Ideally we use graph.ainvoke if we are in async context.
        # For now, assuming typical sync usage:
        return loop.run_until_complete(media_production_logic(state))
    except RuntimeError:
        # No running loop, safe to create one
        return asyncio.run(media_production_logic(state))


# -----------------------------------------------------------------------------
# ASSEMBLY NODE
# -----------------------------------------------------------------------------
def assembly_node(state: NarrativeState):
    """
    Concatenates retrieved clips and Veo videos into a final video.
    """
    print("--- ASSEMBLY NODE STARTING ---")
    retrieved_clips = state.get('retrieved_clips', [])
    veo_videos = state.get('veo_generated_videos', [])
    
    all_clips = []
    
    # Normalize clip structures for sorting
    for clip in retrieved_clips:
        all_clips.append({
            "order": clip.get('segment_order', 0),
            "path": clip.get('video_path'),
            "type": "real_clip"
        })
        
    for video in veo_videos:
        # Veo agent returns 'local_path'
        all_clips.append({
            "order": video.get('segment_order', 0),
            "path": video.get('local_path'),
            "type": "ai_generated"
        })
    
    if not all_clips:
         return {"current_phase": "assembly_failed", "error": "No clips (Veo or Real) to assemble"}

    try:
        # Sort by segment order
        sorted_clips = sorted(all_clips, key=lambda x: x['order'])
        
        # Strict check: Ensure ALL expected video files exist
        video_paths = []
        missing_files = []
        
        for clip in sorted_clips:
            path = clip.get('path')
            if path and os.path.exists(path):
                video_paths.append(path)
            else:
                missing_files.append(path or f"unknown_path_seg_{clip['order']}")
        
        if missing_files:
            error_msg = f"Missing video files for assembly: {', '.join(missing_files)}"
            print(f"❌ {error_msg}")
            return {"current_phase": "assembly_failed", "error": error_msg}
            
        print(f"Video paths ({len(video_paths)}):")
        for p in video_paths:
            print(f" - {p}")

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
builder.add_node("search_fanout", fanout_search_node)
builder.add_node("researcher", research_node)
builder.add_node("script_generator", script_generation_node)
builder.add_node("media_production", media_production_node) # PARALLEL NODE
builder.add_node("assembly", assembly_node)

# Add edges - Full pipeline:
# Research → Script → Media Production (Veo + Clips) → Assembly
builder.add_edge(START, "search_fanout")
builder.add_edge("search_fanout", "researcher")
builder.add_edge("researcher", "script_generator")
builder.add_edge("script_generator", "media_production")
builder.add_edge("media_production", "assembly")
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
        "research_results": {},
        "research_context": None,
        "script": None,
        "retrieved_clips": [],
        "veo_generated_videos": [],
        "veo_failed_videos": [],
        "current_phase": "starting",
        "error": None,
        "final_video_path": None,
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
        "veo_generated_videos": final_state.get("veo_generated_videos"),
        "veo_failed_videos": final_state.get("veo_failed_videos"),
        "final_video_path": final_state.get("final_video_path"),
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

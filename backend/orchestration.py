from typing import Annotated, TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use_sdk import BrowserUse
import requests
import time
import os
import json
from dataclasses import dataclass
import asyncio
from dotenv import load_dotenv

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

async def _async_retrieve_video(url: str) -> Video:
    """
    Internal async function to use Browser Use SDK skills API to download a video.
    Uses the YouTube Shorts search skill to find and download videos.
    """
    print(f"--- BROWSER-USE SDK RETRIEVING VIDEO: {url} ---")
    
    # Get API key from environment
    api_key = os.getenv("BROWSER_USE_API_KEY")
    if not api_key:
        raise ValueError("BROWSER_USE_API_KEY not found in environment variables")
    
    # Initialize Browser Use SDK client
    client = BrowserUse(api_key=api_key)
    
    # Define the video directory
    video_dir = os.path.join(os.path.dirname(__file__), "videos")
    os.makedirs(video_dir, exist_ok=True)
    
    # Extract search query from URL or use URL as query
    # For YouTube URLs, we could parse the video ID, but for now use a generic approach
    # If the user provides a direct URL, we'll use it as the search query
    query = url
    
    # Execute the YouTube Shorts search skill
    skill_id = "e0d2a054-18a8-4667-a0cc-1f5e250b24fe"
    
    result = await client.skills.execute_skill(
        skill_id=skill_id,
        parameters={
            "query": query,
            "limit": 1  # We only need one video
        }
    )
    
    print(f"Skill execution result: {result}")
    
    # Parse the result to get video information
    if not result:
        raise ValueError("Skill returned no results")
    
    # Extract video data from result
    # This structure may need adjustment based on actual skill response
    video_data = result if isinstance(result, dict) else result[0] if isinstance(result, list) else {}
    
    # Get video download URL or file from the skill result
    download_url = video_data.get("downloadUrl") or video_data.get("url")
    title = video_data.get("title", "downloaded_video")
    
    if not download_url:
        raise ValueError("No download URL found in skill result")
    
    # Download the video file
    video_response = requests.get(download_url)
    video_response.raise_for_status()
    
    # Generate filename from title
    safe_filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_filename = safe_filename[:100]  # Limit length
    file_name = f"{safe_filename}.mp4"
    
    # Save to local directory
    local_path = os.path.join(video_dir, file_name)
    with open(local_path, "wb") as f:
        f.write(video_response.content)
    
    print(f"Video downloaded to: {local_path}")
    
    return Video(path=local_path, title=title)


def retrieve_video(url: str) -> Video:
    """
    Synchronous wrapper for the async video retrieval.
    """
    return asyncio.run(_async_retrieve_video(url))


@tool
def youtube_scraper_tool(query: str):
    """
    Search and scrape YouTube for videos related to the query.
    """
    # Shell code: To be implemented with actual scraping logic
    return f"YouTube scrape results for: {query} (STUB)"

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
# Note: Ensure GOOGLE_API_KEY is in your .env
llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview")
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
    A single node that acts as the primary researcher.
    """
    print("--- RESEARCH NODE STARTING ---")
    query = state['messages'][-1].content
    
    # In a real implementation, you'd bind tools to an LLM here.
    # For this shell, we'll just simulate calling the tools.
    yt_data = youtube_scraper_tool.invoke({"query": query})
    sm_data = social_media_researcher_tool.invoke({"platform": "X", "topic": query})
    
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

def run_workflow(prompt: str):
    """
    Executes the LangGraph workflow with the given prompt.
    """
    initial_state = {
        "messages": [HumanMessage(content=prompt)],
        "research_results": {},
        "current_status": "starting"
    }
    
    # Execute synchronously within the process spawned by generation_service
    final_output = graph.invoke(initial_state)
    return final_output

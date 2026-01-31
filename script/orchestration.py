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
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import json

# =============================================================================
# AGENT IMPORTS - Add your agents here
# =============================================================================
from models import SportsNarrativeScript, ResearchContext
from research_agent import research_agent
from script_generator import script_generator

# TODO: Import future agents as they're built
# from video_agent import video_agent           # Veo video generation
# from clip_agent import clip_agent             # Real sports clip retrieval
# from audio_agent import audio_agent           # Voice/audio generation
# from assembly_agent import assembly_agent     # Final video assembly


# =============================================================================
# SHARED STATE - All agents read/write to this
# =============================================================================

class NarrativeState(TypedDict):
    """
    The shared state for the entire workflow.
    Each agent adds its output here for other agents to use.
    """
    
    # -------------------------------------------------------------------------
    # INPUT
    # -------------------------------------------------------------------------
    prompt: str
    duration_seconds: int
    
    # -------------------------------------------------------------------------
    # WORKFLOW TRACKING
    # -------------------------------------------------------------------------
    messages: Annotated[List[BaseMessage], "Conversation history"]
    current_phase: str
    error: Optional[str]
    
    # -------------------------------------------------------------------------
    # RESEARCH AGENT OUTPUT
    # -------------------------------------------------------------------------
    research_context: Optional[Dict[str, Any]]
    research_status: str
    
    # -------------------------------------------------------------------------
    # SCRIPT AGENT OUTPUT
    # -------------------------------------------------------------------------
    script: Optional[Dict[str, Any]]
    script_status: str
    
    # -------------------------------------------------------------------------
    # VIDEO AGENT OUTPUT (TODO: Veo integration)
    # -------------------------------------------------------------------------
    # video_segments: Optional[List[Dict[str, Any]]]  # Generated video clips
    # video_status: str
    
    # -------------------------------------------------------------------------
    # CLIP AGENT OUTPUT (TODO: Real clip retrieval)
    # -------------------------------------------------------------------------
    # retrieved_clips: Optional[List[Dict[str, Any]]]  # Found sports clips
    # clip_status: str
    
    # -------------------------------------------------------------------------
    # AUDIO AGENT OUTPUT (TODO: Voice generation)
    # -------------------------------------------------------------------------
    # audio_tracks: Optional[List[Dict[str, Any]]]  # Generated audio
    # audio_status: str
    
    # -------------------------------------------------------------------------
    # ASSEMBLY AGENT OUTPUT (TODO: Final video)
    # -------------------------------------------------------------------------
    # final_video: Optional[Dict[str, Any]]  # Assembled video
    # assembly_status: str


# =============================================================================
# NODE FUNCTIONS - Each agent gets a node
# =============================================================================

# -----------------------------------------------------------------------------
# RESEARCH NODE
# -----------------------------------------------------------------------------
def research_node(state: NarrativeState) -> Dict[str, Any]:
    """
    🔍 RESEARCH AGENT
    
    Purpose: Gather sports information from the web
    Input: prompt (from state)
    Output: research_context (facts, figures, timeline, sources)
    """
    print(f"\n{'='*60}")
    print("🔍 RESEARCH NODE - Starting sports research...")
    print(f"{'='*60}")
    
    prompt = state["prompt"]
    print(f"Researching: {prompt}")
    
    try:
        research_context = research_agent.research_storyline_sync(prompt)
        
        print(f"\n✅ Research complete!")
        print(f"   - Found {len(research_context.key_facts)} key facts")
        print(f"   - Identified {len(research_context.key_figures)} key figures")
        print(f"   - {len(research_context.sources)} sources gathered")
        
        return {
            "research_context": research_context.model_dump(),
            "research_status": "completed",
            "current_phase": "research_complete",
            "messages": [
                AIMessage(content=f"Research completed for: {', '.join(research_context.key_figures[:5])}")
            ]
        }
        
    except Exception as e:
        print(f"\n❌ Research failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "research_status": "failed",
            "error": str(e),
            "current_phase": "research_failed"
        }


# -----------------------------------------------------------------------------
# SCRIPT GENERATION NODE
# -----------------------------------------------------------------------------
def script_generation_node(state: NarrativeState) -> Dict[str, Any]:
    """
    📝 SCRIPT AGENT
    
    Purpose: Generate broadcast script from research
    Input: research_context (from research node)
    Output: script (structured script with segments, dialogue, clips)
    """
    print(f"\n{'='*60}")
    print("📝 SCRIPT GENERATION NODE - Creating broadcast script...")
    print(f"{'='*60}")
    
    research_dict = state["research_context"]
    if not research_dict:
        return {
            "script_status": "failed",
            "error": "No research context available",
            "current_phase": "script_failed"
        }
    
    research_context = ResearchContext(**research_dict)
    duration = state.get("duration_seconds", 150)
    
    print(f"Generating {duration}s script for: {research_context.original_prompt}")
    
    try:
        script = script_generator.generate_script_sync(research_context, duration)
        
        ai_segments = sum(1 for s in script.segments if s.segment_type == "ai_generated")
        clip_segments = sum(1 for s in script.segments if s.segment_type == "real_clip")
        
        print(f"\n✅ Script generated!")
        print(f"   - Title: {script.title}")
        print(f"   - {ai_segments} AI-generated segments")
        print(f"   - {clip_segments} real clip references")
        print(f"   - {len(script.hosts)} hosts")
        print(f"   - Total duration: {script.total_duration_seconds}s")
        
        return {
            "script": script.model_dump(),
            "script_status": "completed",
            "current_phase": "script_complete",
            "messages": [
                AIMessage(content=f"Script '{script.title}' generated with {len(script.segments)} segments")
            ]
        }
        
    except Exception as e:
        print(f"\n❌ Script generation failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "script_status": "failed",
            "error": str(e),
            "current_phase": "script_failed"
        }


# -----------------------------------------------------------------------------
# VIDEO GENERATION NODE (TODO)
# -----------------------------------------------------------------------------
def video_generation_node(state: NarrativeState) -> Dict[str, Any]:
    """
    🎬 VIDEO AGENT (TODO: Implement with Veo)
    
    Purpose: Generate AI video segments using Veo
    Input: script (AI segments with visual descriptions)
    Output: video_segments (generated video files/URLs)
    
    Example implementation:
    ```
    from video_agent import video_agent
    
    script = state["script"]
    ai_segments = [s for s in script["segments"] if s["segment_type"] == "ai_generated"]
    
    video_segments = []
    for seg in ai_segments:
        video = video_agent.generate_video(
            prompt=seg["ai_segment"]["visual_description"],
            duration=seg["ai_segment"]["duration_seconds"]
        )
        video_segments.append(video)
    
    return {"video_segments": video_segments, "video_status": "completed"}
    ```
    """
    print(f"\n{'='*60}")
    print("🎬 VIDEO GENERATION NODE - (Not yet implemented)")
    print(f"{'='*60}")
    
    # TODO: Implement Veo video generation
    return {
        "current_phase": "video_skipped",
        "messages": [AIMessage(content="Video generation not yet implemented")]
    }


# -----------------------------------------------------------------------------
# CLIP RETRIEVAL NODE (TODO)
# -----------------------------------------------------------------------------
def clip_retrieval_node(state: NarrativeState) -> Dict[str, Any]:
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
        "current_phase": "assembly_skipped",
        "messages": [AIMessage(content="Video assembly not yet implemented")]
    }


# -----------------------------------------------------------------------------
# OUTPUT NODE
# -----------------------------------------------------------------------------
def output_node(state: NarrativeState) -> Dict[str, Any]:
    """
    📤 OUTPUT NODE
    
    Purpose: Finalize workflow and return results
    """
    print(f"\n{'='*60}")
    print("📤 OUTPUT NODE - Finalizing...")
    print(f"{'='*60}")
    
    if state.get("error"):
        print(f"⚠️ Workflow completed with errors: {state['error']}")
        return {"current_phase": "completed_with_errors"}
    
    script = state.get("script")
    if script:
        print(f"✅ Workflow complete!")
        print(f"   Script ready: {script.get('title', 'Untitled')}")
    
    return {"current_phase": "completed"}


# =============================================================================
# CONDITIONAL ROUTING - Decide which path to take
# =============================================================================

def route_after_research(state: NarrativeState) -> str:
    """Decide what to do after research."""
    if state.get("research_status") == "completed" and state.get("research_context"):
        return "generate_script"
    else:
        return "output"  # Skip to output on error


def route_after_script(state: NarrativeState) -> str:
    """Decide what to do after script generation."""
    if state.get("script_status") == "completed" and state.get("script"):
        # TODO: When video agent is ready, route to "generate_video"
        return "output"
    else:
        return "output"


# =============================================================================
# GRAPH CONSTRUCTION - Wire up all the agents
# =============================================================================

def build_narrative_graph() -> StateGraph:
    """
    Build the LangGraph workflow.
    
    CURRENT FLOW:
        START → research → generate_script → output → END
    
    FUTURE FLOW (when all agents are ready):
        START → research → generate_script → generate_video → retrieve_clips 
              → generate_audio → assemble → output → END
    """
    
    builder = StateGraph(NarrativeState)
    
    # -------------------------------------------------------------------------
    # ADD NODES - Each agent is a node
    # -------------------------------------------------------------------------
    builder.add_node("research", research_node)
    builder.add_node("generate_script", script_generation_node)
    builder.add_node("output", output_node)
    
    # TODO: Uncomment when agents are ready
    # builder.add_node("generate_video", video_generation_node)
    # builder.add_node("retrieve_clips", clip_retrieval_node)
    # builder.add_node("generate_audio", audio_generation_node)
    # builder.add_node("assemble", assembly_node)
    
    # -------------------------------------------------------------------------
    # ADD EDGES - Connect the nodes
    # -------------------------------------------------------------------------
    
    # Start with research
    builder.add_edge(START, "research")
    
    # After research, conditionally go to script or output
    builder.add_conditional_edges(
        "research",
        route_after_research,
        {
            "generate_script": "generate_script",
            "output": "output"
        }
    )
    
    # After script, go to output (or video when ready)
    builder.add_conditional_edges(
        "generate_script",
        route_after_script,
        {
            "output": "output",
            # TODO: Add more routes when agents are ready
            # "generate_video": "generate_video",
        }
    )
    
    # TODO: Wire up future agents
    # builder.add_edge("generate_video", "retrieve_clips")
    # builder.add_edge("retrieve_clips", "generate_audio")
    # builder.add_edge("generate_audio", "assemble")
    # builder.add_edge("assemble", "output")
    
    # Output goes to END
    builder.add_edge("output", END)
    
    return builder.compile()


# Compile the graph
graph = build_narrative_graph()


# =============================================================================
# PUBLIC API - Called by main.py / generation_service.py
# =============================================================================

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

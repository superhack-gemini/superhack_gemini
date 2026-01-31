"""
Pydantic models for Veo-ready script output.
Clean format for video generation pipeline.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class Host(BaseModel):
    """A broadcast host/analyst."""
    name: str
    role: str
    appearance: str  # Detailed visual description


class Studio(BaseModel):
    """Studio setting - included in every AI segment for consistency."""
    description: str
    lighting: str
    color_scheme: str


class AISegment(BaseModel):
    """A single AI-generated video segment (max 8 seconds)."""
    order: int
    type: str = "ai_generated"
    duration_seconds: int = Field(..., le=8, description="Max 8 seconds")
    
    # Visual prompt for Veo (includes studio + hosts + action)
    visual_prompt: str = Field(..., description="Complete Veo prompt with studio, hosts, action")
    
    # Dialogue
    speaker: str
    dialogue: str
    delivery: str  # How to deliver (tone, emotion)
    
    # Camera
    camera: str
    
    # Graphics
    graphics: List[str] = []
    
    # Include studio & hosts in each segment for Veo consistency
    studio: Studio
    hosts: List[Host]


class RealClipSegment(BaseModel):
    """A real sports clip to insert."""
    order: int
    type: str = "real_clip"
    duration_seconds: int = Field(..., le=8, description="Max 8 seconds")
    
    description: str
    search_query: str  # YouTube search query
    context: str  # Why this clip matters


class VeoScript(BaseModel):
    """
    Complete script ready for Veo generation.
    Clean format: ai_order_1, ai_order_2, real_clip, ai_order_3, ai_order_4...
    """
    title: str
    storyline: str
    total_duration_seconds: int
    
    # Global visual style (reference)
    studio: Studio
    hosts: List[Host]
    
    # All segments in order
    segments: List[dict]  # Mix of AISegment and RealClipSegment as dicts
    
    # Research used
    research_summary: str
    key_facts: List[str]


# Keep these for research agent
class ResearchResult(BaseModel):
    query: str
    source: str
    title: str
    snippet: str
    url: Optional[str] = None
    relevance_score: float = 0.9


class ResearchContext(BaseModel):
    original_prompt: str
    storyline_summary: str
    key_facts: List[str]
    key_figures: List[str]
    timeline: List[str]
    controversy_points: List[str]
    emotional_angles: List[str]
    sources: List[ResearchResult]

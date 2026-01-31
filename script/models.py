"""
Pydantic models for structured sports narrative scripts.
These models define the format for a primetime sports analysis show.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum


class Mood(str, Enum):
    """The emotional tone of a segment."""
    DRAMATIC = "dramatic"
    EXCITING = "exciting"
    SOMBER = "somber"
    CELEBRATORY = "celebratory"
    TENSE = "tense"
    REFLECTIVE = "reflective"
    CONTROVERSIAL = "controversial"


class Host(BaseModel):
    """A broadcast host/analyst."""
    name: str = Field(..., description="Name of the host")
    role: str = Field(..., description="Role (e.g., 'Lead Anchor', 'Analyst', 'Former Player')")
    appearance: str = Field(..., description="Visual description for AI generation")
    position: str = Field(..., description="Where they're seated/standing in studio")


class StudioSetting(BaseModel):
    """The broadcast studio environment."""
    description: str = Field(..., description="Overall studio description for Veo")
    lighting: str = Field(..., description="Lighting mood and style")
    background_elements: List[str] = Field(..., description="Screens, graphics, props visible")
    color_scheme: str = Field(..., description="Primary colors and aesthetic")
    time_of_day: str = Field(..., description="When the show is 'airing'")


class RealClipReference(BaseModel):
    """Reference to a real sports clip to be inserted."""
    clip_id: str = Field(..., description="Unique identifier for this clip slot")
    description: str = Field(..., description="What the clip should show")
    search_query: str = Field(..., description="Query to find this clip")
    duration_seconds: int = Field(default=5, description="Suggested clip length")
    context: str = Field(..., description="Why this clip is relevant here")
    transition_in: str = Field(default="cut", description="How to transition into clip")
    transition_out: str = Field(default="cut", description="How to transition out of clip")


class DialogueLine(BaseModel):
    """A single line of dialogue from a host."""
    speaker: str = Field(..., description="Name of the host speaking")
    text: str = Field(..., description="What they say")
    delivery: str = Field(..., description="How they deliver it (tone, gesture notes)")
    camera_direction: Optional[str] = Field(None, description="Camera angle/movement")


class AIGeneratedSegment(BaseModel):
    """An AI-generated broadcast segment (hosts talking in studio)."""
    segment_id: str = Field(..., description="Unique identifier")
    segment_type: Literal["intro", "analysis", "debate", "transition", "outro"] = Field(...)
    duration_seconds: int = Field(..., description="Target duration")
    mood: Mood = Field(..., description="Emotional tone")
    
    # Visual direction for Veo
    visual_description: str = Field(..., description="Full visual scene description for Veo")
    camera_notes: str = Field(..., description="Camera work suggestions")
    
    # The actual content
    dialogue: List[DialogueLine] = Field(..., description="The dialogue for this segment")
    
    # Graphics/lower thirds
    graphics: Optional[List[str]] = Field(None, description="On-screen graphics/text")


class ScriptSegment(BaseModel):
    """A segment in the script - either AI-generated or a clip reference."""
    order: int = Field(..., description="Order in the script")
    segment_type: Literal["ai_generated", "real_clip"] = Field(...)
    ai_segment: Optional[AIGeneratedSegment] = None
    clip_reference: Optional[RealClipReference] = None


class SportsNarrativeScript(BaseModel):
    """The complete script for a sports narrative video."""
    
    # Metadata
    title: str = Field(..., description="Episode/segment title")
    storyline: str = Field(..., description="The sports storyline being covered")
    total_duration_seconds: int = Field(..., description="Target total duration")
    
    # Setting
    studio: StudioSetting = Field(..., description="The broadcast studio setting")
    hosts: List[Host] = Field(..., description="The hosts/analysts")
    
    # Premise
    premise: str = Field(..., description="The narrative premise and angle")
    key_points: List[str] = Field(..., description="Main points to cover")
    
    # The actual script segments
    segments: List[ScriptSegment] = Field(..., description="Ordered list of segments")
    
    # Research data used
    research_sources: List[str] = Field(default=[], description="Sources used for research")
    
    def get_total_ai_duration(self) -> int:
        """Calculate total duration of AI-generated segments."""
        return sum(
            seg.ai_segment.duration_seconds 
            for seg in self.segments 
            if seg.ai_segment
        )
    
    def get_total_clip_duration(self) -> int:
        """Calculate total duration of real clips."""
        return sum(
            seg.clip_reference.duration_seconds 
            for seg in self.segments 
            if seg.clip_reference
        )


class ResearchResult(BaseModel):
    """Research findings from web scraping."""
    query: str
    source: str
    title: str
    snippet: str
    url: Optional[str] = None
    date: Optional[str] = None
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)


class ResearchContext(BaseModel):
    """Aggregated research context for script generation."""
    original_prompt: str
    storyline_summary: str
    key_facts: List[str]
    key_figures: List[str]  # Players, coaches, teams mentioned
    timeline: List[str]  # Key events in chronological order
    controversy_points: List[str]  # Debatable aspects
    emotional_angles: List[str]  # Human interest elements
    sources: List[ResearchResult]

"""
Pydantic models for structured sports narrative scripts.
Optimized for Veo video generation (8 second max per clip).
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
    ANALYTICAL = "analytical"
    INTENSE = "intense"
    HOPEFUL = "hopeful"
    URGENT = "urgent"


class Host(BaseModel):
    """A broadcast host/analyst."""
    name: str = Field(..., description="Name of the host")
    role: str = Field(..., description="Role (e.g., 'Lead Anchor', 'Analyst', 'Former Player')")
    appearance: str = Field(..., description="Visual description for AI generation")
    position: str = Field(..., description="Where they're seated/standing in studio")


class VisualStyle(BaseModel):
    """Consistent visual style for ALL AI-generated clips (cohesion)."""
    studio_description: str = Field(..., description="Detailed studio setting - same for all clips")
    lighting_setup: str = Field(..., description="Exact lighting - warm/cool, dramatic/soft")
    color_palette: str = Field(..., description="Primary and accent colors")
    camera_style: str = Field(..., description="Camera movement style - steady/dynamic/cinematic")
    graphics_style: str = Field(..., description="Lower thirds, overlays style")
    overall_mood: str = Field(..., description="Consistent mood/tone across all clips")


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
    duration_seconds: int = Field(default=5, ge=1, le=8, description="Max 8 seconds for Veo")
    context: str = Field(..., description="Why this clip is relevant here")
    transition_in: str = Field(default="cut", description="How to transition into clip")
    transition_out: str = Field(default="cut", description="How to transition out of clip")


class DialogueLine(BaseModel):
    """A single line of dialogue from a host."""
    speaker: str = Field(..., description="Name of the host speaking")
    text: str = Field(..., description="What they say")
    delivery: str = Field(..., description="How they deliver it (tone, gesture notes)")
    camera_direction: Optional[str] = Field(None, description="Camera angle/movement")


class VeoClip(BaseModel):
    """A single 8-second max Veo clip."""
    clip_id: str = Field(..., description="Unique identifier")
    duration_seconds: int = Field(..., ge=1, le=8, description="1-8 seconds max for Veo")
    visual_prompt: str = Field(..., description="Detailed Veo prompt for this specific clip")
    dialogue_text: Optional[str] = Field(None, description="What's being said during this clip")
    speaker: Optional[str] = Field(None, description="Who's speaking")
    camera_angle: str = Field(..., description="Camera angle/movement for this clip")
    action: str = Field(..., description="What's happening in frame")


class AIGeneratedSegment(BaseModel):
    """An AI-generated broadcast segment - can chain multiple 8-sec Veo clips."""
    segment_id: str = Field(..., description="Unique identifier")
    segment_type: str = Field(..., description="Type: intro, analysis, debate, transition, outro, etc.")
    total_duration_seconds: int = Field(..., description="Total duration of all clips combined")
    mood: str = Field(..., description="Emotional tone (dramatic, exciting, tense, etc.)")
    
    # Multiple Veo clips (each 8 sec max) that chain together
    veo_clips: List[VeoClip] = Field(..., description="1-2 Veo clips (8 sec each max)")
    
    # Full dialogue for this segment
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
    
    # VISUAL COHESION - Same style across ALL Veo clips
    visual_style: VisualStyle = Field(..., description="Consistent visual style for all AI clips")
    
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
            seg.ai_segment.total_duration_seconds 
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
    
    def get_all_veo_clips(self) -> List[VeoClip]:
        """Get all Veo clips in order for video generation."""
        clips = []
        for seg in self.segments:
            if seg.ai_segment and seg.ai_segment.veo_clips:
                clips.extend(seg.ai_segment.veo_clips)
        return clips


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
    key_figures: List[str]
    timeline: List[str]
    controversy_points: List[str]
    emotional_angles: List[str]
    sources: List[ResearchResult]

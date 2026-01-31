"""
Simple models for Veo script generation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class Host(BaseModel):
    name: str
    role: str
    appearance: str


class Studio(BaseModel):
    description: str
    lighting: str
    color_scheme: str


class VeoScript(BaseModel):
    """Complete script ready for Veo generation."""
    title: str
    storyline: str
    total_duration_seconds: int
    studio: Studio
    hosts: List[Host]
    segments: List[dict]
    research_summary: str
    key_facts: List[str]


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

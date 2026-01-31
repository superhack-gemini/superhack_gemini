"""
Script generation agent using Google Gemini.
Optimized for Veo video generation (8 second max per clip, visual cohesion).
"""
import os
import json
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types
from models import SportsNarrativeScript, ResearchContext


class ScriptGenerator:
    """
    Generates sports broadcast scripts optimized for Veo.
    - Each Veo clip is MAX 8 seconds
    - Can chain 2 clips (16 sec max) for longer segments
    - All clips share consistent visual style for cohesion
    """
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("No GOOGLE_API_KEY found!")
        
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.0-flash"
        print("[ScriptGenerator] ✅ Configured for Veo (8-sec clips)")

    def _get_script_prompt(self, research: ResearchContext, duration_seconds: int = 120) -> str:
        """Create prompt for Veo-optimized script generation."""
        return f"""Generate a sports broadcast script optimized for Veo AI video generation.

CRITICAL VEO CONSTRAINTS:
- Each Veo clip is MAX 8 SECONDS
- For longer segments, chain 2 clips back-to-back (max 16 seconds)
- ALL clips must share the SAME visual style for cohesion

STORYLINE: {research.original_prompt}

RESEARCH:
{research.storyline_summary}

KEY FACTS: {json.dumps(research.key_facts[:5])}
KEY FIGURES: {json.dumps(research.key_figures[:5])}
CONTROVERSY: {json.dumps(research.controversy_points[:3])}

Generate JSON with this EXACT structure:

{{
    "title": "Compelling episode title",
    "storyline": "{research.original_prompt}",
    "total_duration_seconds": {duration_seconds},
    
    "visual_style": {{
        "studio_description": "DETAILED studio description - modern sports broadcast set with curved anchor desk, 3 hosts seated, large LED screens behind showing sports graphics. Dark wood and brushed metal aesthetic.",
        "lighting_setup": "Dramatic low-key lighting, warm key lights on hosts, cool blue accent lighting on background screens, subtle rim lighting for depth",
        "color_palette": "Primary: Deep navy blue. Accent: Gold and red. Background: Charcoal gray",
        "camera_style": "Smooth cinematic movements, slow push-ins for dramatic moments, steady shots for analysis",
        "graphics_style": "Modern ESPN-style lower thirds, clean sans-serif fonts, animated transitions",
        "overall_mood": "Professional primetime sports broadcast with dramatic tension"
    }},
    
    "studio": {{
        "description": "Same as visual_style.studio_description",
        "lighting": "Same as visual_style.lighting_setup",
        "background_elements": ["Large LED screen", "Team logos", "Stats ticker", "Sports graphics"],
        "color_scheme": "Same as visual_style.color_palette",
        "time_of_day": "Primetime evening broadcast"
    }},
    
    "hosts": [
        {{
            "name": "Unique Host Name",
            "role": "Lead Anchor",
            "appearance": "DETAILED: Age, ethnicity, clothing (specific colors), demeanor. Example: 40s African American woman, burgundy blazer, confident posture",
            "position": "Center desk"
        }},
        {{
            "name": "Another Host",
            "role": "Analyst",
            "appearance": "DETAILED description - make visually distinct",
            "position": "Left of center"
        }},
        {{
            "name": "Third Host",
            "role": "Former Player",
            "appearance": "DETAILED description - athletic build",
            "position": "Right of center"
        }}
    ],
    
    "premise": "The narrative hook for this story",
    "key_points": ["Point 1", "Point 2", "Point 3"],
    
    "segments": [
        {{
            "order": 1,
            "segment_type": "ai_generated",
            "ai_segment": {{
                "segment_id": "intro_1",
                "segment_type": "intro",
                "total_duration_seconds": 12,
                "mood": "dramatic",
                "veo_clips": [
                    {{
                        "clip_id": "intro_1a",
                        "duration_seconds": 6,
                        "visual_prompt": "EXACT COPY of visual_style details + specific action: Wide shot of sports broadcast studio, three hosts at curved desk, LED screens showing team highlights, camera slowly pushes in toward center host who begins speaking with serious expression",
                        "dialogue_text": "What the host says during this 6 seconds",
                        "speaker": "Host Name",
                        "camera_angle": "Wide shot, slow push in",
                        "action": "Host speaking to camera, dramatic intro"
                    }},
                    {{
                        "clip_id": "intro_1b",
                        "duration_seconds": 6,
                        "visual_prompt": "SAME studio setting as intro_1a, now medium shot of center host, same lighting and colors, host gesturing while speaking passionately",
                        "dialogue_text": "Continuation of dialogue",
                        "speaker": "Host Name",
                        "camera_angle": "Medium shot",
                        "action": "Host continuing dramatic intro"
                    }}
                ],
                "dialogue": [
                    {{
                        "speaker": "Host Name",
                        "text": "Full dialogue for this segment",
                        "delivery": "Dramatic, building tension",
                        "camera_direction": "Push in"
                    }}
                ],
                "graphics": ["LOWER THIRD: Show Title"]
            }},
            "clip_reference": null
        }},
        {{
            "order": 2,
            "segment_type": "real_clip",
            "ai_segment": null,
            "clip_reference": {{
                "clip_id": "clip_1",
                "description": "Real sports footage to insert",
                "search_query": "Specific YouTube search query",
                "duration_seconds": 6,
                "context": "Why this clip matters here",
                "transition_in": "cut",
                "transition_out": "cut"
            }}
        }}
    ],
    
    "research_sources": ["ESPN", "NFL.com"]
}}

CRITICAL RULES:
1. Each veo_clip.duration_seconds MUST be 1-8 seconds (MAX 8!)
2. Each veo_clip.visual_prompt MUST include the EXACT visual_style details for cohesion
3. Chain 2 veo_clips for segments longer than 8 seconds (max 16 total)
4. Real clips (segment_type: real_clip) are also max 8 seconds
5. Create 5-7 segments alternating ai_generated and real_clip
6. Total duration should be approximately {duration_seconds} seconds
7. Make dialogue natural but dramatic - this is primetime sports TV

Return ONLY the JSON."""

    def generate_script_sync(
        self, 
        research: ResearchContext, 
        duration_seconds: int = 120
    ) -> SportsNarrativeScript:
        """Generate a Veo-optimized script."""
        print(f"\n[ScriptGenerator] 📝 Generating {duration_seconds}s script...")
        print(f"[ScriptGenerator] Veo mode: 8-sec clips, visual cohesion")
        
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=self._get_script_prompt(research, duration_seconds),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.85,
                )
            )
            
            script_data = json.loads(response.text)
            script = SportsNarrativeScript(**script_data)
            
            # Count clips
            total_veo_clips = len(script.get_all_veo_clips())
            
            print(f"[ScriptGenerator] ✅ Script generated!")
            print(f"   - Title: {script.title}")
            print(f"   - {len(script.segments)} segments")
            print(f"   - {total_veo_clips} Veo clips (8-sec each)")
            print(f"   - Total: {script.total_duration_seconds}s")
            
            return script
            
        except Exception as e:
            print(f"[ScriptGenerator] ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"Script generation failed: {e}")


script_generator = ScriptGenerator()

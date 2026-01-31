"""
Script generation for Veo video pipeline.
Output format: ai_order_1, ai_order_2, real_clip, ai_order_3, ai_order_4...
Each AI segment includes hosts + studio for visual consistency.
"""
import os
import json
from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types
from models import VeoScript, ResearchContext


class ScriptGenerator:
    """
    Generates Veo-ready scripts.
    - Each AI segment is MAX 8 seconds
    - Each AI segment includes full hosts + studio description
    - Formula: ai, ai, clip, ai, ai, clip...
    """
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("No GOOGLE_API_KEY found!")
        
        self.client = genai.Client(api_key=api_key)
        print("[ScriptGenerator] ✅ Ready for Veo (8-sec max, hosts in each segment)")

    def _get_prompt(self, research: ResearchContext, duration: int = 120) -> str:
        return f"""Generate a sports broadcast script for Veo AI video generation.

RULES:
1. Each AI segment is MAX 8 SECONDS
2. Each AI segment must include FULL studio and hosts description (for visual consistency)
3. Follow this pattern: ai_order_1, ai_order_2, real_clip_1, ai_order_3, ai_order_4, real_clip_2...
4. Real clips are also max 8 seconds

STORYLINE: {research.original_prompt}

RESEARCH:
{research.storyline_summary}

KEY FACTS: {json.dumps(research.key_facts[:5])}
KEY FIGURES: {json.dumps(research.key_figures[:4])}

Generate this EXACT JSON structure:

{{
    "title": "Compelling title",
    "storyline": "{research.original_prompt}",
    "total_duration_seconds": {duration},
    
    "studio": {{
        "description": "Modern ESPN-style sports broadcast studio. Curved dark wood anchor desk with chrome accents. Three leather chairs. Massive 85-inch curved LED screen behind hosts showing dynamic sports graphics. NFL shield logo illuminated on floor. Sleek, professional atmosphere.",
        "lighting": "Dramatic low-key lighting. Warm key lights on hosts faces. Cool blue LED accents on background screens. Subtle rim lighting for depth separation.",
        "color_scheme": "Primary: Deep navy blue. Accent: Gold and crimson red. Background: Charcoal gray."
    }},
    
    "hosts": [
        {{
            "name": "Marcus Webb",
            "role": "Lead Anchor",
            "appearance": "African American male, early 40s. Wearing fitted charcoal suit with burgundy tie. Clean-shaven, confident posture, seated center at anchor desk."
        }},
        {{
            "name": "Sarah Chen",
            "role": "NFL Analyst",
            "appearance": "Asian American female, mid-30s. Wearing cream blazer over black top. Hair pulled back professionally. Seated left side of desk."
        }},
        {{
            "name": "Tony Martinez",
            "role": "Former Player Analyst",
            "appearance": "Latino male, late 30s, athletic build. Navy sport coat over open collar shirt. Energetic demeanor. Seated right side of desk."
        }}
    ],
    
    "segments": [
        {{
            "order": 1,
            "type": "ai_generated",
            "duration_seconds": 8,
            "visual_prompt": "Modern ESPN-style sports broadcast studio. Curved dark wood anchor desk with three hosts seated. Massive LED screen behind showing [RELEVANT IMAGERY]. Dramatic low-key lighting with warm key lights on hosts. Deep navy blue and gold color scheme. Camera slowly pushes in on center host Marcus Webb who speaks with serious expression.",
            "speaker": "Marcus Webb",
            "dialogue": "Opening line - dramatic hook about the storyline",
            "delivery": "Serious, measured, building tension",
            "camera": "Wide shot, slow push in to medium",
            "graphics": ["LOWER THIRD: Show Title"],
            "studio": {{
                "description": "Modern ESPN-style sports broadcast studio...",
                "lighting": "Dramatic low-key lighting...",
                "color_scheme": "Deep navy blue, gold, crimson"
            }},
            "hosts": [
                {{"name": "Marcus Webb", "role": "Lead Anchor", "appearance": "African American male, early 40s, charcoal suit..."}},
                {{"name": "Sarah Chen", "role": "Analyst", "appearance": "Asian American female, mid-30s, cream blazer..."}},
                {{"name": "Tony Martinez", "role": "Former Player", "appearance": "Latino male, late 30s, navy sport coat..."}}
            ]
        }},
        {{
            "order": 2,
            "type": "ai_generated",
            "duration_seconds": 8,
            "visual_prompt": "Same studio setting. Medium shot of Sarah Chen. Same lighting and colors. She gestures while making analytical point.",
            "speaker": "Sarah Chen",
            "dialogue": "Analytical point about key facts",
            "delivery": "Analytical, citing stats",
            "camera": "Medium shot on Sarah",
            "graphics": ["STAT GRAPHIC: Key statistic"],
            "studio": {{ ... same studio ... }},
            "hosts": [ ... same hosts ... ]
        }},
        {{
            "order": 3,
            "type": "real_clip",
            "duration_seconds": 8,
            "description": "What the real sports footage shows",
            "search_query": "Specific YouTube search query to find this clip",
            "context": "Why this clip is relevant here"
        }},
        {{
            "order": 4,
            "type": "ai_generated",
            "duration_seconds": 8,
            "visual_prompt": "Same studio. Close-up on Tony Martinez. Same lighting. He speaks passionately with hand gestures.",
            "speaker": "Tony Martinez",
            "dialogue": "Former player perspective",
            "delivery": "Passionate, emphatic",
            "camera": "Close-up on Tony",
            "graphics": [],
            "studio": {{ ... same studio ... }},
            "hosts": [ ... same hosts ... ]
        }},
        {{
            "order": 5,
            "type": "ai_generated",
            "duration_seconds": 8,
            "visual_prompt": "Same studio. Three-shot of all hosts. Debate energy. Quick cuts between speakers.",
            "speaker": "Marcus Webb",
            "dialogue": "Debate or transition point",
            "delivery": "Mediating discussion",
            "camera": "Three-shot, dynamic cuts",
            "graphics": ["DEBATE GRAPHIC"],
            "studio": {{ ... same studio ... }},
            "hosts": [ ... same hosts ... ]
        }},
        {{
            "order": 6,
            "type": "real_clip",
            "duration_seconds": 8,
            "description": "Another key sports moment",
            "search_query": "Search query for clip",
            "context": "Relevance"
        }}
    ],
    
    "research_summary": "{research.storyline_summary[:500]}",
    "key_facts": {json.dumps(research.key_facts[:5])}
}}

IMPORTANT:
- Create 8-10 segments following pattern: ai, ai, clip, ai, ai, clip, ai, ai
- Each AI segment MUST include full studio and hosts objects (copy the same values)
- Each AI segment is EXACTLY 8 seconds or less
- visual_prompt must describe the SAME studio for every AI segment
- Make dialogue natural but concise (fits in 8 seconds)
- Real clip search queries should find actual YouTube sports footage

Return ONLY valid JSON."""

    def generate_script_sync(self, research: ResearchContext, duration: int = 120) -> VeoScript:
        """Generate Veo-ready script."""
        print(f"\n[ScriptGenerator] 📝 Generating {duration}s Veo script...")
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=self._get_prompt(research, duration),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.8,
                )
            )
            
            data = json.loads(response.text)
            script = VeoScript(**data)
            
            ai_count = sum(1 for s in script.segments if s.get("type") == "ai_generated")
            clip_count = sum(1 for s in script.segments if s.get("type") == "real_clip")
            
            print(f"[ScriptGenerator] ✅ Generated!")
            print(f"   - Title: {script.title}")
            print(f"   - {ai_count} AI segments (8-sec each)")
            print(f"   - {clip_count} real clips")
            print(f"   - Total: {len(script.segments)} segments")
            
            return script
            
        except Exception as e:
            print(f"[ScriptGenerator] ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            raise


script_generator = ScriptGenerator()

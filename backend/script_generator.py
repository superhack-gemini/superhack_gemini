"""
Script generation for Veo video pipeline.
STRICT visual consistency - same simple studio for ALL AI clips.
"""
import os
import json
from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types
from models import VeoScript, ResearchContext

# STRICT STUDIO TEMPLATE - Same for ALL AI clips
STUDIO_PROMPT = """Simple dark broadcast studio. Black background with subtle blue accent lighting. 
Single curved news desk, dark gray surface. Three hosts seated at desk facing camera. 
Clean, minimal set with no distracting elements. Soft key lighting on hosts faces."""

STUDIO = {
    "description": "Simple dark broadcast studio with black background, subtle blue accent lighting, single curved dark gray news desk, three hosts seated facing camera, minimal clean set",
    "lighting": "Soft key lighting on hosts, subtle blue accent glow from behind, dark background",
    "color_scheme": "Black background, dark gray desk, blue accent lighting"
}

HOSTS = [
    {
        "name": "Marcus Webb",
        "role": "Lead Anchor",
        "appearance": "African American male, 40s, charcoal suit, burgundy tie, seated center"
    },
    {
        "name": "Sarah Chen", 
        "role": "Analyst",
        "appearance": "Asian American female, 30s, cream blazer, seated left"
    },
    {
        "name": "Tony Martinez",
        "role": "Former Player",
        "appearance": "Latino male, 30s, navy sport coat, seated right"
    }
]


class ScriptGenerator:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("No GOOGLE_API_KEY found! Set GOOGLE_API_KEY environment variable.")
        
        self.client = genai.Client(api_key=api_key)
        print("[ScriptGenerator] ✅ Ready")

    def _get_prompt(self, research: ResearchContext, duration: int = 120) -> str:
        return f"""Generate a sports broadcast script for Veo AI video.

STRICT RULES:
1. Each AI segment MAX 8 SECONDS
2. ALL AI segments use this EXACT same studio prompt:
   "{STUDIO_PROMPT}"
3. Pattern: ai, ai, real_clip, ai, ai, real_clip, ai, real_clip, ai
4. EXACTLY 3 real clips total
5. EXACTLY 6 AI segments total

REAL CLIP SEARCH QUERIES - KEEP GENERIC:
- Use simple searches like: "seahawks touchdown highlights", "team name playoffs", "player name catch"
- Do NOT use specific dates, exact scores, or complex phrases
- Keep it 2-4 words max for searchability

STORYLINE: {research.original_prompt}
SUMMARY: {research.storyline_summary[:500]}
FACTS: {json.dumps(research.key_facts[:4])}

Generate JSON:

{{
    "title": "Short compelling title",
    "storyline": "{research.original_prompt}",
    "total_duration_seconds": {duration},
    
    "studio": {{
        "description": "{STUDIO['description']}",
        "lighting": "{STUDIO['lighting']}",
        "color_scheme": "{STUDIO['color_scheme']}"
    }},
    
    "hosts": {json.dumps(HOSTS)},
    
    "segments": [
        {{
            "order": 1,
            "type": "ai_generated",
            "duration_seconds": 8,
            "visual_prompt": "{STUDIO_PROMPT} Camera on center host Marcus Webb, medium shot, he speaks seriously.",
            "speaker": "Marcus Webb",
            "dialogue": "Opening hook line about the story",
            "delivery": "Serious",
            "camera": "Medium shot center host",
            "graphics": ["LOWER THIRD: Title"],
            "studio": {json.dumps(STUDIO)},
            "hosts": {json.dumps(HOSTS)}
        }},
        {{
            "order": 2,
            "type": "ai_generated",
            "duration_seconds": 8,
            "visual_prompt": "{STUDIO_PROMPT} Camera on Sarah Chen left side, medium shot.",
            "speaker": "Sarah Chen",
            "dialogue": "Context and key background",
            "delivery": "Informative",
            "camera": "Medium shot left host",
            "graphics": [],
            "studio": {json.dumps(STUDIO)},
            "hosts": {json.dumps(HOSTS)}
        }},
        {{
            "order": 3,
            "type": "real_clip",
            "duration_seconds": 8,
            "description": "Key highlight moment",
            "search_query": "GENERIC 2-4 word search like: team name highlights",
            "context": "Why this matters"
        }},
        {{
            "order": 4,
            "type": "ai_generated", 
            "duration_seconds": 8,
            "visual_prompt": "{STUDIO_PROMPT} Camera on Tony Martinez right side, close-up.",
            "speaker": "Tony Martinez",
            "dialogue": "Former player insight",
            "delivery": "Passionate",
            "camera": "Close-up right host",
            "graphics": [],
            "studio": {json.dumps(STUDIO)},
            "hosts": {json.dumps(HOSTS)}
        }},
        {{
            "order": 5,
            "type": "ai_generated",
            "duration_seconds": 8, 
            "visual_prompt": "{STUDIO_PROMPT} Wide shot all three hosts.",
            "speaker": "Marcus Webb",
            "dialogue": "Question or transition",
            "delivery": "Engaged",
            "camera": "Wide shot all hosts",
            "graphics": [],
            "studio": {json.dumps(STUDIO)},
            "hosts": {json.dumps(HOSTS)}
        }},
        {{
            "order": 6,
            "type": "real_clip",
            "duration_seconds": 8,
            "description": "Another key moment",
            "search_query": "GENERIC search like: player name touchdown",
            "context": "Relevance"
        }},
        {{
            "order": 7,
            "type": "ai_generated",
            "duration_seconds": 8,
            "visual_prompt": "{STUDIO_PROMPT} Camera on Sarah Chen, medium shot.",
            "speaker": "Sarah Chen", 
            "dialogue": "Analysis point",
            "delivery": "Thoughtful",
            "camera": "Medium shot left host",
            "graphics": [],
            "studio": {json.dumps(STUDIO)},
            "hosts": {json.dumps(HOSTS)}
        }},
        {{
            "order": 8,
            "type": "real_clip",
            "duration_seconds": 8,
            "description": "Final highlight",
            "search_query": "GENERIC search like: team celebration",
            "context": "Closing visual"
        }},
        {{
            "order": 9,
            "type": "ai_generated",
            "duration_seconds": 8,
            "visual_prompt": "{STUDIO_PROMPT} Camera slowly pushes in on Marcus Webb center.",
            "speaker": "Marcus Webb",
            "dialogue": "Closing statement",
            "delivery": "Conclusive",
            "camera": "Push in on center host",
            "graphics": ["LOWER THIRD: Show title"],
            "studio": {json.dumps(STUDIO)},
            "hosts": {json.dumps(HOSTS)}
        }}
    ],
    
    "research_summary": "{research.storyline_summary[:300]}",
    "key_facts": {json.dumps(research.key_facts[:4])}
}}

CRITICAL: 
- Every visual_prompt MUST start with exactly: "{STUDIO_PROMPT}"
- search_query for real clips MUST be generic and short (2-4 words)
- Keep dialogue short (fits in 8 seconds when spoken)
- EXACTLY 6 AI segments, EXACTLY 3 real clips

Return ONLY valid JSON."""

    def generate_script_sync(self, research: ResearchContext, duration: int = 120) -> VeoScript:
        print(f"\n[ScriptGenerator] 📝 Generating script...")
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=self._get_prompt(research, duration),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7,
                )
            )
            
            data = json.loads(response.text)
            script = VeoScript(**data)
            
            ai_count = sum(1 for s in script.segments if s.get("type") == "ai_generated")
            clip_count = sum(1 for s in script.segments if s.get("type") == "real_clip")
            
            print(f"[ScriptGenerator] ✅ Done! {ai_count} AI clips, {clip_count} real clips")
            
            return script
            
        except Exception as e:
            print(f"[ScriptGenerator] ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            raise


script_generator = ScriptGenerator()

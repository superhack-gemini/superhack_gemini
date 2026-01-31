"""
Script generation agent using Google Gemini.
Generates structured sports broadcast scripts from research context.
"""
import os
import json
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import google.generativeai as genai
from models import (
    SportsNarrativeScript, 
    ResearchContext,
    StudioSetting,
    Host,
    ScriptSegment,
    AIGeneratedSegment,
    RealClipReference,
    DialogueLine,
    Mood
)


class ScriptGenerator:
    """
    Generates sports broadcast scripts using Gemini.
    """
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            self.has_api = True
        else:
            print("[ScriptGenerator] Warning: No GOOGLE_API_KEY set, using mock generation")
            self.model = None
            self.has_api = False
    
    def _get_system_prompt(self) -> str:
        """System prompt for script generation."""
        return """You are an expert sports broadcast scriptwriter for a primetime ESPN-style analysis show.
Your task is to create compelling, dramatic scripts that blend AI-generated studio segments with real sports footage clips.

The script should feel like a high-production sports documentary/analysis show with:
- Dramatic narrative tension
- Expert analysis and debate
- Emotional storytelling
- Strategic use of real game footage

IMPORTANT: You must return ONLY valid JSON matching the exact schema provided. No markdown, no explanations, just the JSON object."""

    def _get_script_prompt(self, research: ResearchContext, duration_seconds: int = 150) -> str:
        """Create the prompt for script generation."""
        return f"""Generate a {duration_seconds}-second sports broadcast script for this storyline:

STORYLINE: {research.original_prompt}

RESEARCH SUMMARY:
{research.storyline_summary}

KEY FACTS:
{json.dumps(research.key_facts, indent=2)}

KEY FIGURES:
{json.dumps(research.key_figures, indent=2)}

CONTROVERSY POINTS:
{json.dumps(research.controversy_points, indent=2)}

EMOTIONAL ANGLES:
{json.dumps(research.emotional_angles, indent=2)}

---

Generate a JSON script with this EXACT structure:
{{
    "title": "Episode title",
    "storyline": "The storyline being covered",
    "total_duration_seconds": {duration_seconds},
    "studio": {{
        "description": "Detailed studio description for AI video generation",
        "lighting": "Lighting description",
        "background_elements": ["element1", "element2"],
        "color_scheme": "Color description",
        "time_of_day": "Evening/Night"
    }},
    "hosts": [
        {{
            "name": "Host name",
            "role": "Lead Anchor",
            "appearance": "Detailed appearance for AI generation",
            "position": "Center desk"
        }}
    ],
    "premise": "The narrative premise",
    "key_points": ["point1", "point2"],
    "segments": [
        {{
            "order": 1,
            "segment_type": "ai_generated",
            "ai_segment": {{
                "segment_id": "intro_1",
                "segment_type": "intro",
                "duration_seconds": 20,
                "mood": "dramatic",
                "visual_description": "Detailed visual for Veo",
                "camera_notes": "Camera directions",
                "dialogue": [
                    {{
                        "speaker": "Host name",
                        "text": "What they say",
                        "delivery": "How they say it",
                        "camera_direction": "Close-up"
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
                "description": "What the clip shows",
                "search_query": "Query to find clip",
                "duration_seconds": 8,
                "context": "Why this clip matters",
                "transition_in": "dramatic fade",
                "transition_out": "cut"
            }}
        }}
    ],
    "research_sources": ["source1", "source2"]
}}

REQUIREMENTS:
1. Create 5-7 segments alternating between ai_generated and real_clip
2. Start with an intro segment, end with an outro
3. Make dialogue natural, dramatic, and insightful
4. Include specific clip descriptions that could be found on YouTube/sports archives
5. Use mood values: dramatic, exciting, somber, celebratory, tense, reflective, controversial
6. Segment types for ai_segment: intro, analysis, debate, transition, outro
7. Make visual_description detailed enough for Veo to generate realistic studio footage
8. Total duration should be approximately {duration_seconds} seconds

Return ONLY the JSON, no other text."""

    async def generate_script(
        self, 
        research: ResearchContext, 
        duration_seconds: int = 150
    ) -> SportsNarrativeScript:
        """
        Generate a complete broadcast script from research context.
        """
        if not self.has_api:
            return self._generate_mock_script(research, duration_seconds)
        
        try:
            prompt = self._get_script_prompt(research, duration_seconds)
            
            response = self.model.generate_content(
                [self._get_system_prompt(), prompt],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.8,
                )
            )
            
            # Parse the JSON response
            script_data = json.loads(response.text)
            
            # Validate and create the Pydantic model
            return SportsNarrativeScript(**script_data)
            
        except Exception as e:
            print(f"[ScriptGenerator] Error generating script: {e}")
            return self._generate_mock_script(research, duration_seconds)
    
    def _generate_mock_script(
        self, 
        research: ResearchContext, 
        duration_seconds: int
    ) -> SportsNarrativeScript:
        """Generate a mock script for testing without API."""
        
        # Determine the storyline type for customization
        prompt_lower = research.original_prompt.lower()
        
        if "49ers" in prompt_lower:
            return self._generate_49ers_script(research, duration_seconds)
        elif "seahawks" in prompt_lower:
            return self._generate_seahawks_script(research, duration_seconds)
        elif "belichick" in prompt_lower:
            return self._generate_belichick_script(research, duration_seconds)
        else:
            return self._generate_generic_script(research, duration_seconds)
    
    def _generate_49ers_script(self, research: ResearchContext, duration: int) -> SportsNarrativeScript:
        """Generate script for 49ers storyline."""
        return SportsNarrativeScript(
            title="Fallen Favorites: The 49ers' Championship Collapse",
            storyline=research.original_prompt,
            total_duration_seconds=duration,
            studio=StudioSetting(
                description="A sleek, modern ESPN-style studio with dark wood accents and brushed metal surfaces. A curved anchor desk sits center frame with three large 4K monitors behind displaying 49ers imagery in muted red and gold. The NFL shield logo illuminates from the floor.",
                lighting="Dramatic low-key lighting with warm amber accents. Key lights create defined shadows on hosts' faces. Background monitors provide cool blue contrast.",
                background_elements=[
                    "Three 85-inch curved displays showing 49ers highlights",
                    "Illuminated NFL shield logo on floor",
                    "Scrolling stats ticker at bottom of back wall",
                    "Subtle fog/haze for depth"
                ],
                color_scheme="Deep burgundy and gold accents against charcoal gray and black. Cool blue backlighting for contrast.",
                time_of_day="Late evening, 10 PM primetime slot"
            ),
            hosts=[
                Host(
                    name="Marcus Webb",
                    role="Lead Anchor",
                    appearance="African American male, early 40s, wearing a fitted charcoal suit with a burgundy tie. Clean-shaven, confident demeanor, expressive hand gestures.",
                    position="Center of curved desk, facing camera"
                ),
                Host(
                    name="Sarah Chen",
                    role="NFL Analyst",
                    appearance="Asian American female, mid-30s, wearing a cream blazer over black top. Hair pulled back professionally, intense analytical expression.",
                    position="Left side of desk, angled toward center"
                ),
                Host(
                    name="Tony Romo Jr.",
                    role="Former Player Analyst",
                    appearance="Caucasian male, late 30s, athletic build visible in navy sport coat. Energetic, uses hands to demonstrate plays.",
                    position="Right side of desk, slight lean forward"
                )
            ],
            premise="The San Francisco 49ers entered the season as Super Bowl favorites, but a cascade of injuries and crucial mistakes led to a shocking collapse. Tonight, we examine what went wrong and whether this championship window has closed.",
            key_points=[
                "Christian McCaffrey's absence devastated the offense",
                "Kyle Shanahan's play-calling under scrutiny",
                "Brock Purdy struggled without weapons",
                "The championship window may be closing"
            ],
            segments=[
                # SEGMENT 1: Dramatic Intro
                ScriptSegment(
                    order=1,
                    segment_type="ai_generated",
                    ai_segment=AIGeneratedSegment(
                        segment_id="intro_1",
                        segment_type="intro",
                        duration_seconds=25,
                        mood=Mood.DRAMATIC,
                        visual_description="Camera slowly pushes in on Marcus Webb at center desk. Monitors behind show faded 49ers Super Bowl hopes. Lighting is moody, dramatic. Studio has weight of disappointment.",
                        camera_notes="Start wide, slow push to medium shot. Cut to two-shot with Sarah on 'championship dreams.'",
                        dialogue=[
                            DialogueLine(
                                speaker="Marcus Webb",
                                text="They were supposed to be playing for a championship right now. The San Francisco 49ers... favorites by nearly everyone to hoist the Lombardi Trophy.",
                                delivery="Somber, measured pace, slight shake of head",
                                camera_direction="Slow push in to medium close-up"
                            ),
                            DialogueLine(
                                speaker="Marcus Webb",
                                text="Instead, they're watching from home. Tonight... we ask the question the Faithful are dreading.",
                                delivery="Building intensity, lean forward",
                                camera_direction="Hold on medium shot"
                            ),
                            DialogueLine(
                                speaker="Sarah Chen",
                                text="What went wrong with the 49ers?",
                                delivery="Direct, serious, looking into camera",
                                camera_direction="Quick cut to Sarah close-up"
                            )
                        ],
                        graphics=["LOWER THIRD: SPECIAL REPORT - FALLEN FAVORITES", "49ERS LOGO WATERMARK"]
                    )
                ),
                
                # SEGMENT 2: Real Clip - Preseason Hype
                ScriptSegment(
                    order=2,
                    segment_type="real_clip",
                    clip_reference=RealClipReference(
                        clip_id="clip_preseason",
                        description="Montage of 49ers preseason predictions and Super Bowl hype. Analysts picking SF to win it all. Team celebrating training camp.",
                        search_query="49ers 2024 super bowl predictions preseason favorites",
                        duration_seconds=8,
                        context="Establishes the high expectations before showing the fall",
                        transition_in="dramatic fade from studio",
                        transition_out="slow dissolve"
                    )
                ),
                
                # SEGMENT 3: Analysis - The Injuries
                ScriptSegment(
                    order=3,
                    segment_type="ai_generated",
                    ai_segment=AIGeneratedSegment(
                        segment_id="analysis_1",
                        segment_type="analysis",
                        duration_seconds=30,
                        mood=Mood.SOMBER,
                        visual_description="Three-shot of all hosts. Tony has injury report graphic on tablet. Mood is clinical, examining a tragedy.",
                        camera_notes="Start three-shot, cut to Tony close-up when discussing CMC, use over-shoulder shot for tablet graphic.",
                        dialogue=[
                            DialogueLine(
                                speaker="Tony Romo Jr.",
                                text="Look, I've been there. You build a team around certain guys, and when they go down, everything changes. Christian McCaffrey was the engine of that offense.",
                                delivery="Empathetic, drawing from experience, gesturing with hands",
                                camera_direction="Medium shot, slight push in"
                            ),
                            DialogueLine(
                                speaker="Sarah Chen",
                                text="The numbers are staggering, Tony. Without McCaffrey, the 49ers averaged 4.2 yards per carry compared to 5.8 with him. That's not just a drop - that's a different offense entirely.",
                                delivery="Analytical, referencing notes, precise",
                                camera_direction="Cut to Sarah with stat graphic over shoulder"
                            ),
                            DialogueLine(
                                speaker="Marcus Webb",
                                text="And it wasn't just CMC. Deebo Samuel, Brandon Aiyuk missing time, the offensive line shuffling every week...",
                                delivery="Listing with gravity, counting on fingers",
                                camera_direction="Two-shot Marcus and Sarah"
                            )
                        ],
                        graphics=["INJURY GRAPHIC: 15 Players to IR", "STAT: 4.2 vs 5.8 YPC"]
                    )
                ),
                
                # SEGMENT 4: Real Clip - McCaffrey Injury
                ScriptSegment(
                    order=4,
                    segment_type="real_clip",
                    clip_reference=RealClipReference(
                        clip_id="clip_cmc_injury",
                        description="Christian McCaffrey injury footage, trainers helping him off field, sideline shots of his reaction and coaches' concern.",
                        search_query="Christian McCaffrey injury 2024 49ers sideline",
                        duration_seconds=10,
                        context="Visual proof of the devastating loss that changed the season",
                        transition_in="cut",
                        transition_out="fade to black"
                    )
                ),
                
                # SEGMENT 5: Debate - Shanahan
                ScriptSegment(
                    order=5,
                    segment_type="ai_generated",
                    ai_segment=AIGeneratedSegment(
                        segment_id="debate_1",
                        segment_type="debate",
                        duration_seconds=35,
                        mood=Mood.CONTROVERSIAL,
                        visual_description="Energy shifts. Hosts lean in. Split screen graphics ready. This is the hot take segment - lighting shifts slightly warmer, more urgent.",
                        camera_notes="Quick cuts between speakers, use split screen for disagreement, dramatic push-ins on strong statements.",
                        dialogue=[
                            DialogueLine(
                                speaker="Sarah Chen",
                                text="But here's what I can't get past - Kyle Shanahan has now had multiple chances at championships and found ways to let them slip. At what point do we question the coaching?",
                                delivery="Challenging, leaning forward, firm",
                                camera_direction="Push in on Sarah"
                            ),
                            DialogueLine(
                                speaker="Tony Romo Jr.",
                                text="Whoa, whoa. Come on, Sarah. The man has been to two Super Bowls, an NFC Championship game. You can't coach your way out of losing your best players!",
                                delivery="Defensive, animated, hands up",
                                camera_direction="Quick cut to Tony, slightly wider to capture gestures"
                            ),
                            DialogueLine(
                                speaker="Sarah Chen",
                                text="Then explain the fourth quarter play-calling, Tony. Explain going conservative with a lead. AGAIN.",
                                delivery="Pointed, emphatic, not backing down",
                                camera_direction="Split screen Sarah/Tony"
                            ),
                            DialogueLine(
                                speaker="Marcus Webb",
                                text="The 49ers blew a double-digit lead in three different games this season. Three. That's not just bad luck.",
                                delivery="Mediating but making a point, referencing stat",
                                camera_direction="Cut to Marcus, graphic appears"
                            )
                        ],
                        graphics=["SPLIT SCREEN: SHANAHAN DEFENSE vs CRITICISM", "STAT: 3 Blown Double-Digit Leads"]
                    )
                ),
                
                # SEGMENT 6: Real Clip - Blown Lead
                ScriptSegment(
                    order=6,
                    segment_type="real_clip",
                    clip_reference=RealClipReference(
                        clip_id="clip_blown_lead",
                        description="49ers blowing fourth quarter lead. Opposition scoring, Niners sideline dejection, fans with hands on heads.",
                        search_query="49ers blown lead fourth quarter 2024 collapse",
                        duration_seconds=12,
                        context="Evidence of the recurring problem - inability to close games",
                        transition_in="hard cut for impact",
                        transition_out="slow fade"
                    )
                ),
                
                # SEGMENT 7: Outro - The Future
                ScriptSegment(
                    order=7,
                    segment_type="ai_generated",
                    ai_segment=AIGeneratedSegment(
                        segment_id="outro_1",
                        segment_type="outro",
                        duration_seconds=30,
                        mood=Mood.REFLECTIVE,
                        visual_description="Mood shifts to reflective. Lighting softens slightly. Hosts settle back, contemplative. 49ers sunset imagery on monitors behind.",
                        camera_notes="Start wide three-shot, end on slow push to Marcus for final question.",
                        dialogue=[
                            DialogueLine(
                                speaker="Tony Romo Jr.",
                                text="Look, the reality is this - championship windows don't stay open forever. The cap hits are coming. Decisions have to be made.",
                                delivery="Sobering, honest, slight sadness",
                                camera_direction="Medium shot Tony"
                            ),
                            DialogueLine(
                                speaker="Sarah Chen",
                                text="The 49ers need to ask themselves hard questions this offseason. Not just about the roster, but about the identity of this team going forward.",
                                delivery="Thoughtful, measured conclusion",
                                camera_direction="Sarah medium shot"
                            ),
                            DialogueLine(
                                speaker="Marcus Webb",
                                text="A team built to win now... watching others play for the ultimate prize. The question for the Faithful tonight: Was this the year that got away, or the beginning of the end?",
                                delivery="Powerful close, direct to camera, letting question hang",
                                camera_direction="Slow push to Marcus close-up, hold"
                            )
                        ],
                        graphics=["LOWER THIRD: SPECIAL REPORT - FALLEN FAVORITES", "SHOW LOGO FADE IN"]
                    )
                )
            ],
            research_sources=[
                "ESPN 49ers Coverage",
                "The Athletic - San Francisco",
                "NFL Network Analysis",
                "49ers Official Injury Reports"
            ]
        )

    def _generate_seahawks_script(self, research: ResearchContext, duration: int) -> SportsNarrativeScript:
        """Generate script for Seahawks storyline."""
        return SportsNarrativeScript(
            title="The Emerald Ascent: Seattle's Unlikely Championship Run",
            storyline=research.original_prompt,
            total_duration_seconds=duration,
            studio=StudioSetting(
                description="A modern broadcast studio with Seattle-inspired design. Cool blue and green LED accents frame large displays showing Seahawks highlights. Space Needle silhouette visible in background graphics. Clean, energetic aesthetic.",
                lighting="Bright, optimistic lighting with green accent LEDs. Clean key lighting on hosts with dynamic background colors.",
                background_elements=[
                    "Massive LED wall with Seahawks action shots",
                    "Seattle skyline silhouette graphics",
                    "Real-time social media feed display",
                    "Playoff bracket graphic"
                ],
                color_scheme="Seattle Seahawks navy blue and action green against silver and white. Energetic, vibrant palette.",
                time_of_day="Prime time, electric atmosphere"
            ),
            hosts=[
                Host(
                    name="Marcus Webb",
                    role="Lead Anchor",
                    appearance="African American male, early 40s, wearing a tailored navy suit with subtle green pocket square. Energetic, smiling.",
                    position="Center desk"
                ),
                Host(
                    name="Sarah Chen",
                    role="NFL Analyst",
                    appearance="Asian American female, mid-30s, wearing an emerald green blazer. Animated, excited expression.",
                    position="Left of center"
                ),
                Host(
                    name="Tony Romo Jr.",
                    role="Former Player Analyst",
                    appearance="Caucasian male, late 30s, navy sport coat, excited energy, ready to break down plays.",
                    position="Right of center"
                )
            ],
            premise="Nobody gave them a chance. The Seattle Seahawks were supposed to be rebuilding. Instead, they're on the doorstep of the Super Bowl. This is the story of an incredible run and the doubters who got it wrong.",
            key_points=[
                "Geno Smith's redemption arc",
                "Mike Macdonald's defensive transformation",
                "Young core exceeding expectations",
                "Silencing the doubters"
            ],
            segments=[
                ScriptSegment(
                    order=1,
                    segment_type="ai_generated",
                    ai_segment=AIGeneratedSegment(
                        segment_id="intro_1",
                        segment_type="intro",
                        duration_seconds=25,
                        mood=Mood.EXCITING,
                        visual_description="Studio buzzing with energy. Green LED accents pulsing. Monitors showing Seahawks celebration footage. Hosts visibly excited.",
                        camera_notes="Dynamic opening, quick cuts, energy building.",
                        dialogue=[
                            DialogueLine(
                                speaker="Marcus Webb",
                                text="They said Seattle was done. They said Geno Smith was a placeholder. They said this team was two years away from competing.",
                                delivery="Building energy, counting off criticisms, smile growing",
                                camera_direction="Medium shot, slight movement"
                            ),
                            DialogueLine(
                                speaker="Sarah Chen",
                                text="Well, someone forgot to tell the Seahawks!",
                                delivery="Excited, almost laughing",
                                camera_direction="Quick cut to Sarah"
                            ),
                            DialogueLine(
                                speaker="Tony Romo Jr.",
                                text="This team is for REAL, and tonight we break down how Seattle shocked the NFL world!",
                                delivery="Maximum energy, gesturing emphatically",
                                camera_direction="Wide shot capturing enthusiasm"
                            )
                        ],
                        graphics=["LOWER THIRD: THE EMERALD ASCENT", "SEAHAWKS PLAYOFF GRAPHIC"]
                    )
                ),
                ScriptSegment(
                    order=2,
                    segment_type="real_clip",
                    clip_reference=RealClipReference(
                        clip_id="clip_doubters",
                        description="Compilation of preseason analysts predicting Seahawks to finish last in NFC West, mock drafts, low power rankings.",
                        search_query="Seahawks 2024 preseason predictions last place NFC West",
                        duration_seconds=8,
                        context="Sets up the narrative by showing how wrong everyone was",
                        transition_in="dramatic cut",
                        transition_out="whoosh transition"
                    )
                ),
                ScriptSegment(
                    order=3,
                    segment_type="ai_generated",
                    ai_segment=AIGeneratedSegment(
                        segment_id="analysis_1",
                        segment_type="analysis",
                        duration_seconds=30,
                        mood=Mood.CELEBRATORY,
                        visual_description="Geno Smith highlights playing on background monitors. Hosts breaking down his transformation.",
                        camera_notes="Cut to plays on monitor, back to Tony for analysis.",
                        dialogue=[
                            DialogueLine(
                                speaker="Tony Romo Jr.",
                                text="Okay, let me tell you what Geno Smith is doing that nobody is talking about. Watch this throw - that's NFL MVP level anticipation right there!",
                                delivery="Animated, pointing at screen, impressed",
                                camera_direction="Over shoulder shot to monitor"
                            ),
                            DialogueLine(
                                speaker="Sarah Chen",
                                text="His completion percentage in the clutch is absurd. 73% on third and fourth down in the playoffs. He's not just managing games - he's winning them.",
                                delivery="Impressed, emphasizing stats",
                                camera_direction="Sarah with stat graphic"
                            )
                        ],
                        graphics=["STAT: 73% Clutch Completion Rate", "MVP CALIBER PLAYS"]
                    )
                ),
                ScriptSegment(
                    order=4,
                    segment_type="real_clip",
                    clip_reference=RealClipReference(
                        clip_id="clip_geno_td",
                        description="Geno Smith playoff touchdown pass to DK Metcalf, crowd eruption, celebration.",
                        search_query="Geno Smith DK Metcalf touchdown playoffs 2024 Seahawks",
                        duration_seconds=10,
                        context="Showcase the clutch performance that defines this run",
                        transition_in="cut",
                        transition_out="celebration freeze"
                    )
                ),
                ScriptSegment(
                    order=5,
                    segment_type="ai_generated",
                    ai_segment=AIGeneratedSegment(
                        segment_id="analysis_2",
                        segment_type="analysis",
                        duration_seconds=25,
                        mood=Mood.TENSE,
                        visual_description="Defensive highlights playing. Mood shifts to respect for the defensive transformation.",
                        camera_notes="Serious analysis mode, leaning in.",
                        dialogue=[
                            DialogueLine(
                                speaker="Marcus Webb",
                                text="But this isn't just about Geno. Mike Macdonald has completely transformed this defense in year one.",
                                delivery="Transitioning to serious analysis",
                                camera_direction="Medium shot Marcus"
                            ),
                            DialogueLine(
                                speaker="Sarah Chen",
                                text="They went from bottom 10 in points allowed to top 5. That doesn't happen by accident. That's scheme, that's coaching, that's buy-in.",
                                delivery="Emphatic, making the case",
                                camera_direction="Sarah with defensive stats graphic"
                            )
                        ],
                        graphics=["DEFENSIVE TRANSFORMATION GRAPHIC"]
                    )
                ),
                ScriptSegment(
                    order=6,
                    segment_type="real_clip",
                    clip_reference=RealClipReference(
                        clip_id="clip_defense",
                        description="Seahawks defense making big plays - interception, sack, goal line stand. Crowd going wild.",
                        search_query="Seahawks defense highlights playoffs 2024 interception sack",
                        duration_seconds=10,
                        context="Prove the defensive dominance visually",
                        transition_in="impact cut",
                        transition_out="fade"
                    )
                ),
                ScriptSegment(
                    order=7,
                    segment_type="ai_generated",
                    ai_segment=AIGeneratedSegment(
                        segment_id="outro_1",
                        segment_type="outro",
                        duration_seconds=25,
                        mood=Mood.EXCITING,
                        visual_description="Energy peak. Super Bowl graphic appearing. Hosts unified in excitement.",
                        camera_notes="Building to crescendo, end on powerful shot.",
                        dialogue=[
                            DialogueLine(
                                speaker="Tony Romo Jr.",
                                text="I'll say it right now - this Seahawks team can beat ANYONE. They have no fear!",
                                delivery="Confident prediction, emphatic",
                                camera_direction="Tony close-up"
                            ),
                            DialogueLine(
                                speaker="Marcus Webb",
                                text="From doubted to dominant. From written off to writing history. Seattle's path to the Super Bowl is one for the ages. The 12th Man... is LOUD again!",
                                delivery="Building to powerful close, arms spread on final line",
                                camera_direction="Slow push to Marcus, hold on final beat"
                            )
                        ],
                        graphics=["SUPER BOWL BOUND?", "12TH MAN RISING"]
                    )
                )
            ],
            research_sources=[
                "ESPN Seahawks Coverage",
                "The Athletic Seattle",
                "NFL Network",
                "Seattle Times Sports"
            ]
        )

    def _generate_belichick_script(self, research: ResearchContext, duration: int) -> SportsNarrativeScript:
        """Generate script for Belichick HOF storyline."""
        return SportsNarrativeScript(
            title="Six Rings, No Entry: The Belichick Hall of Fame Controversy",
            storyline=research.original_prompt,
            total_duration_seconds=duration,
            studio=StudioSetting(
                description="A dramatic, serious studio setup. Dark tones with gold accents reminiscent of Hall of Fame aesthetics. Large screens show Belichick's championship moments in black and white, creating gravitas.",
                lighting="Dramatic, moody lighting. Strong shadows, almost noir-style. Gold accent lights for Hall of Fame imagery.",
                background_elements=[
                    "Hall of Fame gold jacket imagery",
                    "Six Super Bowl trophies silhouette",
                    "Patriots dynasty timeline",
                    "Voting controversy graphics"
                ],
                color_scheme="Black, gold, and navy. Serious, prestigious atmosphere with hints of controversy red.",
                time_of_day="Late night, serious discussion time"
            ),
            hosts=[
                Host(
                    name="Marcus Webb",
                    role="Lead Anchor",
                    appearance="African American male, early 40s, black suit with gold tie. Gravitas appropriate for serious topic.",
                    position="Center desk"
                ),
                Host(
                    name="Sarah Chen",
                    role="NFL Analyst",
                    appearance="Asian American female, mid-30s, burgundy blazer, serious expression. Ready for heated debate.",
                    position="Left side"
                ),
                Host(
                    name="Tony Romo Jr.",
                    role="Former Player Analyst",
                    appearance="Caucasian male, late 30s, visibly frustrated about topic. Black sport coat, animated.",
                    position="Right side"
                )
            ],
            premise="Six Super Bowl championships. The greatest dynasty in NFL history. And yet, Bill Belichick finds himself on the outside of the Pro Football Hall of Fame looking in. Tonight, we examine the most controversial Hall of Fame snub in football history.",
            key_points=[
                "Six Super Bowl championships as head coach",
                "The politics behind the voting process",
                "Player support for Belichick",
                "What this means for the Hall's credibility"
            ],
            segments=[
                ScriptSegment(
                    order=1,
                    segment_type="ai_generated",
                    ai_segment=AIGeneratedSegment(
                        segment_id="intro_1",
                        segment_type="intro",
                        duration_seconds=25,
                        mood=Mood.CONTROVERSIAL,
                        visual_description="Dark, dramatic open. Six Lombardi trophies appear one by one on screen behind Marcus. Weight of the injustice palpable.",
                        camera_notes="Slow, deliberate camera moves. Building tension.",
                        dialogue=[
                            DialogueLine(
                                speaker="Marcus Webb",
                                text="One. Two. Three. Four. Five. Six.",
                                delivery="Counting slowly as trophies appear, each number heavy with meaning",
                                camera_direction="Cut to trophy appearing with each number"
                            ),
                            DialogueLine(
                                speaker="Marcus Webb",
                                text="Six Super Bowl championships. More than any head coach in NFL history. And somehow... Bill Belichick is not in the Hall of Fame.",
                                delivery="Disbelief, letting the absurdity land",
                                camera_direction="Push in to Marcus"
                            ),
                            DialogueLine(
                                speaker="Sarah Chen",
                                text="This isn't about football anymore, Marcus. This is about something else entirely.",
                                delivery="Serious, implying deeper issues",
                                camera_direction="Cut to Sarah, knowing look"
                            )
                        ],
                        graphics=["SIX CHAMPIONSHIPS", "ZERO HALL OF FAME VOTES"]
                    )
                ),
                ScriptSegment(
                    order=2,
                    segment_type="real_clip",
                    clip_reference=RealClipReference(
                        clip_id="clip_dynasty",
                        description="Patriots dynasty montage - Super Bowl wins, Gatorade baths, Belichick hoisting trophies, confetti falling.",
                        search_query="Patriots dynasty Super Bowl wins Belichick trophy celebration montage",
                        duration_seconds=12,
                        context="Establish the undeniable greatness before discussing the snub",
                        transition_in="dramatic fade",
                        transition_out="slow motion freeze"
                    )
                ),
                ScriptSegment(
                    order=3,
                    segment_type="ai_generated",
                    ai_segment=AIGeneratedSegment(
                        segment_id="debate_1",
                        segment_type="debate",
                        duration_seconds=35,
                        mood=Mood.CONTROVERSIAL,
                        visual_description="Tony visibly upset. Energy in studio is charged. This is the hot take segment.",
                        camera_notes="Quick cuts, capture emotion, split screens for disagreement.",
                        dialogue=[
                            DialogueLine(
                                speaker="Tony Romo Jr.",
                                text="This is an absolute JOKE. I'm sorry, but what are we doing here? The man won SIX Super Bowls! You put him in on DAY ONE!",
                                delivery="Heated, genuinely frustrated, hands gesturing wildly",
                                camera_direction="Medium shot capturing emotion"
                            ),
                            DialogueLine(
                                speaker="Sarah Chen",
                                text="Tony, I agree with you on the merits. But let's talk about what's really happening here. Belichick burned bridges. He wasn't media-friendly. The voters hold grudges.",
                                delivery="Analytical but critical of the process",
                                camera_direction="Cut to Sarah"
                            ),
                            DialogueLine(
                                speaker="Tony Romo Jr.",
                                text="So we're punishing the greatest coach in NFL history because he didn't smile enough at press conferences? That's what the Hall of Fame is now?",
                                delivery="Incredulous, sarcastic",
                                camera_direction="Split screen with Sarah"
                            ),
                            DialogueLine(
                                speaker="Marcus Webb",
                                text="The question becomes - what does this say about the institution itself? If Bill Belichick doesn't get in, what is the Hall of Fame really honoring?",
                                delivery="Philosophical, raising larger point",
                                camera_direction="Cut to Marcus, holding shot"
                            )
                        ],
                        graphics=["HALL OF FAME POLITICS", "BELICHICK'S RESUME"]
                    )
                ),
                ScriptSegment(
                    order=4,
                    segment_type="real_clip",
                    clip_reference=RealClipReference(
                        clip_id="clip_brady_support",
                        description="Tom Brady and former Patriots players speaking in support of Belichick's Hall of Fame candidacy.",
                        search_query="Tom Brady Belichick Hall of Fame support former Patriots players",
                        duration_seconds=10,
                        context="Show the player support rallying behind the coach",
                        transition_in="cut",
                        transition_out="fade"
                    )
                ),
                ScriptSegment(
                    order=5,
                    segment_type="ai_generated",
                    ai_segment=AIGeneratedSegment(
                        segment_id="analysis_1",
                        segment_type="analysis",
                        duration_seconds=25,
                        mood=Mood.REFLECTIVE,
                        visual_description="Mood shifts to more reflective. Comparing to other HOF coaches.",
                        camera_notes="Steady shots, graphics comparing records.",
                        dialogue=[
                            DialogueLine(
                                speaker="Sarah Chen",
                                text="Let's look at the numbers objectively. 302 career wins, six championships, three Coach of the Year awards. Compare that to any coach in Canton.",
                                delivery="Laying out the undeniable case",
                                camera_direction="Sarah with comparison graphic"
                            ),
                            DialogueLine(
                                speaker="Marcus Webb",
                                text="Don Shula, Chuck Noll, Bill Walsh - all first-ballot Hall of Famers. Belichick's resume exceeds all of them in championships.",
                                delivery="Making the point unavoidable",
                                camera_direction="Marcus, graphic showing comparisons"
                            )
                        ],
                        graphics=["COACHING COMPARISON CHART", "CHAMPIONSHIPS WON"]
                    )
                ),
                ScriptSegment(
                    order=6,
                    segment_type="real_clip",
                    clip_reference=RealClipReference(
                        clip_id="clip_reactions",
                        description="Social media reactions, fan protests, former players speaking out about the snub.",
                        search_query="Belichick Hall of Fame snub reactions fans players outrage",
                        duration_seconds=8,
                        context="Show the widespread outrage at the decision",
                        transition_in="cut",
                        transition_out="fade to studio"
                    )
                ),
                ScriptSegment(
                    order=7,
                    segment_type="ai_generated",
                    ai_segment=AIGeneratedSegment(
                        segment_id="outro_1",
                        segment_type="outro",
                        duration_seconds=25,
                        mood=Mood.DRAMATIC,
                        visual_description="Final somber moment. Belichick silhouette with six trophies. Letting the injustice speak for itself.",
                        camera_notes="Slow push to Marcus for final statement, hold on powerful image.",
                        dialogue=[
                            DialogueLine(
                                speaker="Tony Romo Jr.",
                                text="When they finally put him in - and they will - this snub will be remembered as one of the most embarrassing moments in Hall of Fame history.",
                                delivery="Definitive, no room for argument",
                                camera_direction="Tony medium shot"
                            ),
                            DialogueLine(
                                speaker="Marcus Webb",
                                text="Six rings. A dynasty for the ages. And a Hall of Fame that, tonight, has more questions to answer than Bill Belichick ever will. The greatest coach in NFL history... still waiting.",
                                delivery="Powerful, letting words resonate, slight pause before 'still waiting'",
                                camera_direction="Slow push to close-up, final beat on Belichick silhouette"
                            )
                        ],
                        graphics=["STILL WAITING", "SIX RINGS"]
                    )
                )
            ],
            research_sources=[
                "Pro Football Hall of Fame",
                "ESPN NFL Coverage",
                "The Athletic",
                "Sports Illustrated"
            ]
        )

    def _generate_generic_script(self, research: ResearchContext, duration: int) -> SportsNarrativeScript:
        """Generate a generic sports script."""
        return SportsNarrativeScript(
            title=f"Breaking Down: {research.original_prompt}",
            storyline=research.original_prompt,
            total_duration_seconds=duration,
            studio=StudioSetting(
                description="Modern sports broadcast studio with multiple screens and dynamic lighting.",
                lighting="Professional broadcast lighting with dramatic accents",
                background_elements=["Large LED displays", "Sports graphics", "Ticker"],
                color_scheme="Professional blue and silver",
                time_of_day="Evening broadcast"
            ),
            hosts=[
                Host(
                    name="Marcus Webb",
                    role="Lead Anchor",
                    appearance="Professional male anchor in navy suit",
                    position="Center desk"
                ),
                Host(
                    name="Sarah Chen",
                    role="Analyst",
                    appearance="Professional female analyst in blazer",
                    position="Left of center"
                )
            ],
            premise=research.storyline_summary,
            key_points=research.key_facts[:4] if research.key_facts else ["Key point 1", "Key point 2"],
            segments=[
                ScriptSegment(
                    order=1,
                    segment_type="ai_generated",
                    ai_segment=AIGeneratedSegment(
                        segment_id="intro_1",
                        segment_type="intro",
                        duration_seconds=30,
                        mood=Mood.DRAMATIC,
                        visual_description="Standard broadcast intro with hosts at desk",
                        camera_notes="Wide establishing shot, push to hosts",
                        dialogue=[
                            DialogueLine(
                                speaker="Marcus Webb",
                                text=f"Tonight we're breaking down one of the biggest stories in sports: {research.original_prompt}",
                                delivery="Authoritative, engaging",
                                camera_direction="Medium shot"
                            )
                        ],
                        graphics=["SHOW TITLE GRAPHIC"]
                    )
                )
            ],
            research_sources=["ESPN", "NFL Network", "Sports News"]
        )


    def generate_script_sync(
        self, 
        research: ResearchContext, 
        duration_seconds: int = 150
    ) -> SportsNarrativeScript:
        """
        Synchronous version of script generation.
        Uses mock data for fast testing, or calls Gemini API if available.
        """
        if not self.has_api:
            return self._generate_mock_script(research, duration_seconds)
        
        try:
            prompt = self._get_script_prompt(research, duration_seconds)
            
            response = self.model.generate_content(
                [self._get_system_prompt(), prompt],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.8,
                )
            )
            
            script_data = json.loads(response.text)
            return SportsNarrativeScript(**script_data)
            
        except Exception as e:
            print(f"[ScriptGenerator] Error generating script: {e}")
            return self._generate_mock_script(research, duration_seconds)


# Singleton instance
script_generator = ScriptGenerator()

"""
Research agent for gathering sports information using Gemini with Google Search grounding.
Uses Gemini's built-in search capabilities to gather real-time sports context.
"""
import os
import json
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import google.generativeai as genai
from models import ResearchResult, ResearchContext


class SportsResearchAgent:
    """
    Agent that researches sports storylines using Gemini with Google Search grounding.
    """
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            # Use Gemini 2.0 Flash with Google Search tool for grounding
            self.model = genai.GenerativeModel(
                'gemini-2.0-flash',
                tools="google_search"
            )
            self.has_api = True
            print("[Research] Gemini API configured with Google Search grounding")
        else:
            print("[Research] Warning: No GOOGLE_API_KEY set, using mock data")
            self.model = None
            self.has_api = False
    
    def _get_research_prompt(self, query: str) -> str:
        """Create a prompt for sports research."""
        return f"""You are a sports researcher gathering information for a broadcast script.

Research this sports storyline thoroughly: "{query}"

Search for and provide:
1. Recent news and developments about this topic
2. Key facts and statistics
3. Important people involved (players, coaches, executives)
4. Timeline of key events
5. Controversial or debatable aspects
6. Emotional/human interest angles

Format your response as JSON with this structure:
{{
    "storyline_summary": "A 2-3 paragraph summary of the storyline",
    "key_facts": ["fact1", "fact2", "fact3", ...],
    "key_figures": ["person/team 1", "person/team 2", ...],
    "timeline": ["event1", "event2", ...],
    "controversy_points": ["point1", "point2", ...],
    "emotional_angles": ["angle1", "angle2", ...],
    "sources": [
        {{"title": "Article title", "snippet": "Key quote or info", "source": "ESPN/etc"}}
    ]
}}

Be thorough and use current, real information from your search."""

    def research_storyline_sync(self, prompt: str) -> ResearchContext:
        """
        Research a sports storyline using Gemini with Google Search grounding.
        """
        print(f"[Research] Starting research for: {prompt}")
        
        if not self.has_api:
            print("[Research] No API key, using mock data")
            return self._mock_research(prompt)
        
        try:
            # Use Gemini with Google Search grounding
            response = self.model.generate_content(
                self._get_research_prompt(prompt),
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                )
            )
            
            # Extract the response text
            response_text = response.text
            
            # Try to parse as JSON
            try:
                # Find JSON in the response (might be wrapped in markdown)
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end]
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end]
                
                data = json.loads(response_text.strip())
                
                # Convert sources to ResearchResult objects
                sources = []
                for src in data.get("sources", []):
                    sources.append(ResearchResult(
                        query=prompt,
                        source=src.get("source", "web"),
                        title=src.get("title", ""),
                        snippet=src.get("snippet", ""),
                        url=src.get("url"),
                        relevance_score=0.8
                    ))
                
                return ResearchContext(
                    original_prompt=prompt,
                    storyline_summary=data.get("storyline_summary", ""),
                    key_facts=data.get("key_facts", []),
                    key_figures=data.get("key_figures", []),
                    timeline=data.get("timeline", []),
                    controversy_points=data.get("controversy_points", []),
                    emotional_angles=data.get("emotional_angles", []),
                    sources=sources
                )
                
            except json.JSONDecodeError:
                # If JSON parsing fails, extract info manually
                print("[Research] JSON parsing failed, extracting manually")
                return self._extract_from_text(prompt, response_text)
                
        except Exception as e:
            print(f"[Research] Gemini research failed: {e}")
            import traceback
            traceback.print_exc()
            return self._mock_research(prompt)
    
    def _extract_from_text(self, prompt: str, text: str) -> ResearchContext:
        """Extract research context from non-JSON response."""
        # Simple extraction - split into sentences and categorize
        sentences = [s.strip() for s in text.replace('\n', ' ').split('.') if len(s.strip()) > 20]
        
        return ResearchContext(
            original_prompt=prompt,
            storyline_summary=text[:500] + "..." if len(text) > 500 else text,
            key_facts=sentences[:5],
            key_figures=self._extract_names(text),
            timeline=["Recent developments", "Current situation"],
            controversy_points=[s for s in sentences if any(w in s.lower() for w in ['controversy', 'debate', 'criticism', 'question'])],
            emotional_angles=["Fan perspective", "Player impact", "Legacy implications"],
            sources=[ResearchResult(
                query=prompt,
                source="gemini_search",
                title="Gemini Research",
                snippet=text[:200],
                relevance_score=0.7
            )]
        )
    
    def _extract_names(self, text: str) -> List[str]:
        """Extract potential names/teams from text."""
        # Common sports entities to look for
        common_teams = [
            "49ers", "Seahawks", "Patriots", "Chiefs", "Eagles", "Cowboys", "Packers",
            "Bills", "Ravens", "Bengals", "Lions", "Dolphins", "Jets", "Giants",
            "Commanders", "Bears", "Vikings", "Rams", "Cardinals", "Broncos", "Raiders",
            "Chargers", "Texans", "Colts", "Titans", "Jaguars", "Browns", "Steelers",
            "Saints", "Falcons", "Buccaneers", "Panthers", "NFL", "NFC", "AFC"
        ]
        
        found = []
        text_lower = text.lower()
        
        for team in common_teams:
            if team.lower() in text_lower:
                found.append(team)
        
        return found[:10]  # Limit to 10
    
    def _mock_research(self, prompt: str) -> ResearchContext:
        """Fallback mock research when API is unavailable."""
        prompt_lower = prompt.lower()
        
        # Generic mock data based on keywords
        if "49ers" in prompt_lower:
            return ResearchContext(
                original_prompt=prompt,
                storyline_summary="The San Francisco 49ers entered the season as Super Bowl favorites but injuries derailed their championship hopes. Christian McCaffrey's absence and Kyle Shanahan's play-calling have been central topics of debate.",
                key_facts=[
                    "49ers were preseason Super Bowl favorites",
                    "Christian McCaffrey missed significant time with injury",
                    "Multiple blown double-digit leads",
                    "Kyle Shanahan's fourth quarter play-calling questioned"
                ],
                key_figures=["Kyle Shanahan", "Brock Purdy", "Christian McCaffrey", "49ers", "NFC West"],
                timeline=["Preseason hype", "Early injuries", "Mid-season struggles", "Playoff exit"],
                controversy_points=["Shanahan's conservative play-calling", "Championship window closing"],
                emotional_angles=["Fan disappointment", "Player injuries", "What could have been"],
                sources=[]
            )
        elif "seahawks" in prompt_lower:
            return ResearchContext(
                original_prompt=prompt,
                storyline_summary="The Seattle Seahawks defied expectations with an impressive playoff run. Geno Smith's leadership and Mike Macdonald's defensive transformation have been key storylines.",
                key_facts=[
                    "Seahawks exceeded preseason expectations",
                    "Geno Smith playing at MVP level",
                    "Defense transformed under Mike Macdonald",
                    "Young core emerging as contenders"
                ],
                key_figures=["Geno Smith", "DK Metcalf", "Mike Macdonald", "Seahawks", "12th Man"],
                timeline=["Low expectations", "Early wins", "Playoff push", "Championship run"],
                controversy_points=["Doubters proven wrong", "Geno Smith's redemption"],
                emotional_angles=["Underdog story", "City pride", "Redemption narrative"],
                sources=[]
            )
        elif "belichick" in prompt_lower:
            return ResearchContext(
                original_prompt=prompt,
                storyline_summary="Bill Belichick's exclusion from the Hall of Fame despite six Super Bowl championships has sparked outrage across the NFL world. Questions about voter politics and the Hall's credibility dominate the conversation.",
                key_facts=[
                    "Six Super Bowl championships as head coach",
                    "Most wins by a head coach in NFL history",
                    "Controversial departure from Patriots",
                    "Hall of Fame voters influenced by media relationships"
                ],
                key_figures=["Bill Belichick", "Tom Brady", "Patriots", "Hall of Fame", "Rob Gronkowski"],
                timeline=["Dynasty years", "Patriots departure", "HOF voting", "Public outcry"],
                controversy_points=["Voter politics", "HOF credibility questioned", "Greatest snub ever"],
                emotional_angles=["Legacy denied", "Player support", "Institution vs individual"],
                sources=[]
            )
        else:
            return ResearchContext(
                original_prompt=prompt,
                storyline_summary=f"Research on: {prompt}",
                key_facts=["Developing story", "Multiple perspectives"],
                key_figures=["NFL", "Teams involved"],
                timeline=["Recent events", "Current situation"],
                controversy_points=["Debate ongoing"],
                emotional_angles=["Fan interest", "Player impact"],
                sources=[]
            )


# Singleton instance
research_agent = SportsResearchAgent()

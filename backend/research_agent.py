"""
Research agent for gathering sports information using Gemini with Google Search grounding.
Uses Gemini's built-in search capabilities to gather real-time sports context.

NO HARDCODED DATA - All research comes from Gemini + Google Search.
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
    All research is dynamic - no hardcoded fallbacks.
    """
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "No API key found! Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable.\n"
                "Get your API key at: https://aistudio.google.com/app/apikey"
            )
        
            genai.configure(api_key=api_key)
        
            # Use Gemini 2.0 Flash with Google Search tool for grounding
            self.model = genai.GenerativeModel(
                'gemini-2.0-flash',
                tools="google_search"
            )
        print("[Research] ✅ Gemini API configured with Google Search grounding")
    
    def _get_research_prompt(self, query: str) -> str:
        """Create a comprehensive prompt for sports research."""
        return f"""You are a sports researcher gathering information for a primetime broadcast script.

Research this sports storyline thoroughly using Google Search: "{query}"

Your task:
1. Search for the most recent news, articles, and developments about this topic
2. Find specific statistics, scores, and data points
3. Identify all key people involved (players, coaches, executives, analysts)
4. Build a timeline of relevant events
5. Find controversial or debatable aspects that would make good TV discussion
6. Identify emotional/human interest angles

Be thorough and cite real sources. This research will be used to create a broadcast script.

Return your findings as JSON with this EXACT structure:
{{
    "storyline_summary": "A comprehensive 2-3 paragraph summary of the storyline with specific details, dates, and context",
    "key_facts": [
        "Specific fact with numbers/dates",
        "Another specific fact",
        "Include at least 5-8 key facts"
    ],
    "key_figures": [
        "Person/Team 1 - their role in the story",
        "Person/Team 2 - their role",
        "Include all relevant people and teams"
    ],
    "timeline": [
        "Date/Time: Event description",
        "Date/Time: Another event",
        "Build chronological narrative"
    ],
    "controversy_points": [
        "Debatable aspect 1 - why it's controversial",
        "Debatable aspect 2 - different viewpoints",
        "What fans/analysts disagree about"
    ],
    "emotional_angles": [
        "Human interest element 1",
        "Underdog story / redemption arc / tragedy",
        "What makes this story compelling"
    ],
    "sources": [
        {{"title": "Article title", "snippet": "Key quote or information from this source", "source": "Publication name", "url": "URL if available"}},
        {{"title": "Another article", "snippet": "Important info", "source": "ESPN/etc"}}
    ]
}}

IMPORTANT: 
- Use REAL, CURRENT information from your Google Search
- Include specific numbers, dates, names, and quotes
- The more specific and factual, the better the script will be
- Return ONLY the JSON, no other text"""

    def research_storyline_sync(self, prompt: str) -> ResearchContext:
        """
        Research a sports storyline using Gemini with Google Search grounding.
        Returns structured research context for script generation.
        """
        print(f"\n[Research] 🔍 Researching: {prompt}")
        print("[Research] Using Gemini 2.0 Flash with Google Search grounding...")
        
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
            print(f"[Research] Got response ({len(response_text)} chars)")
            
            # Parse the JSON response
            data = self._parse_json_response(response_text)
                
                # Convert sources to ResearchResult objects
                sources = []
                for src in data.get("sources", []):
                    sources.append(ResearchResult(
                        query=prompt,
                        source=src.get("source", "web"),
                        title=src.get("title", ""),
                        snippet=src.get("snippet", ""),
                        url=src.get("url"),
                    relevance_score=0.9
                    ))
                
            research_context = ResearchContext(
                    original_prompt=prompt,
                    storyline_summary=data.get("storyline_summary", ""),
                    key_facts=data.get("key_facts", []),
                    key_figures=data.get("key_figures", []),
                    timeline=data.get("timeline", []),
                    controversy_points=data.get("controversy_points", []),
                    emotional_angles=data.get("emotional_angles", []),
                    sources=sources
                )
                
            print(f"[Research] ✅ Research complete!")
            print(f"   - Summary: {len(research_context.storyline_summary)} chars")
            print(f"   - {len(research_context.key_facts)} key facts")
            print(f"   - {len(research_context.key_figures)} key figures")
            print(f"   - {len(research_context.timeline)} timeline events")
            print(f"   - {len(research_context.sources)} sources")
            
            return research_context
                
        except Exception as e:
            print(f"[Research] ❌ Error during research: {e}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"Research failed: {e}")
    
    def _parse_json_response(self, response_text: str) -> dict:
        """Parse JSON from Gemini response, handling markdown code blocks."""
        text = response_text.strip()
        
        # Remove markdown code blocks if present
        if "```json" in text:
            json_start = text.find("```json") + 7
            json_end = text.find("```", json_start)
            text = text[json_start:json_end]
        elif "```" in text:
            json_start = text.find("```") + 3
            json_end = text.find("```", json_start)
            text = text[json_start:json_end]
        
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError as e:
            print(f"[Research] JSON parsing failed: {e}")
            print(f"[Research] Raw response:\n{response_text[:500]}...")
            
            # Try to extract what we can from the text
            return self._extract_from_text(response_text)
    
    def _extract_from_text(self, text: str) -> dict:
        """
        Last resort: extract research context from non-JSON response.
        Still uses the actual response, not hardcoded data.
        """
        print("[Research] Attempting to extract data from unstructured response...")
        
        # Split into sentences for facts
        sentences = [s.strip() for s in text.replace('\n', ' ').split('.') if len(s.strip()) > 20]
        
        return {
            "storyline_summary": text[:1000] if len(text) > 1000 else text,
            "key_facts": sentences[:8],
            "key_figures": [],  # Hard to extract without structure
            "timeline": [],
            "controversy_points": [s for s in sentences if any(w in s.lower() for w in ['controversy', 'debate', 'criticism', 'question', 'disagree'])],
            "emotional_angles": [s for s in sentences if any(w in s.lower() for w in ['fan', 'heart', 'emotion', 'legacy', 'dream', 'hope'])],
            "sources": []
        }


# Create singleton instance - will raise error if no API key
research_agent = SportsResearchAgent()

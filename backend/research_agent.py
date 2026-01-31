"""
Research agent for sports information.
Fast mode uses Gemini directly. Browser mode uses Browser Use for web scraping.
"""
import os
import json
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types
from models import ResearchResult, ResearchContext


class FastResearchAgent:
    """Super fast research using just Gemini (no browser scraping)."""
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("No GOOGLE_API_KEY found!")
        
        self.client = genai.Client(api_key=api_key)
        print("[Research] ✅ Fast mode - Gemini 2.0 Flash")

    def research_storyline_sync(self, prompt: str) -> ResearchContext:
        """Fast research using Gemini's knowledge."""
        print(f"\n[Research] 🔍 Researching: {prompt}")
        
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""You are a sports researcher creating content for a broadcast script.

TOPIC: {prompt}

Research this thoroughly and return JSON with this EXACT structure:
{{
    "storyline_summary": "A detailed 2-3 paragraph summary covering the key narrative. Include specific dates, scores, player names, and context. Make it dramatic and engaging.",
    "key_facts": [
        "Specific fact 1 with numbers/dates",
        "Specific fact 2",
        "Include 5-8 compelling facts"
    ],
    "key_figures": [
        "Name - their role in the story",
        "Name - why they matter"
    ],
    "timeline": [
        "Date: Event description",
        "Date: Another key event"
    ],
    "controversy_points": [
        "Debatable aspect - why fans disagree",
        "Hot take material"
    ],
    "emotional_angles": [
        "Human interest element",
        "What makes fans care"
    ],
    "sources": [
        {{"title": "Article/Source", "snippet": "Key information", "source": "ESPN/NFL/etc"}}
    ]
}}

Provide accurate, detailed sports information. Return ONLY the JSON.""",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.7,
            )
        )
        
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            print("[Research] JSON parse failed, extracting from response...")
            data = {
                "storyline_summary": response.text[:1000],
                "key_facts": [],
                "key_figures": [],
                "timeline": [],
                "controversy_points": [],
                "emotional_angles": [],
                "sources": []
            }
        
        sources = []
        for s in data.get("sources", []):
            sources.append(ResearchResult(
                query=prompt,
                source=s.get("source", ""),
                title=s.get("title", ""),
                snippet=s.get("snippet", ""),
                relevance_score=0.9
            ))
        
        context = ResearchContext(
            original_prompt=prompt,
            storyline_summary=data.get("storyline_summary", ""),
            key_facts=data.get("key_facts", []),
            key_figures=data.get("key_figures", []),
            timeline=data.get("timeline", []),
            controversy_points=data.get("controversy_points", []),
            emotional_angles=data.get("emotional_angles", []),
            sources=sources
        )
        
        print(f"[Research] ✅ Complete!")
        print(f"   - {len(context.key_facts)} facts")
        print(f"   - {len(context.key_figures)} key figures")
        return context


class BrowserResearchAgent:
    """Research agent using Browser Use for real-time web scraping."""
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        browser_api = os.getenv("BROWSER_USE_API_KEY")
        
        if not api_key:
            raise ValueError("No GOOGLE_API_KEY found!")
        
        self.client = genai.Client(api_key=api_key)
        self.browser_api = browser_api
        print("[Research] ✅ Browser Use mode configured")
    
    def research_storyline_sync(self, prompt: str) -> ResearchContext:
        """Research using Browser Use for web scraping."""
        import asyncio
        return asyncio.run(self._research_async(prompt))
    
    async def _research_async(self, prompt: str) -> ResearchContext:
        """Async research with browser scraping."""
        from browser_use import Agent, Browser
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        print(f"\n[Research] 🌐 Browser scraping: {prompt}")
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        browser = Browser(headless=True)
        
        agent = Agent(
            task=f"""Search for sports news about: "{prompt}"
            
            1. Go to google.com and search for this topic
            2. Click on 2-3 top news results (ESPN, NFL.com, etc)
            3. Extract: dates, scores, player names, key events
            4. Return a summary of what you found""",
            llm=llm,
            browser=browser,
            max_actions_per_step=3,
        )
        
        try:
            result = await agent.run(max_steps=8)
            scraped = result.final_result() if result.final_result() else ""
            await browser.close()
        except Exception as e:
            print(f"[Research] Browser error: {e}")
            scraped = ""
            try:
                await browser.close()
            except:
                pass
        
        # Structure with Gemini
        return self._structure_data(prompt, scraped)
    
    def _structure_data(self, prompt: str, scraped: str) -> ResearchContext:
        """Structure scraped data with Gemini."""
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""Structure this sports research into JSON.

TOPIC: {prompt}
SCRAPED DATA: {scraped if scraped else "Use your knowledge about this topic."}

Return JSON:
{{
    "storyline_summary": "2-3 paragraph summary",
    "key_facts": ["fact1", "fact2"],
    "key_figures": ["person - role"],
    "timeline": ["event1", "event2"],
    "controversy_points": ["debate point"],
    "emotional_angles": ["human interest"],
    "sources": [{{"title": "Source", "snippet": "Info", "source": "Site"}}]
}}""",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.7,
            )
        )
        
        try:
            data = json.loads(response.text)
        except:
            data = {"storyline_summary": scraped or prompt, "key_facts": [], "key_figures": [],
                    "timeline": [], "controversy_points": [], "emotional_angles": [], "sources": []}
        
        sources = [ResearchResult(query=prompt, source=s.get("source", ""), title=s.get("title", ""),
                                   snippet=s.get("snippet", ""), relevance_score=0.9)
                   for s in data.get("sources", [])]
        
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


# Default to fast mode
research_agent = FastResearchAgent()

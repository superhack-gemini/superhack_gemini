"""
Test script for Veo-ready output.
"""
import os
import json
from dotenv import load_dotenv

load_dotenv()


def test_full_pipeline(prompt: str, duration: int = 120):
    """Test research → script pipeline."""
    
    print("\n" + "="*60)
    print("🏈 VEO SCRIPT GENERATOR TEST")
    print("="*60)
    print(f"Prompt: {prompt}")
    print(f"Duration: {duration}s")
    print("="*60)
    
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n❌ No API key! Set GOOGLE_API_KEY")
        return None
    
    print(f"\n✅ API key found: {api_key[:10]}...")
    
    from research_agent import research_agent
    from script_generator import script_generator
    
    # Research
    print("\n" + "-"*60)
    print("STEP 1: RESEARCH")
    print("-"*60)
    
    research = research_agent.research_storyline_sync(prompt)
    print(f"\n📋 Research: {len(research.key_facts)} facts, {len(research.key_figures)} figures")
    
    # Script
    print("\n" + "-"*60)
    print("STEP 2: VEO SCRIPT GENERATION")
    print("-"*60)
    
    script = script_generator.generate_script_sync(research, duration)
    
    print(f"\n📺 Script: {script.title}")
    print(f"   Hosts: {[h.name for h in script.hosts]}")
    
    # Show segments
    print(f"\n📼 Segments ({len(script.segments)} total):")
    for seg in script.segments:
        if seg.get("type") == "ai_generated":
            print(f"   {seg['order']}. [AI] {seg['speaker']} - {seg['duration_seconds']}s")
            print(f"      \"{seg['dialogue'][:60]}...\"")
        else:
            print(f"   {seg['order']}. [CLIP] {seg['description'][:50]}... - {seg['duration_seconds']}s")
    
    # Save
    output = {
        "title": script.title,
        "storyline": script.storyline,
        "total_duration_seconds": script.total_duration_seconds,
        "studio": script.studio.model_dump(),
        "hosts": [h.model_dump() for h in script.hosts],
        "segments": script.segments,
        "research_summary": script.research_summary,
        "key_facts": script.key_facts
    }
    
    with open("test_output.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Saved to: test_output.json")
    return script


if __name__ == "__main__":
    import sys
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Why didn't the 49ers make it to the Super Bowl"
    test_full_pipeline(prompt, duration=120)

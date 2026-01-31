"""
Test script for Veo output.
"""
import os
import json
import sys
from dotenv import load_dotenv

load_dotenv()


def test_full_pipeline(prompt: str, duration: int = 120, output_file: str = "test_output.json"):
    print("\n" + "="*60)
    print("🏈 VEO SCRIPT GENERATOR")
    print("="*60)
    print(f"Prompt: {prompt}")
    print(f"Output: {output_file}")
    
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n❌ No API key! Set GOOGLE_API_KEY")
        return None
    
    print(f"✅ API key: {api_key[:10]}...")
    
    from research_agent import research_agent
    from script_generator import script_generator
    
    # Research
    print("\n--- RESEARCH ---")
    research = research_agent.research_storyline_sync(prompt)
    print(f"✅ {len(research.key_facts)} facts found")
    for fact in research.key_facts[:4]:
        print(f"   • {fact[:60]}...")
    
    # Script
    print("\n--- SCRIPT ---")
    script = script_generator.generate_script_sync(research, duration)
    
    print(f"\n📺 {script.title}")
    print(f"Hosts: {[h.name for h in script.hosts]}")
    
    print(f"\n📼 Segments:")
    for seg in script.segments:
        if seg.get("type") == "ai_generated":
            print(f"  {seg['order']}. [AI] {seg['speaker']} ({seg['duration_seconds']}s)")
            print(f"     \"{seg['dialogue'][:70]}...\"")
        else:
            print(f"  {seg['order']}. [CLIP] \"{seg['search_query']}\" ({seg['duration_seconds']}s)")
    
    # Save
    output = {
        "title": script.title,
        "storyline": script.storyline,
        "studio": script.studio.model_dump(),
        "hosts": [h.model_dump() for h in script.hosts],
        "segments": script.segments,
        "research_summary": script.research_summary,
        "key_facts": script.key_facts
    }
    
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Saved: {output_file}")
    return script


if __name__ == "__main__":
    # Usage: python test_prompts.py "prompt" [output_file.json]
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Why didn't the 49ers make it to the Super Bowl"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "test_output.json"
    test_full_pipeline(prompt, output_file=output_file)

"""
Test script for the Sports Narrative Generator.
Tests the full pipeline: Research → Script Generation

SETUP:
1. Set your API key: export GOOGLE_API_KEY="your-key-here"
2. Run: python test_prompts.py

Get your API key at: https://aistudio.google.com/app/apikey
"""
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_full_pipeline(prompt: str, duration: int = 150):
    """Test the complete research → script pipeline."""
    
    print("\n" + "="*60)
    print("🏈 SPORTS NARRATIVE GENERATOR - FULL PIPELINE TEST")
    print("="*60)
    print(f"Prompt: {prompt}")
    print(f"Duration: {duration}s")
    print("="*60)
    
    # Check for API key
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n❌ ERROR: No API key found!")
        print("Set your API key with:")
        print("  export GOOGLE_API_KEY='your-key-here'")
        print("\nGet your API key at: https://aistudio.google.com/app/apikey")
        return None
    
    print(f"\n✅ API key found: {api_key[:10]}...")
    
    # Import after checking API key to get better error messages
    from research_agent import research_agent
    from script_generator import script_generator
    
    # Step 1: Research
    print("\n" + "-"*60)
    print("STEP 1: RESEARCH")
    print("-"*60)
    
    research_context = research_agent.research_storyline_sync(prompt)
    
    print(f"\n📋 Research Results:")
    print(f"   Summary: {research_context.storyline_summary[:200]}...")
    print(f"   Key Facts: {len(research_context.key_facts)}")
    print(f"   Key Figures: {len(research_context.key_figures)}")
    print(f"   Timeline Events: {len(research_context.timeline)}")
    print(f"   Controversy Points: {len(research_context.controversy_points)}")
    print(f"   Sources: {len(research_context.sources)}")
    
    # Step 2: Script Generation
    print("\n" + "-"*60)
    print("STEP 2: SCRIPT GENERATION")
    print("-"*60)
    
    script = script_generator.generate_script_sync(research_context, duration)
    
    print(f"\n📺 Script Generated:")
    print(f"   Title: {script.title}")
    print(f"   Premise: {script.premise[:150]}...")
    print(f"   Hosts: {[h.name for h in script.hosts]}")
    print(f"   Segments: {len(script.segments)}")
    
    # Show segment breakdown
    print(f"\n📼 Segment Breakdown:")
    for seg in script.segments:
        if seg.segment_type == "ai_generated" and seg.ai_segment:
            ai = seg.ai_segment
            print(f"   {seg.order}. [AI] {ai.segment_type.upper()} - {ai.duration_seconds}s - {ai.mood}")
        elif seg.segment_type == "real_clip" and seg.clip_reference:
            clip = seg.clip_reference
            print(f"   {seg.order}. [CLIP] {clip.description[:50]}... - {clip.duration_seconds}s")
    
    # Save output
    output_file = "test_output.json"
    output_data = {
        "prompt": prompt,
        "research": research_context.model_dump(),
        "script": script.model_dump()
    }
    
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n💾 Full output saved to: {output_file}")
    
    return script


def test_research_only(prompt: str):
    """Test just the research phase."""
    
    print("\n" + "="*60)
    print("🔍 RESEARCH AGENT TEST")
    print("="*60)
    print(f"Prompt: {prompt}")
    
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n❌ ERROR: No API key found!")
        print("Set your API key with: export GOOGLE_API_KEY='your-key-here'")
        return None
    
    from research_agent import research_agent
    
    research_context = research_agent.research_storyline_sync(prompt)
    
    print("\n" + "="*60)
    print("RESEARCH RESULTS")
    print("="*60)
    
    print(f"\n📝 STORYLINE SUMMARY:\n{research_context.storyline_summary}")
    
    print(f"\n📊 KEY FACTS:")
    for i, fact in enumerate(research_context.key_facts, 1):
        print(f"   {i}. {fact}")
    
    print(f"\n👥 KEY FIGURES:")
    for figure in research_context.key_figures:
        print(f"   • {figure}")
    
    print(f"\n📅 TIMELINE:")
    for event in research_context.timeline:
        print(f"   • {event}")
    
    print(f"\n🔥 CONTROVERSY POINTS:")
    for point in research_context.controversy_points:
        print(f"   • {point}")
    
    print(f"\n❤️ EMOTIONAL ANGLES:")
    for angle in research_context.emotional_angles:
        print(f"   • {angle}")
    
    return research_context


# Sample prompts to test
SAMPLE_PROMPTS = [
    "Why didn't the 49ers make it to the Super Bowl this year",
    "Seattle Seahawks' surprising playoff run",
    "Bill Belichick's Hall of Fame snub controversy",
    "Patrick Mahomes dynasty vs Tom Brady legacy comparison",
    "Jayden Daniels rookie of the year campaign",
    "The rise and fall of the Dallas Cowboys",
    "Travis Kelce and Taylor Swift impact on NFL viewership",
]


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Use command line argument as prompt
        prompt = " ".join(sys.argv[1:])
    else:
        # Use first sample prompt
        prompt = SAMPLE_PROMPTS[0]
        print(f"No prompt provided. Using sample: '{prompt}'")
        print(f"\nUsage: python test_prompts.py <your sports prompt>")
        print(f"Example: python test_prompts.py Why did the Chiefs win the Super Bowl")
    
    # Run full pipeline test
    test_full_pipeline(prompt, duration=150)

"""
Test script for the three sample prompts.
Run with: GOOGLE_API_KEY="your-key" python3 test_prompts.py
"""
import os
import json

# Set API key if not already set
if not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = "AIzaSyA1V3UY6E8g9b6RQcgiFQO4p-gQa7iBUpE"

from research_agent import research_agent
from script_generator import script_generator


def test_prompt(prompt: str, duration: int = 150):
    """Test a single prompt and print results."""
    print(f"\n{'='*70}")
    print(f"🏈 TESTING: {prompt}")
    print('='*70)
    
    # Research phase
    print("\n📰 RESEARCH PHASE")
    print("-" * 40)
    research = research_agent.research_storyline_sync(prompt)
    
    print(f"\nSummary:\n{research.storyline_summary[:300]}...")
    print(f"\nKey Facts:")
    for fact in research.key_facts[:3]:
        print(f"  • {fact}")
    print(f"\nKey Figures: {', '.join(research.key_figures[:5])}")
    
    # Script generation phase
    print("\n\n📝 SCRIPT GENERATION PHASE")
    print("-" * 40)
    script = script_generator.generate_script_sync(research, duration)
    
    print(f"\n📺 Title: {script.title}")
    print(f"⏱️  Duration: {script.total_duration_seconds}s")
    print(f"\n🎬 Studio Setting:")
    print(f"   {script.studio.description[:100]}...")
    
    print(f"\n👥 Hosts:")
    for host in script.hosts:
        print(f"   • {host.name} ({host.role})")
    
    print(f"\n📋 Segments:")
    for seg in script.segments:
        if seg.segment_type == "ai_generated":
            ai = seg.ai_segment
            print(f"   {seg.order}. [AI] {ai.segment_type.upper()} - {ai.duration_seconds}s - {ai.mood}")
            if ai.dialogue:
                print(f"       First line: \"{ai.dialogue[0].text[:60]}...\"")
        else:
            clip = seg.clip_reference
            print(f"   {seg.order}. [CLIP] {clip.description[:50]}... - {clip.duration_seconds}s")
            print(f"       Search: \"{clip.search_query}\"")
    
    # Save full script to JSON
    output_file = f"output_{prompt.replace(' ', '_')[:30]}.json"
    with open(output_file, 'w') as f:
        json.dump(script.model_dump(), f, indent=2)
    print(f"\n💾 Full script saved to: {output_file}")
    
    return script


if __name__ == "__main__":
    print("\n" + "🏈"*35)
    print("   SPORTS NARRATIVE GENERATOR - TEST SUITE")
    print("🏈"*35)
    
    test_prompts = [
        "why didnt the 49ers make it to the superbowl",
        "seahawks path to the superbowl",
        "bill belichick getting snubbed from hall of fame"
    ]
    
    scripts = []
    for prompt in test_prompts:
        try:
            script = test_prompt(prompt)
            scripts.append(script)
        except Exception as e:
            print(f"\n❌ Error testing '{prompt}': {e}")
            import traceback
            traceback.print_exc()
    
    print("\n\n" + "="*70)
    print("✅ TEST COMPLETE")
    print("="*70)
    print(f"\nGenerated {len(scripts)} scripts:")
    for s in scripts:
        print(f"  • {s.title}")

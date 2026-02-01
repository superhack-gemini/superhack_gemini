"""
Test Veo Video Generation.
Uses a segment from test_output_3.json to test if Veo generation works.

Run with:
    cd backend
    python -m tests.test_veo_generation
"""
import os
import sys
import json
import asyncio

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google import genai
from google.genai import types


# API Key for Veo
VEO_API_KEY = "AIzaSyAUkxjYSl9PXPdYMebsnCrdP56k549HZfQ"


def load_test_segment():
    """Load first AI segment from test_output_3.json"""
    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_output_3.json")
    
    with open(script_path, 'r') as f:
        script = json.load(f)
    
    # Get first AI generated segment
    for segment in script['segments']:
        if segment.get('type') == 'ai_generated':
            return segment, script
    
    raise ValueError("No AI generated segment found in test_output_3.json")


async def test_veo_generation():
    """Test Veo video generation with a real segment."""
    print("=" * 60)
    print("VEO VIDEO GENERATION TEST")
    print("=" * 60)
    
    # Initialize client
    print("\n1. Initializing Veo client...")
    client = genai.Client(api_key=VEO_API_KEY)
    print("   ✓ Client initialized")
    
    # Load test segment
    print("\n2. Loading test segment from test_output_3.json...")
    segment, script = load_test_segment()
    print(f"   ✓ Loaded segment order {segment.get('order')}")
    print(f"   Speaker: {segment.get('speaker')}")
    print(f"   Dialogue: {segment.get('dialogue')[:50]}...")
    
    # Build the prompt
    print("\n3. Building Veo prompt...")
    
    # Use the studio and hosts from the segment for consistency
    studio = segment.get('studio', {})
    hosts = segment.get('hosts', [])
    
    talent_profiles = f"""
STUDIO SETTING:
{studio.get('description', 'Professional broadcast studio')}
Lighting: {studio.get('lighting', 'Professional lighting')}
Color scheme: {studio.get('color_scheme', 'Professional colors')}

HOSTS ON CAMERA:
"""
    for host in hosts:
        talent_profiles += f"- {host.get('name')} ({host.get('role')}): {host.get('appearance')}\n"
    
    scene_prompt = f"""
SCENE ACTION:
{segment.get('visual_prompt', '')}

SPEAKER: {segment.get('speaker')}
DIALOGUE: "{segment.get('dialogue')}"
DELIVERY: {segment.get('delivery')}
CAMERA: {segment.get('camera')}
DURATION: {segment.get('duration_seconds', 8)} seconds

Create a realistic broadcast segment. The host should speak the dialogue naturally.
Style: Documentary-grade, 35mm film aesthetic, professional studio lighting.
"""
    
    full_prompt = talent_profiles + scene_prompt
    print(f"   ✓ Prompt built ({len(full_prompt)} chars)")
    print("\n   --- PROMPT PREVIEW ---")
    print(full_prompt[:500] + "..." if len(full_prompt) > 500 else full_prompt)
    print("   --- END PREVIEW ---\n")
    
    # Generate video
    print("4. Generating Veo video...")
    print("   (This may take 45-90 seconds)")
    
    try:
        operation = client.models.generate_videos(
            model='veo-3.1-fast-generate-preview',
            prompt=full_prompt,
            config=types.GenerateVideosConfig(
                number_of_videos=1,
                resolution='1080p',
                aspect_ratio='16:9'
            )
        )
        print(f"   ✓ Generation started. Operation: {operation.name if hasattr(operation, 'name') else 'unknown'}")
        
        # Poll for completion
        poll_count = 0
        while not operation.done:
            poll_count += 1
            print(f"   ... Polling ({poll_count}) - waiting 10s")
            await asyncio.sleep(10)
        
        print(f"   ✓ Generation complete after {poll_count} polls")
        
        # Check result
        print("\n5. Checking result...")
        
        if not operation.response:
            print(f"   ✗ ERROR: No response. State: {getattr(operation, 'state', 'unknown')}")
            return False
        
        generated_videos = getattr(operation.response, 'generated_videos', [])
        if not generated_videos:
            print("   ✗ ERROR: No generated_videos in response")
            print(f"   Response: {operation.response}")
            return False
        
        video = generated_videos[0]
        video_uri = video.video.uri if video.video else None
        
        if not video_uri:
            print("   ✗ ERROR: No video URI in response")
            return False
        
        print(f"   ✓ Video URI: {video_uri[:80]}...")
        
        # Download video
        print("\n6. Downloading video...")
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "videos", "veo_test")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"test_segment_{segment.get('order')}.mp4")
        
        import aiohttp
        download_url = f"{video_uri}&key={VEO_API_KEY}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url) as response:
                if response.status == 200:
                    with open(output_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                    print(f"   ✓ Video saved to: {output_path}")
                else:
                    print(f"   ✗ Download failed: {response.status}")
                    return False
        
        print("\n" + "=" * 60)
        print("✅ VEO TEST PASSED!")
        print(f"   Video saved: {output_path}")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n   ✗ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_prompt_refinement_only():
    """Test just the prompt refinement (uses Gemini, not Veo)."""
    print("=" * 60)
    print("PROMPT REFINEMENT TEST (Gemini only, no video)")
    print("=" * 60)
    
    client = genai.Client(api_key=VEO_API_KEY)
    
    segment, _ = load_test_segment()
    
    prompt = f"""Act as a cinematic director for a sports documentary broadcast.
Transform this segment into a highly detailed visual prompt for Veo video generation.

STRICT REQUIREMENTS:
1. DURATION: Must be exactly {segment.get('duration_seconds', 8)} seconds.
2. SPEAKER: {segment.get('speaker')}
3. DIALOGUE: "{segment.get('dialogue')}"
4. DELIVERY: {segment.get('delivery')}
5. CAMERA: {segment.get('camera')}
6. VISUALS: {segment.get('visual_prompt')}
7. STYLE: Organic, 35mm film aesthetic, professional studio lighting. NO CGI feel.

Return a single descriptive paragraph focused on natural performances and facial micro-expressions.
The scene should feel like real broadcast television."""

    print("\nCalling Gemini to refine prompt...")
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        print("\n✅ Gemini Response:")
        print("-" * 40)
        print(response.text)
        print("-" * 40)
        return True
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return False


if __name__ == "__main__":
    print("\nSelect test to run:")
    print("1. Full Veo video generation test (takes 1-2 minutes)")
    print("2. Prompt refinement only (quick Gemini test)")
    print()
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        result = asyncio.run(test_veo_generation())
        sys.exit(0 if result else 1)
    elif choice == "2":
        result = asyncio.run(test_prompt_refinement_only())
        sys.exit(0 if result else 1)
    else:
        # Default to full test
        print("Running full Veo test...")
        result = asyncio.run(test_veo_generation())
        sys.exit(0 if result else 1)

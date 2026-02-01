"""
Test Veo Video Generation - Single Segment at 720p.
Based on official docs: https://ai.google.dev/gemini-api/docs/video

Run: cd backend && python tests/test_veo_single.py
"""
import time
import json
import os

# API Key
VEO_API_KEY = "AIzaSyAUkxjYSl9PXPdYMebsnCrdP56k549HZfQ"

print("=" * 60)
print("VEO SINGLE VIDEO TEST (720p - Fast & Cheap)")
print("=" * 60)

# Import
from google import genai
from google.genai import types

# Create client
client = genai.Client(api_key=VEO_API_KEY)

# Load segment order 1 from test_output_3.json
script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_output_3.json")
with open(script_path, 'r') as f:
    script = json.load(f)

segment = script['segments'][0]  # Order 1
print(f"\nSegment Order: {segment.get('order')}")
print(f"Speaker: {segment.get('speaker')}")
print(f"Dialogue: {segment.get('dialogue')}")

# Build prompt following Veo docs format
# Keep it simple and direct like the docs example
studio = segment.get('studio', {})
hosts = segment.get('hosts', [])

# Find the speaking host
speaker_name = segment.get('speaker', 'Marcus Webb')
speaker_host = next((h for h in hosts if h['name'] == speaker_name), hosts[0] if hosts else {})

prompt = f"""A professional sports broadcast studio with dark background and subtle blue accent lighting.
{speaker_host.get('appearance', 'A professional news anchor in a suit')}, seated at a curved news desk.
The anchor looks at the camera and says: "{segment.get('dialogue')}"
Delivery style: {segment.get('delivery', 'professional')}. Camera: {segment.get('camera', 'medium shot')}.
Duration: 8 seconds. Professional broadcast lighting. 16:9 aspect ratio."""

print(f"\n--- PROMPT ---")
print(prompt)
print("--- END PROMPT ---\n")

# Generate video at 720p (faster)
print("Starting Veo generation (720p for speed)...")
print("Expected time: 45-90 seconds\n")

start_time = time.time()

try:
    # Following exact pattern from docs
    operation = client.models.generate_videos(
        model="veo-3.1-fast-generate-preview",  # Fast variant
        prompt=prompt,
        config=types.GenerateVideosConfig(
            number_of_videos=1,
            resolution="720p",  # 720p is fastest
            aspect_ratio="16:9"
        )
    )
    
    print(f"✓ Generation initiated ({time.time() - start_time:.1f}s)")
    
    # Poll using the correct method from docs
    poll_count = 0
    while not operation.done:
        poll_count += 1
        elapsed = int(time.time() - start_time)
        print(f"  Waiting... ({elapsed}s elapsed, poll #{poll_count})")
        time.sleep(10)
        operation = client.operations.get(operation)
    
    elapsed = time.time() - start_time
    print(f"\n✓ Generation complete! ({elapsed:.0f} seconds)")
    
    # Get the video
    generated_video = operation.response.generated_videos[0]
    
    # Download using the docs method
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "videos", "veo_test")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "segment_1_720p.mp4")
    
    print(f"Downloading video...")
    client.files.download(file=generated_video.video)
    generated_video.video.save(output_path)
    
    print(f"\n" + "=" * 60)
    print(f"✅ SUCCESS!")
    print(f"   Video saved: {output_path}")
    print(f"   Generation time: {elapsed:.0f} seconds")
    print("=" * 60)

except Exception as e:
    elapsed = time.time() - start_time
    print(f"\n✗ ERROR after {elapsed:.0f}s: {type(e).__name__}: {e}")
    
    # Helpful error messages
    error_str = str(e).lower()
    if 'permission' in error_str or 'denied' in error_str or '403' in error_str:
        print("\n⚠️  API key may not have Veo access.")
        print("   Veo requires special API permissions.")
    elif 'quota' in error_str or '429' in error_str:
        print("\n⚠️  Rate limit or quota exceeded.")
    elif 'not found' in error_str or '404' in error_str:
        print("\n⚠️  Model not found - check model name.")
    
    import traceback
    traceback.print_exc()

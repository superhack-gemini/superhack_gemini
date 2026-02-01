"""
Quick Veo API diagnostic test.
Tests if the API key works and Veo is accessible.

Run: python tests/test_veo_quick.py
"""
import os
import sys
import time

# API Key
VEO_API_KEY = "AIzaSyAUkxjYSl9PXPdYMebsnCrdP56k549HZfQ"

print("=" * 60)
print("VEO QUICK DIAGNOSTIC TEST")
print("=" * 60)

# Step 1: Test imports
print("\n1. Testing imports...")
try:
    from google import genai
    from google.genai import types
    print("   ✓ google-genai imported successfully")
except ImportError as e:
    print(f"   ✗ Import failed: {e}")
    print("   Run: pip install google-genai")
    sys.exit(1)

# Step 2: Test client creation
print("\n2. Creating Veo client...")
try:
    client = genai.Client(api_key=VEO_API_KEY)
    print("   ✓ Client created")
except Exception as e:
    print(f"   ✗ Client creation failed: {e}")
    sys.exit(1)

# Step 3: Test a simple Gemini call first (quick)
print("\n3. Testing Gemini API (quick validation)...")
try:
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents='Say "Veo test successful" in exactly those words.'
    )
    print(f"   ✓ Gemini response: {response.text[:50]}...")
except Exception as e:
    print(f"   ✗ Gemini call failed: {e}")
    print("   This suggests the API key may be invalid or lack permissions")
    sys.exit(1)

# Step 4: Test Veo video generation (this is the slow part)
print("\n4. Testing Veo video generation...")
print("   ⚠️  This takes 45-90 seconds - that's NORMAL for AI video")
print("   Starting generation...")

simple_prompt = """
A professional news anchor in a dark broadcast studio.
The anchor, a distinguished man in his 40s wearing a charcoal suit,
looks directly at the camera and says: "Welcome to the show."
Duration: 5 seconds. Professional lighting. 16:9 aspect ratio.
"""

try:
    start_time = time.time()
    
    operation = client.models.generate_videos(
        model='veo-3.1-fast-generate-preview',
        prompt=simple_prompt,
        config=types.GenerateVideosConfig(
            number_of_videos=1,
            resolution='720p',  # Lower res for faster test
            aspect_ratio='16:9'
        )
    )
    
    print(f"   ✓ Generation started (took {time.time() - start_time:.1f}s to initiate)")
    print(f"   Operation name: {getattr(operation, 'name', 'N/A')}")
    
    # Poll with timeout
    poll_count = 0
    max_polls = 20  # ~3 minutes max
    
    while not operation.done and poll_count < max_polls:
        poll_count += 1
        elapsed = time.time() - start_time
        print(f"   ... Polling #{poll_count} (elapsed: {elapsed:.0f}s)")
        time.sleep(10)
    
    elapsed = time.time() - start_time
    
    if operation.done:
        print(f"   ✓ Generation completed in {elapsed:.0f} seconds")
        
        # Check for video
        if operation.response:
            videos = getattr(operation.response, 'generated_videos', [])
            if videos and videos[0].video:
                uri = videos[0].video.uri
                print(f"   ✓ Video URI: {uri[:60]}...")
                print("\n" + "=" * 60)
                print("✅ VEO IS WORKING!")
                print("=" * 60)
            else:
                print("   ⚠️  Response received but no video URI")
                print(f"   Response: {operation.response}")
        else:
            print(f"   ⚠️  No response. Error: {getattr(operation, 'error', 'unknown')}")
    else:
        print(f"   ✗ Timed out after {elapsed:.0f} seconds")
        print("   This could mean:")
        print("   - Veo servers are overloaded")
        print("   - API key doesn't have Veo access")
        print("   - Network issues")
        
except Exception as e:
    print(f"   ✗ Veo generation failed: {type(e).__name__}: {e}")
    
    # Check for specific errors
    error_str = str(e).lower()
    if 'permission' in error_str or 'denied' in error_str:
        print("\n   ⚠️  This API key may not have Veo access.")
        print("   Veo requires special API access - not all keys work.")
    elif 'quota' in error_str:
        print("\n   ⚠️  API quota exceeded.")
    elif 'model' in error_str and 'not found' in error_str:
        print("\n   ⚠️  Veo model not available for this API key.")
    
    import traceback
    traceback.print_exc()
    sys.exit(1)

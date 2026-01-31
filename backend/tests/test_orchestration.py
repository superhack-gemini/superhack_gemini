import os
import pytest
from orchestration import retrieve_video, Video, load_dotenv, run_workflow, youtube_scraper_tool

# Ensure env vars are loaded for the test environment
load_dotenv()

@pytest.fixture
def test_video_url():
    # Use a short, stable video for testing retrieval
    return "https://www.youtube.com/shorts/9_R08X_ZxQU"

def test_retrieve_video_integration(test_video_url):
    """
    Integration test that hits the real Publer API.
    Requires a valid PUBLER_TOKEN in the .env file.
    """
    assert os.getenv("PUBLER_TOKEN") is not None, "PUBLER_TOKEN must be set in .env for this test"
    print(f"\n--- Testing real retrieval for: {test_video_url} ---")
    
    try:
        result = retrieve_video(test_video_url)
        assert isinstance(result, Video)
        assert result.path.endswith(".mp4")
        assert os.path.exists(result.path)
        assert len(result.title) > 0
        print(f"Successfully retrieved video: {result.title} at {result.path}")
    except Exception as e:
        pytest.fail(f"Video retrieval failed: {e}")

def test_youtube_scraper_integration():
    """
    Integration test for the YouTube Search Scraper tool using browser-use.
    Requires BROWSER_USE_API_KEY in .env.
    """
    assert os.getenv("BROWSER_USE_API_KEY") is not None, "BROWSER_USE_API_KEY must be set in .env for this test"
    
    query = "New England Patriots snow game interception shorts"
    print(f"\n--- Testing youtube_scraper_tool for: {query} ---")
    
    try:
        result = youtube_scraper_tool.invoke({"query": query})
        print(f"Scraper Result:\n{result}")
        assert isinstance(result, list)
        if len(result) > 0:
            assert all(isinstance(url, str) for url in result)
            assert all(url.startswith("https://") for url in result)
            print(f"Successfully retrieved {len(result)} URLs")
    except Exception as e:
        pytest.fail(f"YouTube scraper tool failed: {e}")

def test_full_workflow_integration():
    """
    End-to-End integration test for the entire sports narrative pipeline.
    Verifies: Fanout -> Research -> Script Generation -> Clip Retrieval.
    """
    # Check for all required API keys
    assert os.getenv("GEMINI_API_KEY") is not None, "GEMINI_API_KEY is missing"
    assert os.getenv("BROWSER_USE_API_KEY") is not None, "BROWSER_USE_API_KEY is missing"
    assert os.getenv("PUBLER_TOKEN") is not None, "PUBLER_TOKEN is missing"

    prompt = "Why did the 49ers lose the Super Bowl to the Chiefs in 2024?"
    duration = 90  # Keep it short for testing
    
    print(f"\n{'='*60}")
    print(f"🏈 TESTING FULL PIPELINE: {prompt}")
    print(f"{'='*60}\n")
    
    try:
        # Execute the full workflow
        result = run_workflow(prompt, duration_seconds=duration)
        
        # 1. Verify Structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert result.get("prompt") == prompt
        assert result.get("status") == "clips_retrieved", f"Workflow did not complete (Status: {result.get('status')})"
        
        # 2. Verify Research
        assert result.get("research_context"), "Research context is missing"
        print("✅ Research Context populated")
        
        # 3. Verify Script
        script = result.get("script")
        assert script, "Script JSON is missing"
        assert script.get("title"), "Script missing title"
        assert len(script.get("segments")) > 0, "Script has no segments"
        print(f"✅ Script generated: {script['title']} ({len(script['segments'])} segments)")
        
        # 4. Verify Retrieved Clips
        retrieved_clips = result.get("retrieved_clips")
        assert retrieved_clips, "No clips were retrieved"
        assert isinstance(retrieved_clips, list)
        
        print(f"✅ Retrieved {len(retrieved_clips)} clips")
        
        import uuid
        for clip in retrieved_clips:
            # Check structure
            assert "query" in clip
            assert "video_path" in clip
            assert "original_url" in clip
            
            # Check file existence
            path = clip["video_path"]
            assert os.path.exists(path), f"Video file not found: {path}"
            
            # Check filename is UUID
            filename = os.path.basename(path)
            name_part = filename.split('.')[0]
            try:
                uuid.UUID(name_part)
                print(f"  Valid UUID filename: {filename}")
            except ValueError:
                pytest.fail(f"Filename is not a valid UUID: {filename}")
                
            print(f"  Mapped query '{clip['query']}' -> {filename}")
        
    except Exception as e:
        pytest.fail(f"Full workflow failed: {e}")

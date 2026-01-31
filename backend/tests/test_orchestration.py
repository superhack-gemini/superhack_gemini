import os
import pytest
from orchestration import retrieve_video, Video, load_dotenv, run_workflow, fanout_search_node, HumanMessage, youtube_scraper_tool

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
    # Check if token exists
    assert os.getenv("PUBLER_TOKEN") is not None, "PUBLER_TOKEN must be set in .env for this test"

    print(f"\n--- Testing real retrieval for: {test_video_url} ---")
    
    # Run the function
    try:
        result = retrieve_video(test_video_url)
        
        # Assertions
        assert isinstance(result, Video)
        assert result.path.endswith(".mp4")
        assert os.path.exists(result.path)
        assert len(result.title) > 0
        
        print(f"Successfully retrieved video: {result.title} at {result.path}")
        
    except Exception as e:
        pytest.fail(f"Video retrieval failed: {e}")

def test_retrieve_video_no_token(monkeypatch):
    """
    Verifies that the function raises an error when the token is missing.
    """
    monkeypatch.delenv("PUBLER_TOKEN", raising=False)
    with pytest.raises(ValueError, match="PUBLER_TOKEN not found"):
        retrieve_video("http://example.com")

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
        
        # Assertions - should now be a list of URLs
        assert isinstance(result, list)
        if len(result) > 0:
            assert all(isinstance(url, str) for url in result)
            assert all(url.startswith("https://") for url in result)
            print(f"Successfully retrieved {len(result)} URLs")
        else:
            print("No URLs found (scraped list is empty)")
        
    except Exception as e:
        pytest.fail(f"YouTube scraper tool failed: {e}")

import os
import pytest
from orchestration import retrieve_video, Video, load_dotenv, run_workflow, fanout_search_node, HumanMessage

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
    finally:
        # Optional: Cleanup downloaded file
        # if 'result' in locals() and os.path.exists(result.path):
        #     os.remove(result.path)
        pass

def test_retrieve_video_no_token(monkeypatch):
    """
    Verifies that the function raises an error when the token is missing.
    """
    monkeypatch.delenv("PUBLER_TOKEN", raising=False)
    with pytest.raises(ValueError, match="PUBLER_TOKEN not found"):
        retrieve_video("http://example.com")

    except Exception as e:
        pytest.fail(f"Fanout query generation failed: {e}")

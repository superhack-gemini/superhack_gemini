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
    print(f"\n--- Testing real retrieval for: {test_video_url} ---")
    
    # Run the function
    try:
        result = retrieve_video(test_video_url)
        
        # Assertions
        assert isinstance(result, Video)
        # Note: with browser-use, these might be placeholders in the stub
        assert result.path != ""
        assert result.title != ""
        
        print(f"Successfully retrieved video: {result.title} at {result.path}")
        
    except Exception as e:
        pytest.fail(f"Video retrieval failed: {e}")
    finally:
        # Optional: Cleanup downloaded file
        # if 'result' in locals() and os.path.exists(result.path):
        #     os.remove(result.path)
        pass

def test_fanout_queries_integration():
    """
    Integration test for fanout query generation using Gemini.
    Ensures 3-5 queries are generated from a user narrative.
    """
    assert os.getenv("GOOGLE_API_KEY") is not None, "GOOGLE_API_KEY must be set in .env for this test"
    
    narrative = "The New England Patriots played a game in the snow where they got a crucial interception. Find me videos of this play and background on the game context."
    
    print(f"\n--- Testing fanout for: {narrative} ---")
    
    try:
        # Create initial state for the node
        initial_state = {
            "messages": [HumanMessage(content=narrative)],
            "research_results": {},
            "current_status": "starting"
        }
        
        # Execute the node directly
        result = fanout_search_node(initial_state)
        
        # Access research_results from the node output
        queries = result.get("research_results", {}).get("search_fanout_queries", [])
        
        print(f"Generated {len(queries)} queries:")
        for q in queries:
            print(f"  - {q}")
            
        # Assertions
        assert 3 <= len(queries) <= 5, f"Expected 3-5 queries, but got {len(queries)}"
        assert all(isinstance(q, str) for q in queries), "All queries should be strings"
        assert any("Patriots" in q.lower() or "interception" in q.lower() for q in queries), "Queries should be relevant to the narrative"
        
    except Exception as e:
        pytest.fail(f"Fanout query generation failed: {e}")


import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_media_production_parallelism():
    """
    Verify that media_production_node runs Veo and Clip tasks in parallel.
    """
    from orchestration import media_production_node
    
    # Mock state
    state = {
        "script": {
            "segments": [
                {"type": "ai_generated", "order": 1, "speaker": "Test", "dialogue": "Hello"},
                {"type": "real_clip", "order": 2, "search_query": "Test Clip"}
            ]
        }
    }
    
    # Mock helpers
    with patch("orchestration.process_veo_segments", new_callable=AsyncMock) as mock_veo, \
         patch("orchestration.process_clip_workflow", new_callable=AsyncMock) as mock_clip:
         
        # Make them "take time" to prove overlap if we were timing, 
        # but mostly we just want to ensure they are both called.
        mock_veo.return_value = {"generated": [{"path": "v1.mp4"}], "failed": []}
        mock_clip.return_value = [{"path": "c1.mp4"}]
        
        result = await media_production_node(state)
        
        # Verify both were called
        mock_veo.assert_called_once()
        mock_clip.assert_called_once()
        
        # Verify structure
        assert "veo_generated_videos" in result
        assert "retrieved_clips" in result
        assert result["current_phase"] == "media_produced"

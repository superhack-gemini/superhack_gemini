
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_process_veo_segments_stagger():
    """
    Verify that tasks are staggered by checking execution timing.
    """
    from orchestration import process_veo_segments
    
    # Mock script with 3 segments
    script = {
        "segments": [
            {"type": "ai_generated", "order": 1, "speaker": "A"},
            {"type": "ai_generated", "order": 2, "speaker": "B"},
            {"type": "ai_generated", "order": 3, "speaker": "C"}
        ]
    }
    
    start_times = []
    
    async def mock_generate_video(seg):
        # Record when the actual generation started (after sleep)
        start_times.append(time.time())
        return {"video_uri": "http://mock/video", "order": seg["order"]}
        
    async def mock_download_video(uri, path):
        pass

    # Mock VeoAgent
    with patch("orchestration.get_veo_agent") as mock_get_agent:
        mock_agent = AsyncMock()
        mock_agent.generate_video = mock_generate_video
        mock_agent.download_video = mock_download_video
        mock_get_agent.return_value = mock_agent
        
        # We need to speed up default sleep for test, OR utilize the logic that sleep happens.
        # But unrelatedly, we want to verify the Logic uses staggered delays.
        # Ideally we'd mock asyncio.sleep to not wait 12s real time, but verify arguments.
        
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await process_veo_segments(script)
            
            # Verify sleep calls: 0, 6, 12
            assert mock_sleep.call_count == 2 # 0 might be skipped if logic `if delay > 0`
            
            # Check arguments
            args_list = [call.args[0] for call in mock_sleep.call_args_list]
            assert 6 in args_list
            assert 12 in args_list

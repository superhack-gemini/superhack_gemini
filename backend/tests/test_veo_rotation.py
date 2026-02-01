
import pytest
from unittest.mock import MagicMock, patch
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from veo_agent import VeoAgent

def test_key_rotation_init():
    """Verify VeoAgent initializes with multiple keys correctly."""
    with patch.dict(os.environ, {
        "VEO_API_KEY": "key1",
        "VEO_API_KEY2": "key2",
        "VEO_API_KEY3": "key3"
    }):
        with patch('google.genai.Client') as MockClient:
            agent = VeoAgent()
            assert len(agent.api_keys) == 3
            assert len(agent.clients) == 3
            assert agent.api_keys == ["key1", "key2", "key3"]
            
            # Check clients initialized with correct keys
            # MockClient call args
            calls = MockClient.call_args_list
            assert calls[0].kwargs['api_key'] == "key1"
            assert calls[1].kwargs['api_key'] == "key2"
            assert calls[2].kwargs['api_key'] == "key3"

def test_rotation_logic():
    """Verify _get_client_and_key rotates correctly."""
    with patch.dict(os.environ, {
        "VEO_API_KEY": "key1",
        "VEO_API_KEY2": "key2",
        "VEO_API_KEY3": "key3"
    }):
        with patch('google.genai.Client') as MockClient:
            agent = VeoAgent()
            
            c1, k1 = agent._get_client_and_key()
            c2, k2 = agent._get_client_and_key()
            c3, k3 = agent._get_client_and_key()
            c4, k4 = agent._get_client_and_key()
            
            assert k1 == "key1"
            assert k2 == "key2"
            assert k3 == "key3"
            assert k4 == "key1" # Looped back

def test_single_key_fallback():
    """Verify it works with just one key."""
    with patch.dict(os.environ, {
        "VEO_API_KEY": "key1",
        "VEO_API_KEY2": "",
        "VEO_API_KEY3": ""
    }):
        with patch('google.genai.Client') as MockClient:
            agent = VeoAgent()
            assert len(agent.api_keys) == 1
            c1, k1 = agent._get_client_and_key()
            c2, k2 = agent._get_client_and_key()
            assert k1 == "key1"
            assert k2 == "key1"

@pytest.mark.asyncio
async def test_generate_video_returns_key():
    """Verify generate_video returns the used api_key in the result."""
    with patch.dict(os.environ, {"VEO_API_KEY": "key1"}):
        with patch('google.genai.Client') as MockClient:
            agent = VeoAgent()
            
            # Mock the client operation
            mock_client_instance = MockClient.return_value
            mock_op = MagicMock()
            mock_op.name = "ops/123"
            mock_op.done = True
            mock_op.response.generated_videos = [MagicMock()]
            mock_op.response.generated_videos[0].video.uri = "http://video"
            
            # generate_videos return value
            mock_client_instance.models.generate_videos.return_value = mock_op
            # operations.get return value (though we mock done=True so it might skip polling if we test right)
            # Actually our code sleeps 8s first? No, default loop checks done.
            # Wait, the code:
            # while not operation.done:
            # So if done is True internally initially, it skips loop?
            # User code: while not operation.done: ...
            
            result = await agent.generate_video({"order": 1})
            
            assert result["api_key"] == "key1"
            assert result["video_uri"] == "http://video"


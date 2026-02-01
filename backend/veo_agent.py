"""
Veo Video Generation Agent.
Generates AI videos using Google Veo 3.1 for broadcast segments.

Ported from services/geminiService.ts
"""
import os
import time
import asyncio
import aiohttp
from typing import Optional, Callable, Dict, Any
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()


class VeoAgent:
    """
    Agent for generating AI broadcast videos using Veo 3.1.
    Handles prompt refinement and video generation with retry logic.
    """
    
    # Locked talent profiles for visual consistency
    TALENT_PROFILES = """
TALENT PROFILES (LOCKED):
- Lead Anchor (Marcus Webb): Distinguished man, late 40s, charcoal suit, silver-streaked hair, professional demeanor.
- Analyst (Sarah Chen): Professional woman, early 30s, emerald green blazer, sharp analytical presence.

SETTING:
Realistic sports broadcast studio. Soft-focus background monitors showing highlights.
Documentary-grade lighting. Clean, modern aesthetic.
"""
    
    def __init__(self, api_keys: Optional[list] = None):
        import itertools
        
        # Load keys from env
        keys = [
            os.getenv("VEO_API_KEY"),
            os.getenv("VEO_API_KEY2"),
            os.getenv("VEO_API_KEY3")
        ]
        
        # Filter valid keys (or passed ones)
        self.api_keys = [k for k in keys if k]
        
        if api_keys:
             self.api_keys = api_keys
             
        if not self.api_keys:
            raise ValueError("No VEO_API_KEYs found. Set VEO_API_KEY, VEO_API_KEY2, or VEO_API_KEY3.")
        
        print(f"DEBUG: Initialized VeoAgent with {len(self.api_keys)} keys")
        
        # Create client pool
        self.clients = [genai.Client(api_key=k) for k in self.api_keys]
        self.client_pool = list(zip(self.clients, self.api_keys))
        self._pool_cycle = itertools.cycle(self.client_pool)
        
    def _get_client_and_key(self):
        """Get the next (client, key) tuple in the rotation."""
        return next(self._pool_cycle)
    
    async def _with_retry(self, fn: Callable, max_retries: int = 3) -> Any:
        """
        Execute a function with exponential backoff for overloaded/rate-limited errors.
        """
        last_error = None
        
        for i in range(max_retries):
            try:
                return await fn()
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                
                is_overloaded = 'overloaded' in error_msg or '503' in error_msg
                is_rate_limited = 'rate limit' in error_msg or '429' in error_msg
                
                if is_overloaded or is_rate_limited:
                    delay = (2 ** i) + (asyncio.get_event_loop().time() % 1)
                    print(f"Model busy/overloaded. Retrying in {delay:.1f}s... (Attempt {i + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                    continue
                    
                raise e
        
        raise last_error
    
    async def refine_prompt(self, segment: Dict[str, Any]) -> str:
        """
        Refine a segment into a detailed Veo video prompt.
        
        Args:
            segment: AI segment data with dialogue, mood, visual_prompt, etc.
            
        Returns:
            Refined prompt optimized for Veo generation
        """
        # Extract segment details
        dialogue = segment.get('dialogue', '')
        speaker = segment.get('speaker', 'Marcus Webb')
        delivery = segment.get('delivery', 'professional')
        mood = segment.get('mood', 'professional')
        visual_prompt = segment.get('visual_prompt', '')
        camera = segment.get('camera', 'Medium shot')
        duration = segment.get('duration_seconds', 8)
        
        prompt = f"""Act as a cinematic director for a sports documentary broadcast.
Transform this segment into a highly detailed visual prompt for Veo video generation.

STRICT REQUIREMENTS:
1. DURATION: Must be exactly {duration} seconds.
2. SPEAKER: {speaker}
3. DIALOGUE: "{dialogue}"
4. DELIVERY: {delivery}
5. MOOD: {mood}
6. CAMERA: {camera}
7. VISUALS: {visual_prompt}
8. STYLE: Organic, 35mm film aesthetic, professional studio lighting. NO CGI feel.

Return a single descriptive paragraph focused on natural performances and facial micro-expressions.
The scene should feel like real broadcast television."""

        async def _call():
            client, _ = self._get_client_and_key()
            response = await asyncio.to_thread(
                client.models.generate_content,
                model='gemini-2.5-flash',
                contents=prompt
            )
            return response.text
        
        return await self._with_retry(_call)
    
    async def generate_video(
        self, 
        segment: Dict[str, Any],
        on_progress: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Generate a Veo video for a broadcast segment.
        
        Args:
            segment: AI segment data
            on_progress: Optional callback for status updates
            
        Returns:
            Dict with video_uri and metadata
        """
        if on_progress:
            on_progress("Refining prompt for cinematic generation...")
        
        # Refine the prompt
        refined_prompt = await self.refine_prompt(segment)
        
        # Build full prompt with talent consistency
        full_prompt = f"{self.TALENT_PROFILES}\n\nSCENE ACTION: {refined_prompt}"
        
        if on_progress:
            on_progress("Connecting to Veo cinematic engine...")
            
        client, api_key = self._get_client_and_key()
        
        # Generate video with retry
        async def _generate():
            operation = client.models.generate_videos(
                model='veo-3.1-fast-generate-preview',
                prompt=full_prompt,
                config=types.GenerateVideosConfig(
                    number_of_videos=1,
                    resolution='720p',
                    aspect_ratio='16:9'
                )
            )
            return operation
        
        operation = await self._with_retry(_generate)             
        
        # Poll for completion
        while not operation.done:
            await asyncio.sleep(8)
            if on_progress:
                on_progress("Capturing organic talent performance... (45-60s)")
        
        # Extract video URI
        if not operation.response:
            raise Exception(f"Operation completed but response is missing. State: {operation.state}")
            
        # Safe access to generated_videos
        generated_videos = getattr(operation.response, 'generated_videos', [])
        if not generated_videos:
             raise Exception("No generated_videos found in operation response.")

        video = generated_videos[0]
        video_uri = video.video.uri if video.video else None
        
        if not video_uri:
            raise Exception("No video URI returned from Veo.")
        
        if on_progress:
            on_progress("Video generated successfully!")
        
        return {
            "video_uri": video_uri,
            "api_key": api_key, # Return the key used (needed for download)
            "segment_order": segment.get('order', 0),
            "duration_seconds": segment.get('duration_seconds', 5),
            "speaker": segment.get('speaker'),
            "dialogue": segment.get('dialogue')
        }
    
    async def download_video(self, video_uri: str, output_path: str, api_key: str = None) -> str:
        """
        Download a generated video from Veo.
        
        Args:
            video_uri: The URI returned from Veo
            output_path: Local path to save the video
            api_key: The API key used to generate the video (required for permission)
            
        Returns:
            Path to the downloaded video
        """
        key_to_use = api_key or (self.api_keys[0] if self.api_keys else None)
        if not key_to_use:
             raise ValueError("API key required for download")
             
        download_url = f"{video_uri}&key={key_to_use}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url) as response:
                response.raise_for_status()
                
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                with open(output_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
        
        return output_path
    
    async def generate_segment_videos(
        self,
        segments: list,
        output_dir: str,
        on_progress: Optional[Callable[[str, int, int], None]] = None
    ) -> list:
        """
        Generate videos for all AI segments in a script.
        
        Args:
            segments: List of segments from the script
            output_dir: Directory to save videos
            on_progress: Callback(message, current, total)
            
        Returns:
            List of generated video paths with metadata
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Filter AI segments only
        ai_segments = [
            s for s in segments 
            if s.get('type') == 'ai_generated'
        ]
        
        results = []
        total = len(ai_segments)
        
        for i, segment in enumerate(ai_segments):
            if on_progress:
                on_progress(f"Generating video {i + 1}/{total}", i + 1, total)
            
            try:
                # Generate video
                result = await self.generate_video(
                    segment,
                    on_progress=lambda msg: on_progress(msg, i + 1, total) if on_progress else None
                )
                
                # Download video
                video_path = os.path.join(output_dir, f"segment_{segment.get('order', i)}.mp4")
                await self.download_video(result['video_uri'], video_path)
                
                result['local_path'] = video_path
                results.append(result)
                
            except Exception as e:
                print(f"Failed to generate video for segment {i + 1}: {e}")
                results.append({
                    "error": str(e),
                    "segment_order": segment.get('order', i)
                })
        
        return results


# Singleton instance for easy access
_veo_agent: Optional[VeoAgent] = None


def get_veo_agent() -> VeoAgent:
    """Get or create the Veo agent singleton."""
    global _veo_agent
    if _veo_agent is None:
        _veo_agent = VeoAgent()
    return _veo_agent


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    import json
    
    async def test_veo():
        agent = VeoAgent()
        
        test_segment = {
            "order": 1,
            "type": "ai_generated",
            "duration_seconds": 8,
            "visual_prompt": "Studio setting, lead anchor at desk",
            "speaker": "Marcus Webb",
            "dialogue": "The 49ers were supposed to be here. Instead, they're watching from home.",
            "delivery": "Somber, measured pace",
            "camera": "Slow push in to medium shot",
            "mood": "somber but professional"
        }
        
        print("Testing Veo Agent...")
        print(f"Segment: {json.dumps(test_segment, indent=2)}")
        
        # Test prompt refinement
        refined = await agent.refine_prompt(test_segment)
        print(f"\nRefined Prompt:\n{refined}")
        
        # Uncomment to test actual video generation (uses API quota)
        # result = await agent.generate_video(test_segment, lambda msg: print(f"Status: {msg}"))
        # print(f"\nResult: {result}")
    
    asyncio.run(test_veo())

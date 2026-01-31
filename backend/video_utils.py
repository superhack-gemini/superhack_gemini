import os
import ffmpeg
from typing import List

def combine_videos(video_paths: List[str], output_path: str):
    """
    Combines multiple video files into a single video file using ffmpeg.
    
    This function:
    1. Resizes all input videos to 1080x1920 (Vertical/Shorts format).
    2. Concatenates them sequentially.
    3. Handles audio streams.
    
    Args:
        video_paths: List of absolute paths to the video files.
        output_path: Absolute path for the output video.
    """
    if not video_paths:
        raise ValueError("No video paths provided for combination.")
        
    inputs = []
    
    for path in video_paths:
        if not os.path.exists(path):
            print(f"Warning: Video file not found: {path}, skipping.")
            continue
            
        inp = ffmpeg.input(path)
        
        # Scale to 1080x1920 (Vertical HD) and set pixel aspect ratio to 1
        # force_original_aspect_ratio='decrease' + pad could be better, 
        # but for now we force scale to fill or stretch to keep it simple.
        # "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" -> fills screen
        desc = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1"
        
        # Apply filter chain string
        v = inp.video.filter('scale', 1080, 1920, force_original_aspect_ratio='increase') \
                     .filter('crop', 1080, 1920) \
                     .filter('setsar', 1)
        
        a = inp.audio
        inputs.append(v)
        inputs.append(a)
    
    if not inputs:
        raise ValueError("No valid video inputs found.")

    try:
        # Concatenate: n=number of clips, v=1 video stream, a=1 audio stream
        # Note: *inputs expands the list [v1, a1, v2, a2...]
        joined = ffmpeg.concat(*inputs, v=1, a=1).node
        v = joined[0]
        a = joined[1]
        
        out = ffmpeg.output(v, a, output_path, vcodec='libx264', acodec='aac')
        
        print(f"Starting ffmpeg concatenation to {output_path}...")
        out.run(overwrite_output=True, quiet=True)
        print(f"Successfully created: {output_path}")
        
    except ffmpeg.Error as e:
        print("FFmpeg Error:")
        if e.stderr:
            print(e.stderr.decode('utf8'))
        raise e
    except Exception as e:
        print(f"General Error during video combination: {e}")
        raise e

def cut_video(input_path: str, output_path: str, start_time: str, end_time: str):
    """
    Cuts a video file from start_time to end_time.
    
    Args:
        input_path: Absolute path to the input video.
        output_path: Absolute path for the output video.
        start_time: Start time in HH:MM:SS format or seconds.
        end_time: End time in HH:MM:SS format or seconds.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input video not found: {input_path}")
        
    try:
        print(f"Cutting video {input_path} from {start_time} to {end_time}...")
        (
            ffmpeg
            .input(input_path, ss=start_time, to=end_time)
            .output(output_path, c='copy') # copy codec is faster and lossless for cutting
            .run(overwrite_output=True, quiet=True)
        )
        print(f"Successfully created clip: {output_path}")
    except ffmpeg.Error as e:
        print(f"FFmpeg Error cutting video:")
        if e.stderr:
            print(e.stderr.decode('utf8'))
        raise e

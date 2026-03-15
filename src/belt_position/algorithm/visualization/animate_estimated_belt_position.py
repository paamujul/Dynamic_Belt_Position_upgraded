import imageio.v2 as imageio
from pathlib import Path
import belt_position.config.settings as cfg
from belt_position.services.logging_service import log
import time

def create_belt_position_animations(frames_folder : Path | str, output_folder : Path | str, fps=10):
    """
    Create both MP4 animations from saved frame images.
    
    This function reads all images named `frame_XXXX.png` in the `frames_folder`,
    compiles them in order, and writes a video file to `output_folder` using the
    H.264 codec.
    
    Args:
        frames_folder (str | Path): Folder containing input frame images.
        output_folder (str | Path): Folder where the output video will be saved.
        fps (int, optional): Frames per second for the output video. Defaults to 10.
    
    Raises:
        FileNotFoundError: If the input folder does not exist or contains no frames.
        Exception: If any other unexpected error occurs during reading or writing frames.
    
    Side Effects:
        - Writes an MP4 file to the output folder.
        - Logs progress and errors via the project logging system.    
    """
    try:
        frames_folder = Path(frames_folder)
        output_folder = Path(output_folder)
        
        # ---- Validate folders ----
        if not frames_folder.exists():
            raise FileNotFoundError(f"Frames folder does not exist: {frames_folder}")

        # Get all frames
        frame_files = sorted(frames_folder.glob("frame_*.png"))
        
        if not frame_files:
            raise FileNotFoundError(f"No frames found in {frames_folder}")
    
        # Read images
        images = [imageio.imread(f) for f in frame_files]
                
        # Create MP4
        output_mp4 = output_folder / f"{cfg.TEST_ID} Dynamic Belt Position Video.mp4"
        writer = None
        try:
            writer = imageio.get_writer(output_mp4, fps=fps, codec='libx264', quality=8)
            for img in images:
                writer.append_data(img)
        except Exception as e:
            log(f"Writing to video failed: {e}","Error")
            
        finally:
             if writer is not None:
                writer.close()

        log(f"Saved raw frame video in {frames_folder}")
        
    except Exception as e:
        log(f"Error in create_belt_position_animations: {e}","Error")
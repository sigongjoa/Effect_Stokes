
import cv2
import numpy as np
import sys
import os

def analyze_video(video_path):
    """
    Analyzes a video file to check if it is blank.

    Args:
        video_path (str): The absolute path to the video file.

    Returns:
        None. Prints the analysis result to the console.
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at '{video_path}'")
        return

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Error: Could not open video file '{video_path}'")
        return

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    print(f"--- Video Analysis Report ---")
    print(f"File: {os.path.basename(video_path)}")
    print(f"Resolution: {width}x{height}")
    print(f"Frame Rate (FPS): {fps:.2f}")
    print(f"Total Frames: {frame_count}")
    print("-" * 29)

    if frame_count == 0:
        print("Result: The video has 0 frames and is invalid.")
        cap.release()
        return

    # Check a few frames (e.g., 5 frames spread across the video)
    num_frames_to_check = min(frame_count, 5)
    frame_indices = np.linspace(0, frame_count - 1, num_frames_to_check, dtype=int)

    blank_frames = 0
    for i in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if ret:
            # A frame is considered "blank" if the standard deviation of its
            # pixel values is very low. 10 is a reasonable threshold for this.
            if frame.std() < 10:
                blank_frames += 1
        else:
            # Could not read frame, might be a corrupt file
            print(f"Warning: Could not read frame at index {i}.")


    print("--- Blank Frame Analysis ---")
    print(f"Checked {len(frame_indices)} frames at indices: {frame_indices.tolist()}")
    print(f"Found {blank_frames} blank frames.")
    print("-" * 29)


    if blank_frames == len(frame_indices):
        print("Result: The video appears to be BLANK or static.")
    else:
        print("Result: The video contains visible content.")

    cap.release()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_video.py <path_to_video_file>")
        sys.exit(1)

    video_file_path = sys.argv[1]
    analyze_video(video_file_path)

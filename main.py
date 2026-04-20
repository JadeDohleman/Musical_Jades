from src.gui import run_gui
import os
import sys

def main():
    # Path to ffmpeg (found on user's desktop)
    # Check if we are passing a CLI argument to run in headless mode if needed? 
    # For now, user asked for GUI, so default to GUI.
    
    ffmpeg_path = r"C:\Users\jmodo\Documents\ffmpeg\bin\ffmpeg.exe"
    if not os.path.exists(ffmpeg_path):
        print(f"Warning: ffmpeg not found at {ffmpeg_path}. MP3 export might fail.")
    
    print("Launching GUI...")
    run_gui(ffmpeg_path)

if __name__ == "__main__":
    main()

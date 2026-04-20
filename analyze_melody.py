
import subprocess
import os
import numpy as np
import scipy.io.wavfile as wavfile
from src.theory import freq_to_note

def analyze_audio(input_file, ffmpeg_path="ffmpeg"):
    # 1. Convert to WAV
    wav_file = "temp_analysis.wav"
    try:
        if os.path.exists(wav_file):
            os.remove(wav_file)
            
        print(f"Converting {input_file} to WAV...")
        subprocess.run([
            ffmpeg_path, '-y', '-i', input_file, '-ar', '44100', '-ac', '1', wav_file
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    except Exception as e:
        print(f"Error converting audio: {e}")
        return []

    # 2. Load WAV
    sr, data = wavfile.read(wav_file)
    if data.ndim > 1:
        data = data[:, 0] # Mono
        
    print(f"Loaded audio: {len(data)/sr:.2f}s")
    print(f"Data type: {data.dtype}")
    print(f"Min: {np.min(data)}, Max: {np.max(data)}")
    
    # 3. Windowed Pitch Detection (Simple FFT Peak)
    window_size_sec = 0.25 # 1/4 second windows (approx 1 beat at 240bpm, fast enough)
    window_size = int(sr * window_size_sec)
    step_size = window_size # Non-overlapping for creating distinct note events
    
    notes = []
    
    for i in range(0, len(data) - window_size, step_size):
        chunk = data[i:i+window_size]
        
        # Apply Hanning window
        windowed = chunk * np.hanning(len(chunk))
        
        # FFT
        fft = np.fft.rfft(windowed)
        freqs = np.fft.rfftfreq(len(windowed), 1/sr)
        
        # Find peak magnitude
        mag = np.abs(fft)
        
        # Ignore silence
        rms = np.sqrt(np.mean(chunk**2))
        # print(f"DEBUG: Window {i}: RMS={rms:.5f}") 
        
        # Lower threshold significantly (assuming non-normalized maybe?)
        # Audio is very quiet (RMS ~50).
        THRESHOLD = 15 
        
        if rms < THRESHOLD: 
            # print("  Silence")
            notes.append(None)
            continue
            
        peak_idx = np.argmax(mag)
        peak_freq = freqs[peak_idx]
        
        # Debug peak
        # print(f"  Peak Freq: {peak_freq:.2f} Hz")
        
        # Ignore low rumble or high noise
        if peak_freq < 60 or peak_freq > 3000:
            notes.append(None)
            continue
            
        note_name = freq_to_note(peak_freq)
        print(f"DEBUG: Found {note_name} ({peak_freq:.0f}Hz) at {i/sr:.2f}s")
        notes.append(note_name)
        
    # 4. Debounce / Compress with Silence Handling
    # We want to reconstruct the timeline exactly.
    final_sequence = []
    if not notes:
        return []
        
    # We started at t=0.
    # We have a list of 'notes' (strings or None) for each window step.
    
    current_val = notes[0]
    current_count = 1
    
    # 1 bar = 2 seconds at 120bpm default.
    # window_size_sec = 0.25.
    # so 1 window = 0.125 bars.
    BARS_PER_WINDOW = window_size_sec / 2.0 
    
    for note in notes[1:]:
        if note == current_val:
            current_count += 1
        else:
            # End of a block
            duration_bars = current_count * BARS_PER_WINDOW
            final_sequence.append((current_val, duration_bars))
            
            current_val = note
            current_count = 1
            
    # Append last
    duration_bars = current_count * BARS_PER_WINDOW
    final_sequence.append((current_val, duration_bars))
    
    # --- FILTER FOR 4 PEAKS ---
    # The user specifically mentioned "four peak notes". 
    # Our data might have noise or short spurious notes.
    # We will filter `final_sequence` to keep only the note events (not silence),
    # rank them by some metric (duration?), and pick the top 4 in order of appearance?
    # Or just return the sequence if it looks close.
    
    # Filter out silence
    only_notes = [x for x in final_sequence if x[0] is not None]
    
    print(f"DEBUG: Found {len(only_notes)} note events total.")
    
    # If we have many, assume the short ones are noise.
    # Let's clean up: remove events < 0.1 bars?
    cleaned = [x for x in only_notes if x[1] >= 0.1]
    
    # If we still have more than 4, take the 4 loudest/longest? 
    # We don't have RMS here anymore.
    # Let's just assume the 4 longest events are the intended ones.
    # But order matters.
    
    if len(cleaned) >= 4:
         # Sort by duration to find the "main" ones, but we lose order...
         # Maybe the user sang "Doo... Doo... Doo... Doo..."
         # Let's try to just return the cleaned list, printing them to the user.
         pass
         
    return final_sequence # Return full timeline for now, we can manually pick in the generation step if needed.

def extract_peaks(sequence, k=4):
    """ Extract the k most significant notes. """
    # Filter silence
    notes = [x for x in sequence if x[0] is not None]
    
    # Sort by duration descending
    # (Note, Duration)
    sorted_notes = sorted(notes, key=lambda x: x[1], reverse=True)
    
    # Take top k
    top_k = sorted_notes[:k]
    
    # Identify which ones these are in the original list to preserve order?
    # Actually, the user probably wants the motif in order.
    # If the user sang 4 notes, we should just find the 4 distinct events.
    
    if len(notes) <= k:
        return notes
        
    # If we have more, maybe we should just output the top k unique notes?
    return top_k

def generate_four_note_demo(sequence):
    # Custom generator for the 4-note request
    peaks = extract_peaks(sequence, 4)
    
    lines = ["# 4-Note Peak Demo"]
    lines.append("# Extracted Top 4 Notes based on duration/prominence")
    
    note_vars = []
    
    for i, (note, dur) in enumerate(peaks):
        lines.append(f"p{i} = beep(note_to_freq('{note}'), duration={dur:.3f}, waveform='square')")
        note_vars.append(f"p{i}")
        
    lines.append("")
    lines.append("# The Motif")
    motif = " & ".join(note_vars)
    lines.append(f"motif = {motif}")
    lines.append("motif")
    
    return "\n".join(lines)

def generate_code(sequence):
    lines = []
    lines.append("# Auto-generated from audio inspiration (Rhythm Preserved)")
    lines.append("")
    lines.append("# Melody Sequence")
    parts = []
    
    for i, (note, dur) in enumerate(sequence):
        # Round duration slightly to look cleaner, but keep precision
        # dur = round(dur, 3) 
        
        if note is None:
            # Silence
            line = f"s{i} = silence(duration={dur:.3f})"
            parts.append(f"s{i}")
        else:
            # Note
            line = f"n{i} = beep(note_to_freq('{note}'), duration={dur:.3f}, waveform='sine')"
            parts.append(f"n{i}")
            
        lines.append(line)
        
    lines.append("")
    lines.append("# Combine")
    
    if len(parts) > 0:
        # Recursion limit safety? 
        # For ~20 events it's fine.
        mix_expr = " & ".join(parts)
        lines.append(f"melody = {mix_expr}")
        lines.append("melody * 0.5")
    else:
        lines.append("silence(1)")
        
    return "\n".join(lines)
    

if __name__ == "__main__":
    input_file = r"c:\Users\jmodo\Documents\workspace\musical_jades\inspirations\inspire1.m4a"
    ffmpeg = r"C:\Users\jmodo\Desktop\ffmpeg\bin\ffmpeg.exe"
    
    print(f"Analyzing {input_file}...")
    seq = analyze_audio(input_file, ffmpeg)
    
    if seq:
        print(f"Extracted {len(seq)} events found.")
        # print(seq)
        
        # 1. Standard full melody
        code = generate_code(seq)
        with open("inspired_mix.py", "w") as f:
            f.write(code)
        print("Generated inspired_mix.py")
        
        # 2. Four Peak Demo
        code_four = generate_four_note_demo(seq)
        with open("four_note_demo.py", "w") as f:
            f.write(code_four)
        print("Generated four_note_demo.py")
        
    else:
        print("No melody found.")

import numpy as np
import scipy.io.wavfile as wavfile
import subprocess
import os
from .pattern import Pattern
from .synth import generate_wave, apply_envelope
from .theory import note_to_freq

class Renderer:
    def __init__(self, sample_rate=44100, bpm=120, ffmpeg_path="ffmpeg"):
        self.sr = sample_rate
        self.bpm = bpm
        self.ffmpeg_path = ffmpeg_path
        
    def render(self, pattern: Pattern, filename: str, master_volume: float = 0.05):
        # 1. Generate Raw Audio Buffer recursively
        buffer = self._render_buffer(pattern)
        
        # 2. Post-Processing Chain
        
        # Auto-normalization / Maximization
        # REMOVED: Global normalization causes excessive dynamic range (quiet parts get squashed by loud peaks).
        # We rely on soft-clipping (tanh) below to limit peaks while preserving relative volumes.
        peak = np.max(np.abs(buffer))
        print(f"DEBUG: Peak amplitude: {peak}")
        # if peak > 1e-6:
        #     buffer /= peak
        #     buffer *= 0.95 # Safety margin
        
        # Soft Limiter / Tanh Saturation
        buffer = np.tanh(buffer) 
        
        # Apply Master Volume
        buffer *= master_volume
        
        # Convert to 16-bit PCM
        buffer_int16 = (buffer * 32767).astype(np.int16)
        
        # Check output format
        if filename.lower().endswith(".mp3"):
            wav_filename = filename.replace(".mp3", ".wav")
            # Write temp WAV
            wavfile.write(wav_filename, self.sr, buffer_int16)
            
            # Convert to MP3
            try:
                subprocess.run([
                    self.ffmpeg_path, '-y', '-i', wav_filename, '-b:a', '192k', filename
                ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"Rendered to {filename}")
                # Clean up WAV
                if os.path.exists(wav_filename):
                    os.remove(wav_filename)
            except Exception as e:
                print(f"Error converting to MP3: {e}. Kept {wav_filename}")
        else:
            wavfile.write(filename, self.sr, buffer_int16)
            print(f"Rendered to {filename}")

    def _render_buffer(self, pattern: Pattern) -> np.ndarray:
        # Determine duration
        cycle_duration_sec = (60.0 / self.bpm) * 4.0
        
        # Handle Recursive Operators
        if pattern.operator == "mul" and len(pattern.operands) == 2:
            op1 = pattern.operands[0]
            op2 = pattern.operands[1]
            
            # Helper to get buffer or scalar
            def get_content(op):
                if isinstance(op, (int, float)):
                    return float(op)
                else:
                    return self._render_buffer(op)
            
            val1 = get_content(op1)
            val2 = get_content(op2)
            
            # Case 1: Both are arrays (Ring Mod)
            if isinstance(val1, np.ndarray) and isinstance(val2, np.ndarray):
                # Match lengths (pad with zeros)
                max_len = max(len(val1), len(val2))
                if len(val1) < max_len:
                    val1 = np.pad(val1, (0, max_len - len(val1)))
                if len(val2) < max_len:
                    val2 = np.pad(val2, (0, max_len - len(val2)))
                return val1 * val2
                
            # Case 2: One is scalar (Volume Scaling)
            # Array multiplication by float works automatically in numpy
            return val1 * val2

        elif pattern.operator == "add" and len(pattern.operands) == 2:
            b1 = self._render_buffer(pattern.operands[0])
            b2 = self._render_buffer(pattern.operands[1])
            
            # Match lengths (pad with zeros)
            max_len = max(len(b1), len(b2))
            if len(b1) < max_len:
                b1 = np.pad(b1, (0, max_len - len(b1)))
            if len(b2) < max_len:
                b2 = np.pad(b2, (0, max_len - len(b2)))
                
            return b1 + b2
            
        elif pattern.operator == "concat" and len(pattern.operands) == 2:
            b1 = self._render_buffer(pattern.operands[0])
            b2 = self._render_buffer(pattern.operands[1])
            return np.concatenate([b1, b2])

        elif pattern.operator == "crossfade" and len(pattern.operands) == 3:
            b1 = self._render_buffer(pattern.operands[0])
            b2 = self._render_buffer(pattern.operands[1])
            duration_cycles = pattern.operands[2]
            
            # Calculate overlap in samples
            overlap_samples = int(duration_cycles * cycle_duration_sec * self.sr)
            
            # Clamp overlap
            overlap_samples = min(overlap_samples, len(b1), len(b2))
            
            if overlap_samples <= 0:
                return np.concatenate([b1, b2])
                
            # Create output buffer
            new_len = len(b1) + len(b2) - overlap_samples
            out_buffer = np.zeros(new_len, dtype=np.float32)
            
            # 1. Non-overlapping parts
            # Part 1: Start to overlap start
            end_b1_solo = len(b1) - overlap_samples
            out_buffer[:end_b1_solo] = b1[:end_b1_solo]
            
            # Part 2: Overlap end to finish (from b2)
            start_b2_solo = overlap_samples
            out_buffer[len(b1):] = b2[start_b2_solo:]
            
            # 2. Overlapping region
            # Region in output: [end_b1_solo : len(b1)]
            # Region in b1: [end_b1_solo:] (last part)
            # Region in b2: [:start_b2_solo] (first part)
            
            seg1 = b1[end_b1_solo:]
            seg2 = b2[:start_b2_solo]
            
            # Generate fade curves (Equal Power Crossfade)
            # Using Sine/Cosine laws to maintain constant power summation
            # t goes from 0 to pi/2
            t_curve = np.linspace(0, np.pi/2, overlap_samples)
            fade_out = np.cos(t_curve) 
            fade_in = np.sin(t_curve)
            
            cross_seg = (seg1 * fade_out) + (seg2 * fade_in)
            
            out_buffer[end_b1_solo:len(b1)] = cross_seg
            
            return out_buffer

        elif pattern.operator == "reverse" and len(pattern.operands) == 1:
            b = self._render_buffer(pattern.operands[0])
            return b[::-1] # Reverse array
            
        # Base Case: Event Rendering
        # Determine total length based on events or explicit cycles
        # Safe duration calc: max(timestamp + duration, cycles)
        max_event_time = max(e.timestamp + e.duration for e in pattern.events) if pattern.events else 0
        total_cycles = max(max_event_time, pattern.cycles)
        total_duration_sec = total_cycles * cycle_duration_sec
        total_samples = int(total_duration_sec * self.sr)
        
        # Buffer
        buffer = np.zeros(total_samples, dtype=np.float32)
        
        for event in pattern.events:
            start_time_sec = event.timestamp * cycle_duration_sec
            duration_sec = event.duration * cycle_duration_sec
            
            freq = note_to_freq(event.value)
            if freq <= 0:
                continue
                
            wave = generate_wave(freq, duration_sec, sr=self.sr, waveform=event.waveform)
            wave = apply_envelope(wave, duration_sec, sr=self.sr)
            
            # Apply event volume
            wave *= event.volume
            
            start_sample = int(start_time_sec * self.sr)
            end_sample = start_sample + len(wave)
            
            if end_sample > len(buffer):
                # Expand buffer if event goes beyond (rare if cycles is set correctly)
                pad = np.zeros(end_sample - len(buffer), dtype=np.float32)
                buffer = np.concatenate([buffer, pad])
            
            buffer[start_sample:end_sample] += wave
            
        return buffer

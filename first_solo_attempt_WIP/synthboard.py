# Jupyter Notebook: Piano with a Phaser
# Creator: Jade Dohleman with help from ChatGPT.
# Created: 20250128.

# ============================================================================
# 1) OPTIONAL: INSTALL DEPENDENCIES
# ============================================================================
# First, ensure that you have a system version of Python3 installed and in 
# your PATH variable, otherwise the first line to install a virtual 
# will not run.
# 
# If you need a clean virtual environment, run this:
# 
# !python3 -m venv musicenv
# 
# This will create a new directory in your current directory with that name.
# Nestled in this directory is the environment's Python installation.
# Now, establish the environment in the jupyter kernel directory by running:
#
# !.\musicenv\Scripts\python.exe -m ipykernel install --name=musicenv
# 
# Now the virtual environment may be selected from the drop-down menu above, 
# under "Kernel". Please do so.
# 
# Install and upgrade pip:
# 
# !.\musicenv\Scripts\python.exe -m pip install --upgrade pip
#
# If you're in a clean environment, to install packages:
# 
# !.\musicenv\Scripts\pip.exe install pygame librosa soundfile numpy

import pygame
import sys
import time
import numpy as np
import soundfile as sf
import librosa
import math

# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------

BUTTON_SIZE = 50
BUTTON_GAP = 10
FONT_SIZE = 16

SAMPLE_RATE = 22050
AMPLITUDE = 0.3

# Short buffer length (seconds) for real-time playback loop
LOOP_BUFFER_DURATION = 0.5

# Phaser parameters
PHASER_LFO_RATE = 0.5      # Hz (frequency of the delay modulation)
PHASER_MAX_DELAY = 0.005   # seconds (maximum delay shift)
PHASER_FEEDBACK = 0.5      # how much of the delayed signal is fed back

# Define octaves/notes for an 88-key layout (A0..C8)
SEMITONES_FULL = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]
OCTAVES = []
for i in range(7):  # 0..6
    row_notes = [f"{note}{i}" for note in SEMITONES_FULL]
    OCTAVES.append(row_notes)
# partial row: A7, A#7, B7, C8
OCTAVES.append(["A7", "A#7", "B7", "C8"])

# Waveforms
WAVEFORMS = ["Sine", "Square", "Triangle", "Sawtooth"]

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------

def generate_violin_wave(note_name, duration, sr=22050, amplitude=0.3):
    """Generate a violin-like sound with a sawtooth+sine wave, vibrato, and ADSR envelope."""
    freq = librosa.note_to_hz(note_name)
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    # Sawtooth wave for harmonic richness
    sawtooth_wave = amplitude * (2.0 * (freq * t - np.floor(0.5 + freq * t)))

    # Sine wave to soften the tone
    sine_wave = amplitude * 0.3 * np.sin(2.0 * np.pi * freq * t)

    # Vibrato (modulate frequency slightly)
    vibrato_freq = 6.0  # Hz
    vibrato_depth = 0.002  # Pitch variation depth
    vibrato = np.sin(2.0 * np.pi * vibrato_freq * t) * vibrato_depth * freq

    # Apply vibrato effect to frequency
    violin_wave = (sawtooth_wave + sine_wave) * np.sin(2.0 * np.pi * (freq + vibrato) * t)

    # Apply ADSR envelope
    attack_time = 0.1  # seconds
    release_time = 0.3  # seconds
    envelope = np.ones_like(t)

    attack_samples = int(attack_time * sr)
    release_samples = int(release_time * sr)

    envelope[:attack_samples] = np.linspace(0, 1, attack_samples)  # Attack phase
    envelope[-release_samples:] = np.linspace(1, 0, release_samples)  # Release phase

    violin_wave *= envelope

    # Convert to int16 format for playback
    violin_wave_16bit = np.int16(violin_wave * 32767)
    return violin_wave_16bit

def generate_mono_wave(note_name, waveform, duration, sr=SAMPLE_RATE, amplitude=AMPLITUDE):
    """
    Generate a 1D NumPy array (int16) for a single note of a given waveform, no stereo processing yet.
    """
    freq = librosa.note_to_hz(note_name)
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    if waveform == "Sine":
        wave = amplitude * np.sin(2.0 * math.pi * freq * t)
    elif waveform == "Square":
        wave = amplitude * np.sign(np.sin(2.0 * math.pi * freq * t))
    elif waveform == "Triangle":
        wave = amplitude * (2.0 / math.pi) * np.arcsin(np.sin(2.0 * math.pi * freq * t))
    elif waveform == "Sawtooth":
        wave = amplitude * (2.0 * (freq * t - np.floor(0.5 + freq * t)))
    else:
        wave = amplitude * np.sin(2.0 * math.pi * freq * t)

    wave_16bit = np.int16(wave * 32767)
    return wave_16bit

def apply_basic_phaser_stereo(wave_mono, sr=SAMPLE_RATE):
    """
    Applies a simple stereo 'phaser' effect by modulating the right channel
    with a short delay and feedback. The left channel is the original (dry).
    """
    wave_float = wave_mono.astype(np.float32) / 32767.0
    num_samples = len(wave_float)

    # Prepare a float32 stereo array
    stereo_float = np.zeros((num_samples, 2), dtype=np.float32)

    # Left channel = original dry
    stereo_float[:, 0] = wave_float

    # We'll create a modulated delay line for the right channel
    delay_buffer = np.zeros(num_samples, dtype=np.float32)
    time_array = np.arange(num_samples) / sr

    for i in range(num_samples):
        # LFO-based delay time in seconds
        current_delay = PHASER_MAX_DELAY * 0.5 * (1 + math.sin(2.0 * math.pi * PHASER_LFO_RATE * time_array[i]))
        delay_samples = int(current_delay * sr)

        dry_signal = wave_float[i]
        if i - delay_samples >= 0:
            wet_signal = delay_buffer[i - delay_samples] * PHASER_FEEDBACK
        else:
            wet_signal = 0.0

        right_val = dry_signal + wet_signal
        delay_buffer[i] = right_val
        stereo_float[i, 1] = right_val

    # Normalize if needed
    max_val = np.max(np.abs(stereo_float))
    if max_val > 1.0:
        stereo_float /= max_val

    # Convert back to int16
    stereo_16bit = np.int16(stereo_float * 32767)
    return stereo_16bit

def make_stereo_buffer(wave_mono, phaser_on):
    """
    Given a 1D mono int16 array, either duplicate it into both channels (phaser_off)
    or apply a basic phaser effect for stereo.
    """
    if not phaser_on:
        wave_mono = wave_mono.reshape(-1)  # ensure 1D
        stereo_16bit = np.column_stack((wave_mono, wave_mono))
    else:
        stereo_16bit = apply_basic_phaser_stereo(wave_mono)
    return stereo_16bit

def create_pygame_sound(stereo_16bit):
    """
    Convert a (num_samples, 2) stereo int16 NumPy array into a pygame Sound object.
    """
    return pygame.sndarray.make_sound(stereo_16bit)

def generate_and_save_full_press(note_name, waveform, duration, sr=SAMPLE_RATE, amplitude=AMPLITUDE):
    """
    Generate the final wave for the full press duration and save to .wav.
    By default, no phaser is applied to the saved file, but you could adapt if desired.
    """
    wave_16bit = generate_mono_wave(note_name, waveform, duration, sr, amplitude)
    filename = f".\\audio_out\\{note_name}_{waveform}_{int(time.time()*1000)}.wav"
    # Convert to float32 for writing
    wave_float = wave_16bit.astype(np.float32) / 32767.0
    sf.write(filename, wave_float, sr)
    print(f"Saved {note_name} waveform={waveform}, duration={duration:.2f}s to {filename}")

def main():
    pygame.init()
    # Init mixer for 2-channel stereo
    pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2)

    # ----------------------------
    # Layout / Window Setup
    # ----------------------------
    BUTTON_SIZE = 50
    BUTTON_GAP = 10
    FONT_SIZE = 16

    num_rows = len(OCTAVES)
    num_cols = max(len(row) for row in OCTAVES)

    piano_width = num_cols * (BUTTON_SIZE + BUTTON_GAP) + BUTTON_GAP
    piano_height = num_rows * (BUTTON_SIZE + BUTTON_GAP) + BUTTON_GAP

    WAVEFORM_BUTTON_WIDTH = 120
    WAVEFORM_BUTTON_HEIGHT = 40
    WAVEFORM_BUTTON_GAP = 10

    # We add a 5th button for Phaser toggle
    waveform_area_width = WAVEFORM_BUTTON_WIDTH + 2 * WAVEFORM_BUTTON_GAP
    waveform_area_height = 5 * (WAVEFORM_BUTTON_HEIGHT + WAVEFORM_BUTTON_GAP) + WAVEFORM_BUTTON_GAP

    window_width = piano_width + waveform_area_width
    window_height = max(piano_height, waveform_area_height)
    screen = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("Real-Time Piano with Phaser")

    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, FONT_SIZE)

    # Piano key circles
    radius = BUTTON_SIZE // 2
    buttons = []
    for i, row_notes in enumerate(OCTAVES):
        for j, note_name in enumerate(row_notes):
            x = BUTTON_GAP + j * (BUTTON_SIZE + BUTTON_GAP)
            y = BUTTON_GAP + i * (BUTTON_SIZE + BUTTON_GAP)
            cx, cy = x + radius, y + radius
            buttons.append({"center": (cx, cy), "note": note_name})

    # Waveform buttons
    waveform_buttons = []
    for idx, wf in enumerate(WAVEFORMS):
        x = piano_width + WAVEFORM_BUTTON_GAP
        y = WAVEFORM_BUTTON_GAP + idx * (WAVEFORM_BUTTON_HEIGHT + WAVEFORM_BUTTON_GAP)
        rect = pygame.Rect(x, y, WAVEFORM_BUTTON_WIDTH, WAVEFORM_BUTTON_HEIGHT)
        waveform_buttons.append({"rect": rect, "waveform": wf})

    # Phaser toggle button
    phaser_button_rect = pygame.Rect(
        piano_width + WAVEFORM_BUTTON_GAP,
        WAVEFORM_BUTTON_GAP + len(WAVEFORMS) * (WAVEFORM_BUTTON_HEIGHT + WAVEFORM_BUTTON_GAP),
        WAVEFORM_BUTTON_WIDTH,
        WAVEFORM_BUTTON_HEIGHT
    )

    selected_waveform = "Sine"
    phaser_on = False

    # Track pressed key
    pressed_button = None
    press_start_time = 0.0
    currently_playing_sound = None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()

                # Check phaser button
                if phaser_button_rect.collidepoint(mouse_pos):
                    phaser_on = not phaser_on
                    print(f"Phaser toggled to {phaser_on}")
                    continue

                # Check waveform buttons
                for wb in waveform_buttons:
                    if wb["rect"].collidepoint(mouse_pos):
                        selected_waveform = wb["waveform"]
                        print(f"Selected waveform: {selected_waveform}")
                        break
                else:
                    # Check piano keys
                    if pressed_button is None:
                        for btn in buttons:
                            cx, cy = btn["center"]
                            dist_sq = (mouse_pos[0] - cx)**2 + (mouse_pos[1] - cy)**2
                            if dist_sq <= radius**2:
                                pressed_button = btn
                                press_start_time = time.time()

                                # Generate short wave buffer for real-time loop
                                wave_mono = generate_mono_wave(btn["note"], selected_waveform, LOOP_BUFFER_DURATION)
                                stereo_16bit = make_stereo_buffer(wave_mono, phaser_on)
                                sound_obj = create_pygame_sound(stereo_16bit)
                                sound_obj.play(loops=-1)  # loop indefinitely
                                currently_playing_sound = sound_obj

                                print(f"Pressed note: {btn['note']}, phaser={phaser_on}")
                                break

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # Stop real-time sound, save final wave
                if pressed_button is not None:
                    press_duration = time.time() - press_start_time
                    note_name = pressed_button["note"]

                    if currently_playing_sound:
                        currently_playing_sound.stop()

                    if press_duration > 0.01:
                        # Save final wave (no phaser by default)
                        generate_and_save_full_press(note_name, selected_waveform, press_duration)

                    pressed_button = None
                    currently_playing_sound = None

        # Drawing
        screen.fill((0, 0, 0))

        # Piano
        for btn in buttons:
            cx, cy = btn["center"]
            if btn == pressed_button:
                color = (200, 200, 200)
            else:
                color = (255, 255, 255)
            pygame.draw.circle(screen, color, (cx, cy), radius)
            label_surf = font.render(btn["note"], True, (0, 0, 0))
            label_rect = label_surf.get_rect(center=(cx, cy))
            screen.blit(label_surf, label_rect)

        # Waveform buttons
        waveform_font = pygame.font.SysFont(None, 20)
        for wb in waveform_buttons:
            rect = wb["rect"]
            wf = wb["waveform"]
            if wf == selected_waveform:
                pygame.draw.rect(screen, (255, 255, 0), rect)  # highlight
            else:
                pygame.draw.rect(screen, (180, 180, 180), rect)
            label = waveform_font.render(wf, True, (0, 0, 0))
            label_rect = label.get_rect(center=rect.center)
            screen.blit(label, label_rect)

        # Phaser toggle button
        phaser_color = (0, 255, 0) if phaser_on else (128, 128, 128)
        pygame.draw.rect(screen, phaser_color, phaser_button_rect)
        phaser_label = waveform_font.render("Phaser", True, (0, 0, 0))
        phaser_label_rect = phaser_label.get_rect(center=phaser_button_rect.center)
        screen.blit(phaser_label, phaser_label_rect)

        pygame.display.flip()
        clock.tick(60)

    pygame.mixer.quit()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
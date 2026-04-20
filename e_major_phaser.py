# E Major Cusp Mix
# Features:
# - Existing E Major Chord Progression + Phaser
# - Rhythm Layer
# - NEW: Cusp Crescendo Layer (Rising Tension)

# 1. Define Frequencies (E Major Scale)
E3, Gs3, B3 = 164.81, 207.65, 246.94
Cs3 = 138.59
A3, Cs4, E4 = 220.00, 277.18, 329.63
Ds4, Fs4 = 311.13, 369.99

# 2. Build Chords (2 Bars each)
chord_E  = beep(E3,  duration=2) + beep(Gs3, duration=2) + beep(B3, duration=2)
chord_Cm = beep(Cs3, duration=2) + beep(E3,  duration=2) + beep(Gs3, duration=2)
chord_A  = beep(A3,  duration=2) + beep(Cs4, duration=2) + beep(E4, duration=2)
chord_B  = beep(B3,  duration=2) + beep(Ds4, duration=2) + beep(Fs4, duration=2)
pad = chord_E & chord_Cm & chord_A & chord_B

# 3. Apply Fast Phaser
lfo = beep(4, duration=8, waveform="sine")
phased_pad = pad * lfo

# 4. Rapid Fire Rhythm
rhythm = elastic_beeps(start_density=4, peak_density=16, end_density=4, bars=8, note_freq=82.41)

# 5. Cusp Crescendo (rising tension)
# Spans the whole 8 bars (or maybe the last 4 for a buildup?)
# Let's do a slow rise over the full 8 bars using E4 (root octave up)
cusp_layer = cusp_crescendo(freq=E4, duration=8, n_events=64, power=5, waveform="triangle")

# 6. Mix
# Combine all layers
final_mix = phased_pad + rhythm + cusp_layer

final_mix

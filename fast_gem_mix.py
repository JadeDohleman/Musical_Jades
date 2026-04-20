# Fast Driving Mix (G / Em / C)
# Simulated 150 BPM feel by using short durations at 120 BPM

# 1. Driving Bass (E Minor Focus)
# -------------------------------
# 1/8th note pulses (0.125 duration at 120 BPM is technically 1/16th at 60, 
# but effectively fast at 120).
bass_note_e = beep(note_to_freq("E2"), duration=0.25, waveform="sawtooth") * 0.6
bass_note_g = beep(note_to_freq("G2"), duration=0.25, waveform="sawtooth") * 0.6
bass_note_c = beep(note_to_freq("C2"), duration=0.25, waveform="sawtooth") * 0.6

# 4 bars of driving bass: | E E E E | G G G G | E E E E | C C G G |
bass_line = (bass_note_e & bass_note_e & bass_note_e & bass_note_e &
             bass_note_g & bass_note_g & bass_note_g & bass_note_g &
             bass_note_e & bass_note_e & bass_note_e & bass_note_e &
             bass_note_c & bass_note_c & bass_note_g & bass_note_g)

# 2. Fast Arpeggios (G Major / E Minor sharing notes)
# ---------------------------------------------------
# G (G B D), Em (E G B), C (C E G)
# We'll make a sparkly high pattern
arp_g = (beep(note_to_freq("G4"), 0.125, "sine") & 
         beep(note_to_freq("B4"), 0.125, "sine") & 
         beep(note_to_freq("D5"), 0.125, "sine") & 
         beep(note_to_freq("B4"), 0.125, "sine")) * 0.4

arp_e = (beep(note_to_freq("E4"), 0.125, "sine") & 
         beep(note_to_freq("G4"), 0.125, "sine") & 
         beep(note_to_freq("B4"), 0.125, "sine") & 
         beep(note_to_freq("G4"), 0.125, "sine")) * 0.4

# Repeat them to fill space
arpeggios = (arp_e & arp_e & arp_g & arp_g & arp_e & arp_e & arp_g & arp_g)

# 3. Chords (Pads)
# ----------------
# Em -> G -> Em -> C
pad_em = chord("E3", "minor", duration=1, waveform="triangle") * 0.3
pad_g  = chord("G3", "major", duration=1, waveform="triangle") * 0.3
pad_c  = chord("C3", "major", duration=1, waveform="triangle") * 0.3

pads = pad_em & pad_g & pad_em & pad_c

# 4. Drums
# --------
# High energy
kick = elastic_beeps(start_density=4, peak_density=4, end_density=4, bars=4, note_freq=60, waveform="square") * 0.4
# Hi-hats using high freq noise/sine
hats = elastic_beeps(start_density=8, peak_density=12, end_density=8, bars=4, note_freq=8000, waveform="sine") * 0.1

drums = kick + hats

# 5. Assembly
# -----------

# Intro: Arps + Pads (building up)
intro = crossfade(pads, (pads + arpeggios), duration=1)

# Drop: Full Mix
full = (bass_line + arpeggios + pads + drums)

# Breakdown: Reverse the Arps
breakdown = arpeggios.reverse() + (pad_c * 0.8)

# Outro: Cusp Rise into final hit
riser = cusp_crescendo(note_to_freq("G5"), duration=2, n_events=32, power=4) * 0.5
final_hit = chord("G2", "major", duration=2, waveform="sawtooth") * 0.5

# Master Mix
# Intro (4 bars) -> Drop (4 bars) -> Breakdown (4 bars) -> Riser (2) -> Hit (2)
mix = intro & full & breakdown & (riser + (bass_line * 0.5)) & final_hit

mix

# Inspired Fast Mix (B Minor / D Major adaptation)
# Combining the "doo doo doo" extracted melody with the "Fast G/Em" style.
# RHYTHM UPDATE: Using precise timing extracted from audio analysis.

# 1. Lead Melody (The "Indie Vocals" inspiration)
# -----------------------------------------------
lead_wave = "square"

# Auto-generated sequence from audio (Timings preserved)
# Note: Frequencies are exact from FFT, waveforms changed to 'square' for lead style.
s0 = silence(duration=0.375)
n1 = beep(note_to_freq('E5'), duration=0.250, waveform=lead_wave)
n2 = beep(note_to_freq('C#3'), duration=0.125, waveform=lead_wave)
s3 = silence(duration=0.250)
n4 = beep(note_to_freq('F#5'), duration=0.125, waveform=lead_wave)
n5 = beep(note_to_freq('D5'), duration=0.125, waveform=lead_wave)
n6 = beep(note_to_freq('B2'), duration=0.125, waveform=lead_wave)
n7 = beep(note_to_freq('E6'), duration=0.125, waveform=lead_wave)
n8 = beep(note_to_freq('E5'), duration=0.250, waveform=lead_wave)
n9 = beep(note_to_freq('C#5'), duration=0.125, waveform=lead_wave)
n10 = beep(note_to_freq('A2'), duration=0.125, waveform=lead_wave)
s11 = silence(duration=0.375)

# Combine into one pattern
melody_raw = s0 & n1 & n2 & s3 & n4 & n5 & n6 & n7 & n8 & n9 & n10 & s11
lead_riff = melody_raw * 0.4

# 2. Driving Bass (B Minor to match melody's F# and C#)
# -----------------------------------------------------
# Bass Line: 1/8th notes
def make_bass_bar(note):
    b = beep(note_to_freq(note), 0.25, "sawtooth") * 0.6
    return b & b & b & b

bass_b = make_bass_bar("B2")
bass_g = make_bass_bar("G2")
bass_d = make_bass_bar("D3")
bass_a = make_bass_bar("A2")

bass_line = (bass_b & bass_b & bass_g & bass_g & bass_d & bass_d & bass_a & bass_a)

# 3. Arpeggios (Sparkle)
# ----------------------
arp_wave = "sine"
arp_dur = 0.125

arp_bm = (beep(note_to_freq("B4"), arp_dur, arp_wave) & beep(note_to_freq("D5"), arp_dur, arp_wave) & beep(note_to_freq("F#5"), arp_dur, arp_wave) & beep(note_to_freq("D5"), arp_dur, arp_wave))
arp_g  = (beep(note_to_freq("G4"), arp_dur, arp_wave) & beep(note_to_freq("B4"), arp_dur, arp_wave) & beep(note_to_freq("D5"), arp_dur, arp_wave) & beep(note_to_freq("B4"), arp_dur, arp_wave))
arp_d  = (beep(note_to_freq("D5"), arp_dur, arp_wave) & beep(note_to_freq("F#5"), arp_dur, arp_wave) & beep(note_to_freq("A5"), arp_dur, arp_wave) & beep(note_to_freq("F#5"), arp_dur, arp_wave))
arp_a  = (beep(note_to_freq("A4"), arp_dur, arp_wave) & beep(note_to_freq("C#5"), arp_dur, arp_wave) & beep(note_to_freq("E5"), arp_dur, arp_wave) & beep(note_to_freq("C#5"), arp_dur, arp_wave))

arpeggios = (arp_bm & arp_bm & arp_g & arp_g & arp_d & arp_d & arp_a & arp_a) * 0.4

# 4. Drums (High Energy)
# ----------------------
kick = elastic_beeps(4, 4, 4, 4, 60, "square") * 0.5
hats = elastic_beeps(8, 16, 8, 4, 8000, "sine") * 0.15
drums = kick + hats

# 5. Assembly
# -----------
# Since the melody length is determined by the audio file (approx 2 bars?), 
# we might need to loop it or just let the backing run.
# The melody is approx 2.5 seconds + gaps. 
# 120BPM -> 2 bars = 4 seconds.
# Let's loop the melody twice to fit the 4-bar progression?
lead_loop = lead_riff & lead_riff

intro = (bass_line + (lead_loop * 0.5)).reverse() 
full = (bass_line + arpeggios + drums + lead_loop)

# Breakdown: Just Melody + Pads
pad_bm = chord("B3", "minor", 1, "triangle")
pad_g = chord("G3", "major", 1, "triangle")
pad_d = chord("D3", "major", 1, "triangle")
pad_a = chord("A3", "major", 1, "triangle")
pads = (pad_bm & pad_g & pad_d & pad_a) * 0.3

breakdown = crossfade(full, (pads + lead_loop), duration=1)
outro = (pads * 0.5)

# Master Mix
total_mix = intro & full & full & breakdown & outro

total_mix

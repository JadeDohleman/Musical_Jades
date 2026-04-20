# Bass EDM Mix
# Style: Bass House / Mid-Tempo
# Motif: E5, E5, C#3, F#5 (from user audio)
# Key: F# Minor

# 1. The Hook (Gritty Lead)
# -------------------------
# We'll layer the motif: One Sawtooth (Bright) + One Square (Hollow)
# Motif Durations: 0.25, 0.25, 0.125, 0.125 (Total 0.75)
# We need to loop this to fill a bar or make a rhythm.
# Let's repeat it: [Motif] [Rest] [Motif] [Rest]

# 1. The Hook (Complexified)
# ---------------------------
# We'll create a 4-bar phrase:
# Bar 1: Original Motif
# Bar 2: Variation A (Rhythmic stutter)
# Bar 3: Original Motif
# Bar 4: Variation B (Octave / Pitch shift)

def make_complex_lead(wave, vol):
    # Bar 1: Original F#m Motif (E - E - C# - F#)
    b1_n1 = beep(note_to_freq("E5"), 0.25, wave)
    b1_n2 = beep(note_to_freq("E5"), 0.25, wave)
    b1_n3 = beep(note_to_freq("C#3"), 0.125, wave)
    b1_n4 = beep(note_to_freq("F#5"), 0.125, wave)
    bar1 = b1_n1 & b1_n2 & b1_n3 & b1_n4 & silence(0.25)
    
    # Bar 2: Stutter Variation (E - E E - C# - F# F#)
    # E5 (0.25)
    b2_n1 = beep(note_to_freq("E5"), 0.25, wave)
    # E5 (0.125) x 2
    b2_n2 = beep(note_to_freq("E5"), 0.125, wave)
    b2_stutter = b2_n2 & b2_n2
    # C#3 (0.125)
    b2_n3 = beep(note_to_freq("C#3"), 0.125, wave)
    # F#5 (0.0625) x 2 -> Fast trill end
    b2_n4 = beep(note_to_freq("F#5"), 0.0625, wave)
    b2_trill = b2_n4 & b2_n4
    # Fill rest of bar (Total so far: 0.25 + 0.25 + 0.125 + 0.125 = 0.75)
    bar2 = b2_n1 & b2_stutter & b2_n3 & b2_trill & silence(0.25)
    
    # Bar 3: Original
    bar3 = bar1
    
    # Bar 4: Pitch Variation (Go high)
    # E6 !
    b4_n1 = beep(note_to_freq("E6"), 0.25, wave)
    b4_n2 = beep(note_to_freq("E5"), 0.25, wave)
    b4_n3 = beep(note_to_freq("C#4"), 0.125, wave) # Up octave
    b4_n4 = beep(note_to_freq("F#6"), 0.375, wave) # Long release
    bar4 = b4_n1 & b4_n2 & b4_n3 & b4_n4 
    
    phrase = (bar1 & bar2 & bar3 & bar4) * vol
    return phrase

lead_saw = make_complex_lead("sawtooth", 0.4)
lead_sq  = make_complex_lead("square", 0.4)

lead_loop = lead_saw + lead_sq # Layered 4-bar phrase

# 2. The DROP Bass (4-Bar Loop)
# -------------------------------
bass_freq = note_to_freq("F#1")
bass_hit = beep(bass_freq, 0.25, "sawtooth")
bass_hit_short = beep(bass_freq, 0.125, "sawtooth")
# 1 Bar
bass_bar_1 = (bass_hit & bass_hit & bass_hit & bass_hit) * 0.8
# 4 Bar Loop
driving_bass = bass_bar_1 & bass_bar_1 & bass_bar_1 & bass_bar_1 

# Wobble Bass (1 Bar)
wobble_bit = beep(bass_freq, 0.0625, "triangle") 
wobble_beat = wobble_bit & wobble_bit & wobble_bit & wobble_bit
wobble_bar_1 = wobble_beat & wobble_beat & wobble_beat & wobble_beat 
# 4 Bar Loop
wobble_bar = wobble_bar_1 & wobble_bar_1 & wobble_bar_1 & wobble_bar_1

# 3. Drums (4-Bar Loop)
# ---------------------
kick = beep(60, 0.25, "square") * 1.0 
four_floor = kick & kick & kick & kick 
snare_hit = beep(200, 0.25, "noise") * 0.6
snare_line = silence(0.25) & snare_hit & silence(0.25) & snare_hit
drums_1 = four_floor + snare_line

hat = beep(8000, 0.125, "sine") * 0.2
off_hat = silence(0.125) & hat
hats_line_1 = off_hat & off_hat & off_hat & off_hat & off_hat & off_hat & off_hat & off_hat
full_drums_1 = drums_1 + hats_line_1
# 4 Bar Loop
full_drums = full_drums_1 & full_drums_1 & full_drums_1 & full_drums_1

# 3b. Atmospherics (4-Bar Loop)
# -----------------------------
pad_notes = ["F#3", "A3", "C#4", "E4"] 
pad_layer_1 = (beep(note_to_freq(pad_notes[0]), 1, "sawtooth") + 
               beep(note_to_freq(pad_notes[1]), 1, "sawtooth") + 
               beep(note_to_freq(pad_notes[2]), 1, "sawtooth") + 
               beep(note_to_freq(pad_notes[3]), 1, "sawtooth")) * 0.15
# 4 Bar Loop
pad_layer = pad_layer_1 & pad_layer_1 & pad_layer_1 & pad_layer_1

noise_floor_1 = beep(1000, 1, "noise") * 0.05
# 4 Bar Loop
noise_floor = noise_floor_1 & noise_floor_1 & noise_floor_1 & noise_floor_1

# 4. Assembly
# -----------
# Intro: 4 bars of lead + pads fade in
intro_pad = crossfade(silence(4), pad_layer, 2) 
build = (lead_loop * 0.8) + pad_layer

# Pre-Drop: Cusp Riser (2 Bars only)
riser = cusp_crescendo(note_to_freq("F#4"), 2, 64, 4) * 0.5
pre_drop = riser + (noise_floor_1 & noise_floor_1) # 2 bars noise

# DROP: 4 Bars
drop_section = driving_bass + full_drums + lead_loop + pad_layer + noise_floor

# Breakdown: Wobble (4 Bars)
wobble_section = wobble_bar + (lead_loop * 0.5) + (pad_layer * 0.5)

# Outro (4 Bars)
outro = (lead_loop * 0.5) + (pad_layer * 0.5)

# Structure
# Build (4) -> Pre (2) -> Drop (4) -> Wobble (4) -> Outro (4)
mix = build & pre_drop & drop_section & wobble_section & outro

mix

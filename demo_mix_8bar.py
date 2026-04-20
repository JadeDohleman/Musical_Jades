# 8-Bar Demo Mix
# Features:
# - Chord helper (Am - G - F - E progression)
# - Cusp Crescendo (Building tension layers)
# - Reverse Operator (Transition FX)
# - Elastic Rhythm

# 1. Chords (4 Bars, repeated = 8 Bars)
# Progression: Am -> G -> F -> E (Andalusian-ish descent)
# Duration: 4 beats (1 bar) each
am_chord = chord("A4", "minor", duration=4)
g_chord  = chord("G4", "major", duration=4)
f_chord  = chord("F4", "major", duration=4)
e_chord  = chord("E4", "major", duration=4)

# Combine into 4-bar sequence
progression = am_chord & g_chord & f_chord & e_chord
# Repeat for 8 bars total
full_progression = progression & progression

# 2. Bass Line (Simple root notes)
# A2 -> G2 -> F2 -> E2
bass = (beep(note_to_freq("A2"), duration=4, waveform="triangle") &
        beep(note_to_freq("G2"), duration=4, waveform="triangle") &
        beep(note_to_freq("F2"), duration=4, waveform="triangle") &
        beep(note_to_freq("E2"), duration=4, waveform="triangle"))
full_bass = (bass & bass) * 0.6 # Lower volume slightly

# 3. Rhythm (Elastic Beeps)
# 8 bars of rhythm
drums = elastic_beeps(start_density=2, peak_density=8, end_density=4, bars=8, note_freq=55, waveform="sawtooth")
drums = drums * 0.5

# 4. FX Layer 1: Cusp Crescendo
# Rising tension over the second half (Bars 5-8 = 16 beats length? No, duration is cycles)
# Let's run it over the last 4 bars (duration=16 if 1 bar=4 cycles? Standard seems to be duration=4 in e_major_phaser for 8 bars? 
# Wait, e_major_phaser uses duration=2 for chords. 2 cycles * 4 chords = 8 cycles total.
# So 8 bars approx = 8 cycles if 1 cycle = 1 bar?
# e_major_phaser: chords duration=2. total = 2+2+2+2 = 8.
# elastic_beeps(bars=8).
# So 1 cycle = 1 bar seems to be the convention there. 
# My chords above use duration=4?? That would be 16 bars total.
# Let's adjust chords to duration=2 (matches e_major) or duration=1 (matches beep default 0.1s?? No).
# e_major: beep(E3, duration=2). 
# Let's stick to duration=2 per chord => 8 cycle progression. 
# Double it => 16 cycles (16 bars?)
# User asked for "8 measures". 
# If 1 measure = 1 cycle (simplified):
# Let's do 1 bar = 1 cycle.
# So chords duration=1. 
# 4 chords = 4 bars.
# Repeat = 8 bars.

# RE-DEFINING durations for exactly 8 bars total
am_chord = chord("A3", "minor", duration=1) # Lower octave for pad
g_chord  = chord("G3", "major", duration=1)
f_chord  = chord("F3", "major", duration=1)
e_chord  = chord("E3", "major", duration=1)
progression = am_chord & g_chord & f_chord & e_chord # 4 bars
full_progression = progression & progression # 8 bars total

bass = (beep(note_to_freq("A2"), duration=1, waveform="triangle") &
        beep(note_to_freq("G2"), duration=1, waveform="triangle") &
        beep(note_to_freq("F2"), duration=1, waveform="triangle") &
        beep(note_to_freq("E2"), duration=1, waveform="triangle"))
full_bass = bass & bass

drums = elastic_beeps(start_density=4, peak_density=8, end_density=4, bars=8, note_freq=55, waveform="sawtooth") * 0.4

# 5. FX Layer 2: Reverse Transitions
# A reversed cymbal-like sound at bar 4 and bar 8
# Create a noise burst or high pitch beep, decay it, then reverse it for "suck" effect.
# We'll make a 1-bar pattern that has the reverse sound at the end?
# Or just a reverse beep.
rise = beep(note_to_freq("A5"), duration=1, waveform="sawtooth") 
# Apply envelope automatically happens in beep? No, beep is constant volume usually.
# We need decay. echo_pattern has decay.
# Let's use echo_pattern(repeats=1) to get a decaying note? 
# Or cusp_crescendo reversed?
# A reversed cusp crescendo is a decrescendo!
# Let's use `cusp_crescendo` for a riser in bars 7-8.
riser = cusp_crescendo(freq=note_to_freq("A4"), duration=2, n_events=32, power=3, waveform="sine")
# We want this at the END (last 2 bars).
# Pad with silence for first 6 bars.
pre_silence = silence(duration=6)
fx_layer = pre_silence & riser

# 6. Reverse Fill
# Let's add a reverse sound at bar 4.
# A simple varied beep reversed.
rev_sound = beep(880, duration=0.5).reverse()
# Place it at 3.5?
# Construct specific timeline:
# Silence(3.5) + rev_sound (0.5) + Silence(4.0)
rev_layer = silence(duration=3.5) & rev_sound & silence(duration=4.0)

# 7. Master Mix
mix = full_progression + full_bass + drums + fx_layer + rev_layer
mix

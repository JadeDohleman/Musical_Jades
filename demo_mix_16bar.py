# 16-Bar Feature Showcase
# Progression: Em - C - G - D (1 Bar each)
# Total: 4 sections of 4 bars

# 1. Setup Patterns
# -----------------

# Basic Chords (Duration=1 is 1 measure/4 beats)
# Using 'square' wave for a retro synth sound
# Chords have 3 voices, so inherent gain is ~3.0. Scaling down significantly.
chords_clean = (chord("E3", "minor", duration=1, waveform="square") & 
                chord("C3", "major", duration=1, waveform="square") & 
                chord("G3", "major", duration=1, waveform="square") & 
                chord("D3", "major", duration=1, waveform="square")) * 0.15

# Bass Line
bass = (beep(note_to_freq("E2"), duration=1, waveform="triangle") &
        beep(note_to_freq("C2"), duration=1, waveform="triangle") &
        beep(note_to_freq("G2"), duration=1, waveform="triangle") &
        beep(note_to_freq("D2"), duration=1, waveform="triangle")) * 0.3

# Drums (4 bars)
drums = elastic_beeps(start_density=4, peak_density=8, end_density=4, bars=4, note_freq=50, waveform="sawtooth") * 0.25


# 2. SECTION 1: INTRO (Bars 1-4)
# ------------------------------
# Feature: VOLUME MULTIPLICATION 
# Quieter version of chords + bass
intro = (chords_clean * 0.8) + (bass * 0.8)


# 3. SECTION 2: MAIN GROOVE (Bars 5-8)
# ------------------------------------
# A bit louder, add drums
main_groove = chords_clean + bass + drums


# 4. SECTION 3: REVERSE WORLD (Bars 9-12)
# ---------------------------------------
# Feature: REVERSE OPERATOR prominent usage!
# We reverse the entire chord progression audio.
rev_chords = chords_clean.reverse()

# Add a reversed melody snippet
melody = (beep(note_to_freq("B4"), duration=1) & 
          beep(note_to_freq("G4"), duration=1) & 
          beep(note_to_freq("E4"), duration=2))
rev_melody = melody.reverse() * 0.2

# Sparse reversed drums (density 2)
rev_drums = elastic_beeps(start_density=2, peak_density=4, end_density=2, bars=4, note_freq=100).reverse() * 0.2

# Combine reversed elements
reverse_section = rev_chords + rev_melody + rev_drums


# 5. SECTION 4: THE CLIMAX (Bars 13-16)
# -------------------------------------
# Feature: CUSP CRESCENDO prominent usage!
# A massive riser spanning 4 bars to end the track.
riser = cusp_crescendo(freq=note_to_freq("E5"), duration=4, n_events=64, power=6, waveform="sawtooth") * 0.5

# Full chords + Double Bass + Busy Drums
# Increased volume for climax, but kept within reasonable limits
final_section = (chords_clean * 1.2) + (bass * 1.1) + (drums * 1.2) + riser


# 6. MASTER COMPOSITION
# ---------------------
# Feature: CROSSFADE TRANSITIONS
# Smoothly blend sections together with 1-bar overlap
part1 = crossfade(intro, main_groove, duration=1)
part2 = crossfade(part1, reverse_section, duration=1)
mix = crossfade(part2, final_section, duration=1)

mix

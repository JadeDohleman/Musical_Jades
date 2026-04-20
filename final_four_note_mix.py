# Final Mix based on 4 Peak Notes from Inspiration
# Motif: E5, E5, C#3, F#5
# Key: F# Minor / A Major
# Style: Atmospheric Trap / Cloud Rap

# 1. The Motif (The "Peaks")
# --------------------------
# We will treat these as the main hook.
# E5 (High) -> E5 -> C#3 (Low Bass hit?) -> F#5 (Resolution)
# Actually C#3 is low enough to be a counter-melody or sub.

hook_wave = "sine" 

# E5
n1 = beep(note_to_freq("E5"), 0.250, hook_wave)
# E5
n2 = beep(note_to_freq("E5"), 0.250, hook_wave)
# C#3 (Make this one longer and deeper)
n3 = beep(note_to_freq("C#3"), 0.125, "triangle") 
# F#5 (The resolution)
n4 = beep(note_to_freq("F#5"), 0.125, hook_wave)

motif = n1 & n2 & n3 & n4
# Total duration: 0.25+0.25+0.125+0.125 = 0.75 bars. 
# We need to fill 4 bars for the loop.
# Let's repeat it or extend/rest.
# Motif is short now.
# E E C# F# . . . .
motif_4bar = motif & silence(4 - 0.75)

# Slow Trap Glitch Drums
# Kick on 1 and & of 3.
kick = beep(60, 0.25, "square") * 0.8
hat = beep(8000, 0.125, "noise") * 0.2
snare = beep(200, 0.25, "noise") * 0.5

# Bar 1: Kick . . . Snare . . Kick .
b1 = kick & silence(0.25) & silence(0.25) & silence(0.25) & snare & silence(0.25) & silence(0.25) & kick
# Bar 2: . . . . Snare . . .
b2 = silence(1) # Chill
# Bar 3: Kick . . . Snare . . .
b3 = kick & silence(0.75) & snare
# Bar 4: Fast Hats
b4 = hat & hat & hat & hat & hat & hat & hat & hat

drums = (b1 & b2 & b3 & b4)

# 3. Atmospherics
# ---------------
# F#m Pad (F# A C#) and Dmaj7 Pad (D F# A C#)
pad_fsm = chord("F#3", "minor", 2, "sawtooth") * 0.2
pad_dmaj = chord("D3", "major", 2, "sawtooth") * 0.2

pads = pad_fsm & pad_dmaj

# 4. Assembly
# -----------
# Intro: Pads only
intro = pads

# Main: Motif + Drums + Pads
main = (motif_4bar * 0.6) + drums + pads

# B-Section: Reverse the Motif for "Alien" effect
alien_motif = motif_4bar.reverse() * 0.5
section_b = alien_motif + drums

# Outro: Cusp Fade
fade = cusp_crescendo(note_to_freq("F#2"), 2, 32, 2) * 0.4
outro = fade.reverse() # Fade out? No, reverse cusp is loud->quiet? 
# Cusp is quiet->loud. Reverse is loud->quiet (decrescendo). Correct.
outro_hit = beep(note_to_freq("F#2"), 2, "sine") * 0.5 

final_mix = intro & main & section_b & outro_hit

final_mix

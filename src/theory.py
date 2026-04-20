import re

def note_to_freq(note: str) -> float:
    """
    Converts a note string (e.g., 'A4', 'C#3', 'Gb5') to frequency in Hz.
    Reference: A4 = 440Hz.
    """
    if not isinstance(note, str):
        try:
            return float(note)
        except:
            return 0.0

    # Simple regex to parse note, accidental, octave
    match = re.match(r"([A-Ga-g])([#b]?)(-?\d+)", note)
    if not match:
        # Fallback or maybe it's just a frequency as a string
        try:
            return float(note)
        except:
            print(f"Warning: Could not parse note '{note}'")
            return 0.0
            
    name, accidental, octave = match.groups()
    name = name.upper()
    octave = int(octave)
    
    semitone_map = {
        'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11
    }
    
    semitone = semitone_map.get(name, 0)
    
    if accidental == '#':
        semitone += 1
    elif accidental == 'b':
        semitone -= 1
        
    # A4 is the 69th semitone in MIDI (where C-1 is 0), or:
    # A4 (octave 4) is 9 semitones above C4.
    # Our map is 0-indexed from C.
    
    # Calculate semitone distance from A4
    # A4 is 440hz. A4 is octave 4, semitone 9.
    
    # Absolute semitone number (C0 = 0)
    # This formula needs to be correct.
    # MIDI Note limit: C4 maps to 60.
    # A4 (69) - C4 (60) = 9. Correct.
    
    midi_note = (octave + 1) * 12 + semitone
    
    # Frequency formula: f = 440 * (2 ** ((midi_note - 69) / 12))
    freq = 440.0 * (2 ** ((midi_note - 69) / 12))
    return freq

def freq_to_note(freq: float) -> str:
    """
    Converts a frequency in Hz to the nearest note string (e.g., 'A4').
    """
    if freq <= 0:
        return "C0" # Fallback
        
    # Standard formula: m = 12 * log2(f/440) + 69
    import math
    midi_note = 12 * math.log2(freq / 440.0) + 69
    midi_note = round(midi_note)
    
    # MIDI 0 is C-1 (approx 8.17 Hz)
    # MIDI 60 is C4
    
    # Octave
    octave = (midi_note // 12) - 1
    
    # Semitone names
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    semitone = midi_note % 12
    name = note_names[semitone]
    
    return f"{name}{octave}"

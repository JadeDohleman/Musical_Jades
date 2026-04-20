from .pattern import Pattern, Event
from .theory import note_to_freq
import math

def beep(freq=440, duration=0.1, waveform="sine"):
    """
    Returns a Pattern with a single beep.
    """
    # Create an event at time 0 with given duration
    # Value is the frequency directly or a note name. 
    e = Event(timestamp=0.0, duration=duration, value=str(freq), waveform=waveform)
    return Pattern([e], cycles=duration)

def silence(duration=1):
    """
    Returns a silent Pattern of a given duration (cycles).
    """
    return Pattern([], cycles=duration)

def elastic_beeps(start_density=1, peak_density=4, end_density=1, bars=8, note_freq=440, waveform="sine"):
    """
    Generates a sequence of beeps with variable density.
    Density (beeps/bar) ramps:
      - Start -> Peak (0 to bars/2)
      - Peak -> End (bars/2 to bars)
      
    Uses phase accumulation to determine beep onsets.
    Phase phi(t) = integral of Density(t) dt.
    Beep when phi(t) crosses integer boundary.
    """
    events = []
    
    # We simulate time in small steps to find crossings
    # Or analytically integration.
    # Split into two halves.
    
    mid_bar = bars / 2.0
    
    def get_density(t):
        if t < mid_bar:
            # Linear ramp from start to peak
            # D(t) = start + (peak - start) * (t / mid_bar)
            return start_density + (peak_density - start_density) * (t / mid_bar)
        else:
            # Linear ramp from peak to end
            # t' = t - mid_bar
            # D(t') = peak + (end - peak) * (t' / mid_bar)
            t_prime = t - mid_bar
            return peak_density + (end_density - peak_density) * (t_prime / mid_bar)

    # Numerical integration for simplicity and robustness
    dt = 0.01 # Resolution in bars
    t = 0.0
    phase = 0.0
    last_phase = 0.0
    
    while t < bars:
        d = get_density(t)
        phase += d * dt
        
        # Check for integer crossing
        # Actually proper way: check floor(phase) > floor(last_phase)
        if math.floor(phase) > math.floor(last_phase):
            # We crossed an integer!
            # Precise time roughly at t
            # Duration: inversely proportional to density.
            # Base duration: e.g. 0.5 / density (half duty cycle)
            
            # Note: duration in our engine is in cycles (bars).
            # If density is 4 beeps/bar, each beep is 0.25 bar apart.
            # Making duration = 0.5 * (1/d) ensures gaps.
            
            beep_dur = 0.5 / d if d > 0 else 0.1
            
            # Clamp duration to not exceed total bars
            if t + beep_dur > bars:
                beep_dur = bars - t
            
            # The beep event
            # Use provided freq
            e = Event(timestamp=t, duration=beep_dur, value=str(note_freq), waveform=waveform)
            events.append(e)
            
        last_phase = phase
        t += dt
        
    return Pattern(events, cycles=bars)

def echo_pattern(freq=440, repeats=8, decay=0.6, interval=0.25, waveform="sine"):
    """
    Generates a sequence of repeating notes with exponentially decaying volume.
    """
    events = []
    current_vol = 1.0
    
    for i in range(repeats):
        # Create event
        e = Event(timestamp=i * interval, duration=interval, value=str(freq), waveform=waveform, volume=current_vol)
        events.append(e)
        
        # Decay volume
        current_vol *= decay
        
    # Total duration is roughly repeats * interval
    return Pattern(events, cycles=repeats * interval)

def cusp_crescendo(freq=440, duration=4, n_events=32, power=4, waveform="sine"):
    """
    Generates a sequence of notes with volume increasing increasingly sharply (power curve).
    
    Args:
        freq: Frequency of the note.
        duration: Total duration in cycles (bars).
        n_events: Number of discrete notes to generate.
        power: Exponent for the volume curve. Higher = sharper cusp (quieter for longer).
        waveform: Waveform type.
    """
    events = []
    step = duration / n_events
    # Slight gap to distinguish notes
    event_dur = step * 0.9 
    
    for i in range(n_events):
        t = i * step
        # Normalized progress (0 to 1)
        # We want the last note to be roughly volume 1.0, 
        # and checking volume at the time of the note.
        progress = (i + 1) / n_events
        vol = progress ** power
        
        e = Event(timestamp=t, duration=event_dur, value=str(freq), waveform=waveform, volume=vol)
        events.append(e)
        
    return Pattern(events, cycles=duration)

def reverse(pattern):
    """
    Reverse the audio of a pattern.
    """
    return pattern.reverse()

def chord(root="C4", quality="major", duration=1, waveform="sine"):
    """
    Generates a chord pattern.
    Qualities: major, minor, dim, aug.
    """
    freq = note_to_freq(root)
    if freq <= 0:
        return Pattern([], cycles=duration)
        
    semitones = [0] # Root
    
    q = quality.lower()
    if q == "major" or q == "maj":
        semitones.extend([4, 7])
    elif q == "minor" or q == "min":
        semitones.extend([3, 7])
    elif q == "dim":
        semitones.extend([3, 6])
    elif q == "aug":
        semitones.extend([4, 8])
    else:
        # Default to major
        semitones.extend([4, 7])
        
    # Build chord pattern: Sum of beeps
    p = Pattern([], cycles=duration)
    
    for semi in semitones:
        f = freq * (2 ** (semi / 12.0))
        # Note: We probably want to normalize volume? 
        # Summing 3 waves -> amplitude 3. Renderer handles soft clip, so it's okay.
        p = p + beep(f, duration=duration, waveform=waveform)
        
    return p

def crossfade(p1, p2, duration=1):
    """
    Smoothly transition from p1 to p2 over `duration` cycles.
    """
    if not isinstance(p1, Pattern) or not isinstance(p2, Pattern):
        return NotImplemented
    new_cycles = p1.cycles + p2.cycles - duration
    if new_cycles < 0:
        new_cycles = max(p1.cycles, p2.cycles)
    return Pattern(cycles=new_cycles, operator="crossfade", operands=[p1, p2, duration])

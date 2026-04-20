import numpy as np
import scipy.signal

def generate_wave(frequency, duration, waveform="sine", sr=44100, amplitude=0.5):
    """
    Generate a 1D NumPy array (float32) for a single note.
    """
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    
    if waveform.lower() == "sine":
        wave = np.sin(2.0 * np.pi * frequency * t)
    elif waveform.lower() == "square":
        # scipy.signal.square is more robust
        wave = scipy.signal.square(2.0 * np.pi * frequency * t)
    elif waveform.lower() == "triangle":
        wave = scipy.signal.sawtooth(2.0 * np.pi * frequency * t, width=0.5)
    elif waveform.lower() == "sawtooth":
        wave = scipy.signal.sawtooth(2.0 * np.pi * frequency * t)
    else:
        # Default to sine
        wave = np.sin(2.0 * np.pi * frequency * t)
        
    return wave * amplitude

def apply_envelope(wave, duration, sr=44100, attack=0.01, decay=0.1, sustain=0.7, release=0.1):
    """
    Apply a simple ADSR envelope to the wave.
    Note: For a simple sequencer, we might just use AR or ASR for fixed duration notes.
    Here we fit the envelope to the duration.
    """
    total_samples = len(wave)
    attack_samples = int(attack * sr)
    release_samples = int(release * sr)
    decay_samples = int(decay * sr)
    
    # Validation to ensure envelope doesn't exceed duration
    if attack_samples + release_samples > total_samples:
        # Shorten attack/release to fit
        scale = total_samples / (attack_samples + release_samples)
        attack_samples = int(attack_samples * scale)
        release_samples = int(release_samples * scale)
        decay_samples = 0 # Skip decay in this edge case

    sustain_samples = total_samples - attack_samples - decay_samples - release_samples
    if sustain_samples < 0:
        sustain_samples = 0
        decay_samples = total_samples - attack_samples - release_samples
    
    # Construct envelope
    env_attack = np.linspace(0, 1, attack_samples)
    env_decay = np.linspace(1, sustain, decay_samples)
    env_sustain = np.full(sustain_samples, sustain)
    env_release = np.linspace(sustain, 0, release_samples)
    
    envelope = np.concatenate([env_attack, env_decay, env_sustain, env_release])
    
    # If rounding errors caused mismatch in length
    if len(envelope) < total_samples:
        envelope = np.pad(envelope, (0, total_samples - len(envelope)), 'constant', constant_values=0)
    elif len(envelope) > total_samples:
        envelope = envelope[:total_samples]
        
    return wave * envelope

# Auto-generated from audio inspiration (Rhythm Preserved)

# Melody Sequence
s0 = silence(duration=0.375)
n1 = beep(note_to_freq('E5'), duration=0.250, waveform='sine')
n2 = beep(note_to_freq('C#3'), duration=0.125, waveform='sine')
s3 = silence(duration=0.250)
n4 = beep(note_to_freq('F#5'), duration=0.125, waveform='sine')
n5 = beep(note_to_freq('D5'), duration=0.125, waveform='sine')
n6 = beep(note_to_freq('B2'), duration=0.125, waveform='sine')
n7 = beep(note_to_freq('E6'), duration=0.125, waveform='sine')
n8 = beep(note_to_freq('E5'), duration=0.250, waveform='sine')
n9 = beep(note_to_freq('C#5'), duration=0.125, waveform='sine')
n10 = beep(note_to_freq('A2'), duration=0.125, waveform='sine')
s11 = silence(duration=0.375)

# Combine
melody = s0 & n1 & n2 & s3 & n4 & n5 & n6 & n7 & n8 & n9 & n10 & s11
melody * 0.5
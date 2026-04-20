# 4-Note Peak Demo
# Extracted Top 4 Notes based on duration/prominence
p0 = beep(note_to_freq('E5'), duration=0.250, waveform='square')
p1 = beep(note_to_freq('E5'), duration=0.250, waveform='square')
p2 = beep(note_to_freq('C#3'), duration=0.125, waveform='square')
p3 = beep(note_to_freq('F#5'), duration=0.125, waveform='square')

# The Motif
motif = p0 & p1 & p2 & p3
motif
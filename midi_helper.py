import midi
from interval import Interval

def export_midi( chord, filename ):
    print( filename )
    for note in chord:
        print(note.freq)
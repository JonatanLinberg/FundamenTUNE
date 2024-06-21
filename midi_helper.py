import midi
from interval import Interval, cent_diff

def closest_midi_note( freq ):
    # A4 == 440 Hz == midi 69 (nice)
    diff = cent_diff( freq, 440 )
    diff //= 100 # diff in semitones
    return int(69 + diff)

def export_midi( chord, filename, base_channel, pitch_range ):

    ####
    # Create Header
    ####
    d_ticks = 1
    header = midi.Header.create_basic_header( d_ticks )

    ####
    # Create Track
    ####
    def iter_to_ch( i ):
        return i + ( 0 if i < base_channel else 1 )

    events = []
    # create one pitch bend and note on event for each note
    chord = list(chord.values())
    for i, note in enumerate(chord):
        ch = iter_to_ch( i )

        range_cents = pitch_range * 100
        pitch_bend_scale = 0x4000 / range_cents

        cents = note.cents_off_piano
        pitch_val = 0x2000 + round(cents * pitch_bend_scale)
        events.append(
            midi.Event.create_pitch( 0, ch=ch, pitch_val=pitch_val )
        )

        key = closest_midi_note( note.frequency )
        vel = 80
        events.append(
            midi.Event.create_key_on( 0, key, ch=ch, vel=vel )
        )

    # add note off for each note
    delta_time = d_ticks * 4 # whole notes
    for i, note in enumerate(chord):
        ch = iter_to_ch( i )
        key = closest_midi_note( note.frequency )
        events.append(
            midi.Event.create_key_off( delta_time, key, ch=ch )
        )
        delta_time = 0 # only first note should have delta_time > 0

    track = midi.Track( events )

    midi.write_file( f"{filename}.mid", [header, track] )

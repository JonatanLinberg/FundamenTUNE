#!/usr/local/bin/python3
from math import floor as _floor
from sys import stderr as _stderr


class UnsupportedMidiException(Exception):
    def __init__(self, message, midi):
        self.message = message
        self.midi = midi

    def __str__(self):
        return self.message + str(self.midi)

class NotImplementedException(Exception):
    def __init__(self, feature):
        self.feature = feature

    def __str__(self):
        return "Sorry! " + str(self.feature) + " has not yet been implemented."

class InvalidEvent(Exception):
    def __init__(self, status, method):
        self.status = str(status)
        self.method = str(method)

    def __str__(self):
        return "Event of type '" + self.status + "' is incompatible with " + self.method + "."






class Chunk():

    def parse_data(self, data):
        raise NotImplementedException("Abstract parse_data")

    def to_bytes(self):
        raise NotImplementedException("Abstract to_bytes")

    def getLength(self):
        return self.getDataLength() + 8

    def getDataLength(self):
        raise NotImplementedException("Abstract getDataLength")







class Header(Chunk):
    def __init__(self, data_length, _format, n_tracks, div):
        self.datalen = data_length
        self.format = _format
        self.n_tracks = n_tracks

        self.div_format = div['format']
        if (self.div_format == 'delta_ticks'):
            self.delta_ticks = div['delta_ticks']
        else:
            pass


    @classmethod
    def from_bytes(cls, data_length, data):
        _format = int.from_bytes(data[:2], byteorder='big')
        n_tracks = int.from_bytes(data[2:4], byteorder='big')

        raw_div = int.from_bytes(data[4:], byteorder='big')
        if (raw_div & 0x8000):  #subdiv of second
            raise NotImplementedException('Negative SMPTE delta time')
        else:   # length of quarter note
            div = {'format':'delta_ticks', 'delta_ticks':raw_div}

        return cls(data_length, _format, n_tracks, div)

    @classmethod
    def create_basic_header(cls, delta_ticks):
        return cls( 6, 0, 1, { 'format':'delta_ticks', 'delta_ticks':delta_ticks } )

    def to_bytes(self, **kwargs):
        ret = b'MThd'
        ret += self.getDataLength().to_bytes(4, byteorder='big')
        ret += self.format.to_bytes(2, byteorder='big')
        ret += self.n_tracks.to_bytes(2, byteorder='big')
        
        if (self.div_format == 'delta_ticks'):
            if (self.delta_ticks >= 0x8000):
                print("Warning: Converting delta ticks larger than 2^15 = 32768 will cut the extra bits.", file=_stderr)
            ret += (self.delta_ticks & 0x7fff).to_bytes(2, byteorder='big')
        else: 
            raise NotImplementedException('Negative SMPTE delta time')
        return ret

    def getDataLength(self):
        return self.datalen

    def __str__(self):
        format_str = ('(0) Single Track', '(1) Simultaneous Tracks', '(2) Sequential Tracks')
        if (self.div_format == 'delta_ticks'):
            division = "Delta Ticks: %d" % (self.delta_ticks)
        else:
            division = "[[ Unsupported Division Format ]]"
        return "Header:\n\tNumber of Tracks: %d\n\tFormat: %s\n\tDivision: %s" % (self.n_tracks, format_str[self.format], division)








class Track(Chunk):
    def __init__(self, events):
        self.events = events

    @classmethod
    def from_bytes(cls, data):
        events = []

        while (data != b''):
            delta_time, data = decode_varlen( data )
            status = data[0]
            if (status < 0x80):     # Running status -> use last status   !!! assumes only true for < 0x80
                status = lastStatus
            lastStatus = status     # Save status for running status

            if (status == 0xff):
                e_type = data[1]
                length, data = decode_varlen( data[2:] )
                events.append(Event(delta_time,
                                    status,
                                    e_type = e_type,
                                    datalen = length,
                                    data = data[:length] ))
                data = data[length:]

            elif ( status & 0xf0 == Event._STATUS_NOTE_OFF or 
                   status & 0xf0 == Event._STATUS_NOTE_ON ): # & 0xf0 bit 0-3 is channel nr
                events.append(Event(delta_time,
                                    status & 0xf0, # mask channel
                                    channel = status & 0xf, # mask status
                                    key = data[1],
                                    velocity = data[2] ))
                data = data[3:]

            elif ( status & 0xf0 == Event._STATUS_PITCH ):
                first = data[1] & 0x7f
                second = data[2] & 0x7f
                pitch_val = (second << 7) | first # 14-bit value: 0b00sssssssfffffff
                events.append( Event( delta_time,
                                      status & 0xf0, # mask ch
                                      channel = status & 0xf, # mask status
                                      pitch = pitch_val))
                data = data[3:]

            else:
                raise UnsupportedMidiException('Unknown midi status code: ', hex(status))

        return cls(events)


    def to_bytes(self, clean=False, **kwargs):
        ret = b'MTrk'
        
        e_b = b''
        for e in self.events:
            if ( ( not clean) or ( not e.cleanable ) ):
                e_b += e.to_bytes()
        
        ret += len(e_b).to_bytes(4, byteorder='big')
        ret += e_b
        return ret

    def getDataLength(self):
        _sum = 0
        for e in self.events:
            _sum += len(e.to_bytes())
        return _sum

    # mult is a multiplier of the speed e.g:
    #   2: double speed (half delta_time)
    def modify_speed(self, mult):
        for i, _ in enumerate(self.events):
            self.events[i].delta_time = round(self.events[i].delta_time / mult)

    def add_event(self, event, i):
        next_event = self.events[i]
        if (next_event.delta_time < event.delta_time):
            # next event comes before this event => Error or handle?
            # handle and use iteratively through events list
            event.delta_time -= next_event.delta_time
            return self.add_event(event, i+1)
        else:
            next_event.delta_time -= event.delta_time
            self.events.insert(i, event)

    def pop_event(self, i):
        event = self.events.pop(i)
        self.events[i].delta_time += event.delta_time
        return event
    
    def add_note(self, time, key, dur, vel=64, ch=0):
        key_on = Event.create_key_on(time, key, vel=vel, ch=ch)
        key_off = Event.create_key_off(time+dur, key, vel=vel, ch=ch)
        self.add_event(key_on, 0)
        self.add_event(key_off, 0)

    def remove_note(self, i):
        key_on = self.pop_event(i)

        if (key_on.get_status_name() == "Note on"):
            for j in range(i, len(self.events)):
                e = self.events[j]
                if (e.get_status_name() == "Note off" and
                    e.channel == key_on.channel and
                    e.key == key_on.key):
                    self.pop_event(j)
                    return

        else:
            raise InvalidEvent(key_on.get_status_name(), "remove note")

    def __getitem__(self, i):
        return self.events[i]

    def __str__(self):
        return "Track:\n\t" \
                + ''.join(s.ljust(Event._out_str_just_len) for s in ['Delta Time', 'Status', 'Channel', 'Key', 'Velocity', 'Misc.']) \
                + "\n\t" \
                + "\n\t".join([str(e) for e in self.events])







class Event():
    _out_str_just_len = 12
    _STATUS_NOTE_OFF  = 0x80
    _STATUS_NOTE_ON   = 0x90
    _STATUS_PITCH     = 0xe0
    _STATUS_META      = 0xff
    _STATUS_NAME = {
        _STATUS_NOTE_OFF:'Note off',
        _STATUS_NOTE_ON:'Note on',
        _STATUS_PITCH:'Pitch bend',
        _STATUS_META:'Meta Event',
    }
    _TYPE_EOF = 0x2f

    def __init__(self, delta_time, status, channel=None, key=None, velocity=None, e_type=None, pitch=None, datalen = 0, data=None):
        if data and len(data) != datalen:
            print(f"ERROR! Inconsistent data/datalen: { data }/{ datalen }")
        self.delta_time = delta_time
        self.status = status
        self.channel = channel
        self.key = key
        self.velocity = velocity
        self.pitch = pitch
        self.type = e_type
        self.datalen = datalen
        self.data = data

    @classmethod
    def create_key_on(cls, delta_time, key, vel=64, ch=0):
        return cls(delta_time, Event._STATUS_NOTE_ON, ch, key, vel)

    @classmethod
    def create_key_off(cls, delta_time, key, vel=0, ch=0):
        return cls(delta_time, Event._STATUS_NOTE_OFF, ch, key, vel)

    @classmethod
    def create_pitch(cls, delta_time, ch = 0, pitch_val = 0x2000):
        # 0x2000 == no pitch change
        # range:  [ 0, 0x4000 )
        if pitch_val < 0:
            pitch_val = 0
        elif pitch_val >= 0x4000:
            pitch_val = 0x3fff

        return cls( delta_time, Event._STATUS_PITCH, channel=ch, pitch=pitch_val )


    @classmethod
    def create_meta(cls, delta_time, e_type, d_len, data):
        return cls(delta_time, Event._STATUS_META, e_type=e_type, datalen=d_len, data=data)

    @classmethod
    def create_eof(cls, delta_time):
        return Event.create_meta(delta_time, Event._TYPE_EOF, 0, b'')

    def get_status_name(self):
        return Event._STATUS_NAME[self.status]

    def to_bytes(self):
        ret = encode_varlen(self.delta_time)
        if ( Event._STATUS_NOTE_OFF == self.status or
             Event._STATUS_NOTE_ON  == self.status ):
            ret += ( self.status | self.channel ).to_bytes(1, byteorder='big')
            ret += self.key.to_bytes(1, byteorder='big')
            ret += self.velocity.to_bytes(1, byteorder='big')

        elif ( Event._STATUS_PITCH == self.status ):
            ret += ( self.status | self.channel ).to_bytes(1, byteorder='big')
            first = self.pitch & 0x7f
            second = ( self.pitch >> 7 ) & 0x7f
            ret += first.to_bytes(1, byteorder='big')
            ret += second.to_bytes(1, byteorder='big')

        elif ( Event._STATUS_META == self.status ):
            ret += self.status.to_bytes(1, byteorder='big')
            ret += self.type.to_bytes(1, byteorder='big')
            ret += encode_varlen(self.datalen)
            ret += self.data

        else:
            raise UnsupportedMidiException( f"Cannot encode event with status: ", hex(self.status) )

        return ret

    @property
    def cleanable(self):
        return (self.status == Event._STATUS_META and self.type != Event._TYPE_EOF)

    #   delta_time  status  channel  key  velocity  misc
    def __str__(self):
        out = [ self.delta_time, self.get_status_name(), self.channel, self.key, self.velocity]
        if ( self.status == Event._STATUS_META ):
            out.append("[%s] %a" % (hex(self.type).rjust(2, '0'), self.data))
        if ( self.status == Event._STATUS_PITCH ):
            out.append("[%d]" % (self.pitch - 0x2000) )
        return ''.join([_str(s).ljust(Event._out_str_just_len) for s in out])





def _str(a):
    if (a is not None):
        return str(a)
    else:
        return ""

def encode_varlen(val):
    byte_arr = []
    if (val == 0):
        return bytes([0])

    while val:
        byte_arr = [(val & 0x7f)] + byte_arr
        val //= 128
    for i in range(len(byte_arr)-1):
        byte_arr[i] |= 0x80
    return bytes(byte_arr)





# parses first varlen value and returns it and the rest of the data
def decode_varlen(data):
    byte_arr = []
    rest = []

    for i,_ in enumerate(data):
        if (data[i] & 0x80):
            byte_arr = [(data[i] & 0x7f)] + byte_arr
        else:
            byte_arr = [(data[i] & 0x7f)] + byte_arr
            rest = data[i+1:]
            break
    val = 0
    for i,_ in enumerate(byte_arr):
        val += (byte_arr[i] << i*7)
    return val, rest





def decode_chunk(data):
    if (data[0:4] == b'MThd'):
        c_type = 'header'
    elif (data[0:4] == b'MTrk'):
        c_type = 'track'
    else:
        raise UnsupportedMidiException("Unknown midi chunk type:", data[0:4])

    d_len = int.from_bytes(data[4:8], byteorder='big')
    c_len = d_len+8
    c_data = data[8:c_len]

    if (c_type == 'header'):
        return Header.from_bytes(d_len, c_data), c_len
    
    elif (c_type == 'track'):
        return Track.from_bytes(c_data), c_len


def decode_chunks(data):
    chunks = []
    
    while (data != b''):
        c, i = decode_chunk(data)
        chunks.append(c)
        data = data[i:]
    return chunks


def write_file(filename, chunks, clean_file=False):
    with open(filename, 'wb') as out:
        for c in chunks:
            out.write(c.to_bytes(clean=clean_file))

def read_file(filename):
    data = open(filename, 'rb').read()
    return decode_chunks(data)




if (__name__ == "__main__"):
    from sys import argv

    try:
        chunks = read_file(argv[1])
    except IndexError:
        try:
            chunks = read_file(input("Enter file name: "))
        except Exception as e:
            print(e)
            quit()

    for c in chunks:
        print(c)
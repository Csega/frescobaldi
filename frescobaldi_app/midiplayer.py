#! python

# Python midiplayer.py -- base class for a MIDI player
# Copyright (C) 2011 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.


"""
A MIDI Player.
"""


import collections
import midisong


class Player(object):
    """The base class for a MIDI player.
    
    It should be inherited to actually play MIDI:
    - midi_event() should be implemented to play the MIDI to an output port.
    - start() and stop() should be implemented for timing logic. These logic
      should call next_event() and use the returned time offset to schedule
      the next call to next_event().
    - is_playing() should be implemented.
    - set_position() should be implemented to enable seeking.
    
    """
    def __init__(self):
        self._song = None
        self._events = []
        self._position = 0
        self._tempo_factor = 1.0
    
    def load(self, filename, time=1000, beat=True):
        """Convenience function, loads a MIDI file.
        
        See setSong() for the other arguments.
        
        """
        song = midisong.load(filename)
        self.set_song(song, time, beat)
    
    def set_song(self, song, time=1000, beat=True):
        """Loads the specified Song (see midisong.py).
        
        If time is not None, it specifies at which interval (in msec) the
        time() method will be called. Default: 1000.
        If beat is True (default), the beat() method will be called on every
        beat.
        
        """
        self._song = song
        self._events = make_event_list(song, time, beat)
    
    def song(self):
        """Returns the current Song."""
        return self._song
    
    def total_time(self):
        """Returns the length in msec of the current song."""
        if self._events:
            return self._events[-1][0]
        return 0
    
    def current_time(self):
        """Returns the current time.
        
        This method simply returns the time of the last played event.
        Inherit to really return the current playing time.
        
        """
        pos = self._position - 1
        return self._events[pos][0] if pos >= 0 else 0
    
    def start(self):
        """Starts playing."""
    
    def stop(self):
        """Stops playing."""
    
    def is_playing(self):
        """Returns True if the player is playing, else False."""
    
    def set_tempo_factor(self, factor):
        """Sets the tempo factor as a floating point value (1.0 is normal)."""
        self._tempo_factor = factor
    
    def tempo_factor(self):
        """Returns the tempo factor (by default: 1.0)."""
        return self._tempo_factor
    
    def seek(self, time):
        """Goes to the specified time (in msec)."""
        pos = 0
        offset = 0
        if time:
            # bisect our way in the events list.
            end = len(self._events)
            while pos < end:
                mid = (pos + end) // 2
                if time > self._events[mid][0]:
                    pos = mid + 1
                else:
                    end = mid
            offset = self._events[pos][0] - time
        self.set_position(pos, offset)
    
    def seek_measure(self, measnum, beat=1):
        """Goes to the specified measure and beat (beat defaults to 1).
        
        Returns whether the measure position could be found (True or False).        
        
        """
        result = False
        for i, (t, e) in enumerate(self._events):
            if e.beat:
                if e.beat[0] == measnum:
                    position = i
                    result = True
                    if e.beat[1] >= beat:
                        break
                if e.beat[0] > measnum:
                    break
        if result:
            self.set_position(position)
            return True
        return False
        
    def set_position(self, position, time_offset=0):
        """(Private) Goes to the specified position in the internal events list.
        
        The default implementation does nothing with the time offset,
        but inherited implementations may wait that many msec before
        triggering the event at that position.
        
        This method is called by seek() and seek_measure().
        
        """
        self._position = position
        
    def next_event(self):
        """(Private) Handles the current event and advances to the next.
        
        Returns the time in ms (not adjusted by tempo factor!) before
        next_event should be called again.
        
        If there is no event to handle anymore, returns 0.
        If this event was the last, calls finish() and returns 0.
        
        """
        if self._events and self._position < len(self._events):
            time, event = self._events[self._position]
            self.handle_event(time, event)
            self._position += 1
            if self._position < len(self._events):
                return self._events[self._position][0] - time
            self.finish()
        return 0
    
    def finish(self):
        """(Private) Called when a played song reaches the end.
        
        The default implementation calls stop().
        
        """
        self.stop()
    
    def handle_event(self, time, event):
        """(Private) Called for every event."""
        if e.midi:
            self.midi_event(e.midi)
        if e.time:
            self.time_event(time)
        if e.beat:
            self.beat_event(*e.beat)
    
    def midi_event(self, midi):
        """(Private) Plays the specified MIDI events.
        
        The format depends on the way MIDI events are stored in the Song.
        
        """
    
    def time_event(self, msec):
        """(Private) Called on every time update."""
    
    def beat_event(self, measnum, beat, num, den):
        """(Private) Called on every beat."""



class Event(object):
    """Any event (MIDI, Time and/or Beat).
    
    Has three attributes that determine what the Player does:
    
    time: if True, time_event() is caled with the current music time.
    beat: None or (measnum, beat, num, den), then beat_event() is called.
    midi: If not None, midi_event() is called with the midi.
    
    """
    __slots__ = ['midi', 'time', 'beat']
    def __init__(self):
        self.midi = None
        self.time = None
        self.beat = None

    def __repr__(self):
        l = []
        if self.time:
            l.append('time')
        if self.beat:
            l.append('beat({0}:{1})'.format(self.beat[0], self.beat[1]))
        if self.midi:
            l.append('midi')
        return '<Event ' + ', '.join(l) + '>'


def make_event_list(song, time=None, beat=None):
    """Returns a list of all the events in Song.
    
    Each item is a two-tuple(time, Event).
    
    If time is given, a time event is generated every that many microseconds
    If beat is True, beat events are generated as well.
    MIDI events are always created.
    
    """
    d = collections.defaultdict(Event)
    
    for t, evs in song.music:
        d[t].midi = evs
    
    if time:
        for t in range(0, song.length+1, time):
            d[t].time = True
    
    if beat:
        for i in song.beats:
            d[i[0]].beat = i[1:]
    
    return [(t, d[t]) for t in sorted(d)]



import alsaseq
import time
import pandas as pd
import pydantic

from utils.decorator import memoize

MIDI_OFFSET = 20


@memoize
def start_client(connection_id=20):
    alsaseq.client('Simple', 1, 0, False)
    alsaseq.connectfrom(0, connection_id, 0)


class RawMidiNote(pydantic.BaseModel):
    start: float
    piano_key: int
    velocity: int
    dampened: bool = False
    end: float = None


NOTE_PLAYED = 6
PEDAL_PRESSED = 10
HEARTBEAT = 42

SUSTAIN_PEDAL = 64
MIDDLE_PEDAL = 66
DAMPEN_PEDAL = 67


class LiveListener(object):
    def __init__(self, connection_id=20):
        start_client(connection_id)
        self.notes = []  # type:list[RawMidiNote]
        self.pedal_events = []
        self.dampened = False
        self.sounding_notes = {}
        self.sustained_notes = {}
        self.mid_sustained_notes = {}
        self.sustain = False

    def listen(self):
        while True:
            try:
                if alsaseq.inputpending():
                    self.process_event(alsaseq.input())
            except KeyboardInterrupt:
                break

    def process_event(self, event):
        typ = event[0]
        if typ == NOTE_PLAYED:
            _, midi_key, velocity, __, ___ = event[-1]
            key = midi_key - MIDI_OFFSET
            if velocity == 0:
                note = self.sounding_notes.pop(key)
                note.end = time.time()
            else:
                note = RawMidiNote(start=time.time(), piano_key=key, velocity=velocity, dampened=self.dampened)
                print(note)
                self.sounding_notes[key] = note
                self.notes.append(note)
                if self.sustain:
                    self.sustained_notes[key] = note
                if key in self.mid_sustained_notes:
                    self.mid_sustained_notes[key] = note
        elif typ == PEDAL_PRESSED:
            pedal, depressed = event[-1][-2:]
            self.pedal_events.append((pedal, depressed, time.time()))
            if pedal == DAMPEN_PEDAL:
                self.dampened = bool(depressed)
            elif pedal == MIDDLE_PEDAL:
                if depressed:
                    self.mid_sustained_notes = dict(self.sounding_notes)
                else:
                    self.mid_sustained_notes = {}
            elif pedal == SUSTAIN_PEDAL:
                self.sustain = bool(depressed)
                if not depressed:
                    self.sustained_notes = {}
        elif typ != HEARTBEAT:
            print(event)


class Chord(object):
    def __init__(self, note):
        self.notes = [note]
        self.start = note.start
        self.end = note.end

    def add_note(self, note):
        if note.end > self.end:
            self.end = note.end
        self.notes.append(note)


def group_chords(notes, threshold=.02):
    chord = Chord(notes[0])
    chords = [chord]

    for note in notes[1:]:
        if (note.start - chord.start) < threshold:
            chord.add_note(note)
        else:
            chord = Chord(note)
            chords.append(chord)

    return chords


def infer_rhythm(chords, hint=.02, var=.20, most_common=1, sequence=(1, 2, 3, 4, 8)):
    """
    :type chords: list[Chord]
    :param hint: float; used to group the length of the chords to guess at the length of a single beat
    :param var: float; the variation from one beat that is to be expected (between 0 and 1)
    :param most_common: the number of beats in the most common note
    :param sequence: a list of the valid denominators of fractions of a single beat
    :return:
    """
    mult = int(1/hint)
    last = chords[0]
    differences = []
    raw_diffs = []
    for chord in chords[1:]:
        raw = chord.start - last.start
        differences.append(int(mult * raw))
        raw_diffs.append(raw)
        last = chord
    counts = pd.Series(differences).value_counts()
    if len(counts) == len(raw_diffs):
        raise ValueError('Hint ({}) is too tight or not enough chords to infer rhythm'.format(hint))
    mode = hint * counts.idxmax()
    raw = pd.Series(raw_diffs)
    best_guess = raw[((1 - var) * mode < raw) & (raw < (1 + var) * mode)].mean()
    best_guess = best_guess/most_common
    denoms = pd.Series(pd.np.nan, range(len(raw)))
    for i in reversed(sequence):
        s = (i * raw / best_guess)  # type: pd.Series
        r = s.round()
        valid = (s - r).abs() < var
        denoms[valid] = i

    nums = (denoms * raw/best_guess).round()

    return pd.DataFrame(dict(nums=nums, denoms=denoms, raw=raw, bg=best_guess))



l = LiveListener()
l.listen()
last = 0
print([n.piano_key for n in l.notes])
print(infer_rhythm(group_chords(l.notes)))



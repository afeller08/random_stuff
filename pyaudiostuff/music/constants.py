from enum import Enum
import math


class Harmonics(object):
    simple = {i: 1/i for i in range(1, 11)}
    decayed = {i: 1/i ** 2 for i in range(1, 11)}
    exp_decayed = {i: 1/(2**i) for i in range(1, 11)}
    negradius = {.9992 ** (i-1) * i: 1/(2 * 1.7**i) for i in range(1, 11)}
    inharmonic = {1.0008 ** (i-1) * i: 1/(1.65**i) for i in range(1, 11)}
    inharmonic2 = {1.00081 ** (i-1) * i: 1/(1.75**i) for i in range(1, 11)}
    inharmonic3 = {1.00083 ** (i-1) * i: 1/(1.71**i) for i in range(1, 11)}
    percussive = {1.6 ** (i-1) * i: 1/(2**i) for i in range(1, 11)}


class EqualTempered(Enum):
    # By convention, C4 is 261.625HZ, A4 is 440 and C5 is 523.25.
    # (A labeling that started with A would probably make more sense, but convention wins.)
    C = 523.25/2 # 261.625
    Cs = Df = 554.37/2
    D = 587.33/2
    Ds = Ef = 622.25/2
    E = 659.25/2
    F = 698.46/2
    Fs = Gf = 739.99/2
    G = 783.99/2
    Gs = Af= 830.61/2
    A = 440.
    As = Bf = 466.16
    B = 493.88


def single_note(position, value):
    v = position * ((), ) + (value, ) + (11 - position) * ((), )
    return v,


HARMONIC_FIE = (11, 8)


equal_ratios = (tuple((_.value/261.625, 1) for _ in EqualTempered), )
symmetric_la = single_note(9, (27, 16))
harmonic_la = single_note(9, (13, 8))
subharmonic_ma = single_note(3, (7, 6))
subharmonic_fa = single_note(4, (4, 3))
harmonic_ratios = (((1, 1), (), (9, 8), (7, 6), (5, 4),  (), (),
                    (3, 2), (), (), (7, 4), (15, 8)), )
minor_ratios = (((1, 1), (28, 27), (9, 8), (7, 6), (5, 4),  (4, 3),
                 (17, 12), (3, 2), (14, 9), (27, 16), (7, 4), (15, 8)), )

pentatonic_ratios = (tuple(
    (
        (3 * 9 ** ((i+5)//2), 4 * 8**((i+5)//2))
        if i < 7 else (3 * 9 ** ((i-7)//2), 2 * 8 ** ((i -7)//2)))
    if (i % 2) else (9**(i//2), 8**(i//2)) for i in range(12)), )


class WesternTuning(object):
    positions = dict(
        # T
        Cf=-1,  # Cf4 == B3 (for discreetly tuned instruments; close for viola, trombone, etc.)
        C=0,  # Convention starts at C, not A.
        Cs=1,
        Df=1,
        D=2,
        Ds=3,
        Ef=3,
        E=4,
        Ff=4,
        Es=5,
        F=5,
        Fs=6,
        Gf=6,
        G=7,
        Gs=8,
        Af=8,
        A=9,
        As=10,
        Bf=10,
        B=11,
        Bs=12,  # Bs4 == C5
    )

    scale_positions = dict(
        C=0,
        D=1,
        E=2,
        F=3,
        G=4,
        A=5,
        B=6,
    )

    def __init__(self, key, tuning_preferences, renormalization=None):
        self.key, self.tonic = (key, EqualTempered[key].value) if isinstance(key, str) else key
        print('key', self.key, self.tonic)
        _flipped = {_v: _i for _i, _v in enumerate(EqualTempered)}
        self._notes = {_n: _flipped[_v] for _n, _v in EqualTempered.__members__.items()}
        if not isinstance(tuning_preferences[0][0], tuple):
            raise ValueError('Expected a list of tuning preferences not a single tuning')

        pitches = []
        for i in range(12):
            for tuning in tuning_preferences:
                if tuning[i]:
                    print(tuning[i])
                    n, d = tuning[i]
                    pitches.append(self.tonic * n / d)
                    break
            else:
                raise ValueError('Please add a more complete tuning to your tuning_preferences to fill gaps')
        n = self._notes[self.key]
        print(self._notes)
        self.pitches = [p/2 for p in pitches[-n:]] + pitches[:-n]
        if renormalization is not None and renormalization != self.key:
            adjustment = EqualTempered[renormalization].value / self[renormalization]
            self.pitches = [adjustment * p for p in self.pitches]

    def __getitem__(self, note_name):
        result = self.pitches[self._notes[note_name]]
        print(note_name, result)
        return result

    def __getattr__(self, item):
        return self[item]


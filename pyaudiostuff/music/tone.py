import pandas as pd
import numpy as np
from music import constants
from utils import decorator


class WmlnMeta(type):
    def __getattr__(cls, item):
        octave = int(item[-1])
        return cls(item[:-1], octave)


class BaseNoteObject(object):
    tuning = None

    def __init__(self, note, octave, duration=1, denom=1):
        self.note = note
        self.octave = octave
        self.duration = duration
        self.denom = denom

    @property
    def freq(self):
        return self.note * 2 ** (self.octave - 3)


class _BNO(BaseNoteObject):
    tuning = constants.WesternTuning('G', constants.minor_ratios, renormalization='G')

    def __init__(self, name, octave, duration=1, denom=1):
        self.name = name
        super(_BNO, self).__init__(self.tuning[name], octave, duration=duration, denom=denom)

    def distance(self, other):
        pass


class NamedTone(_BNO, metaclass=WmlnMeta):

    def __mul__(self, other):
        self.duration *= other
        return self

    def __rmul__(self, other):
        self.duration *= other
        return self

    def __truediv__(self, other):
        self.denom *= other
        return self

    def __add__(self, other):
        return MusicLine([self, other])


N = NamedTone


class MusicLine(object):
    def __init__(self, notes):
        self.notes = notes

    def __add__(self, other):
        if isinstance(other, NamedTone):
            self.notes.append(other)
        else:
            self.notes.extend(other)
        return self


melody = (
    2 * N.D5 + N.G4 + N.A4 + N.B4 + N.C5
    + 2 * N.D5 + 2 * N.G4 + 2 * N.G4
    + 2 * N.E5 + N.C5 + N.D5 + N.E5 + N.Fs5
    + 2 * N.G5 + 2 * N.G4 + 2 * N.G4
    + 2 * N.C5 + N.D5 + N.C5 + N.B4 + N.A4
    + 2 * N.B4 + N.C5 + N.B4 + N.A4 + N.G4
    + 2 * N.Fs4 + N.G4 + N.A4 + N.B4 + N.G4
    + 6 * N.B4 / 10 + 54 * N.A4 / 10
)


class Decay(object):
    def __init__(self, tone_factory):
        self.factory = tone_factory
        self.one_beat = tone_factory.tempo * tone_factory.framerate

    def get_decay(self, freq, beats, ampl=1.0, strength=1.0):
        pass



class ToneFactory(object):
    def __init__(self, width, framerate, tempo):
        self.width = width
        self._width = int(2 ** (width * 8 - 1) - 1)
        self.framerate = int(framerate)
        self.tempo = tempo

    @decorator.memoize_instance_method
    def get_linear_decay(self, beats, ampl=1.0, strength=1.0):
        suffix = pd.Series()
        length = int(self.tempo * self.framerate * beats)
        if beats > .4:
            intermediate = int(self.tempo * self.framerate * 2)
        else:
            intermediate = None
        if strength > 1.0:
            duration = int(1./strength * length)
            suffix = pd.Series(0, range(length - duration))
            length = duration
            strength = 1.0
        amplitude = pd.Series(np.nan, range(length))
        amplitude[0] = 0
        amplitude[200] = ampl
        if intermediate is None:
            amplitude[length - 1] = (ampl * (1 - strength))
        else:
            amplitude[intermediate] = ampl * (1 - strength)
            amplitude[length - 1] = (ampl * (1 - strength)) ** (beats/.4)
        return pd.concat([amplitude.interpolate(), suffix])

    @decorator.memoize_instance_method
    def render(self, freq, ampl, beats, filters=()):
        baseline = pd.Series(range(int(self.tempo * float(beats) * self.framerate)))
        tone = self._width * ampl * np.sin(freq * (baseline) * np.pi / self.framerate)

        for filter in filters:
            tone = filter(tone, freq, ampl, beats)

        if self.width == 1:
            return (tone + self._width)
        else:
            return tone


def normalize_values(harmonics):
    s = sum(harmonics.values())
    return {k: v/s for k, v in harmonics.items()} if harmonics else {1: 1}


def _use_id_for_series(x):
    return id(x) if isinstance(x, pd.Series) else x


class HToneFactory(ToneFactory):
    def __init__(self, width, framerate, tempo, harmonics, **kwargs):
        self.harmonics = normalize_values(harmonics)
        # noinspection PyArgumentList
        super().__init__(width, framerate, tempo, **kwargs)

    @decorator.memoize_instance_method(ampl=_use_id_for_series)
    def render(self, freq, ampl, beats, filters=()):
        tone = None
        for mult, strength in self.harmonics.items():
            t = super(HToneFactory, self).render(mult * freq, strength, beats, filters)
            if tone is None:
                tone = t
            else:
                tone += t

        return ampl * tone


class Combiner(object):
    def combine(self, primary, *secondaries):
        secondaries = [secondary.reindex(primary).iterpolate().fillna(0) for secondary in secondaries]
        secondary = sum(secondaries)
        result = primary + sum(secondary)
        result[result > 1] = 1.
        result[result < -1] = -1.
        return result


class DecayedCombiner(Combiner):
    def combine(self, primary, *secondaries):
        if len(secondaries) == 1:
            secondary = secondaries[0]
        else:
            secondary = self.combine(*secondaries)
        secondary = secondary.reindex(primary).interpolate().fillna(0)
        sign = pd.np.sign(primary)
        result = primary + secondary
        result[pd.np.sign(secondary) == sign] = sign * (1 - (1 - abs(primary)) * (1 - abs(secondary)))
        return result



def harsher(tone, *_):
    signs = (tone / tone.abs()).fillna(0)
    return np.sqrt(tone.abs().mean() * tone.abs()) * signs


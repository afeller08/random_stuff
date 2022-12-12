import wave
import time
import pyaudio
import numpy as np
from scipy.io import wavfile

from music import tone
from music import constants

SIZES = {1: np.uint8, 2: np.int16, 4: np.int32, 8: np.int64}


def test_case():
    tones = []
    harmonics = constants.Harmonics.inharmonic
    harmonics.update(constants.Harmonics.inharmonic2)
    harmonics.update(constants.Harmonics.inharmonic3)
    harmonics.update(constants.Harmonics.exp_decayed)
    f = tone.HToneFactory(2, 22050, 1, harmonics=harmonics)
    print('concatting notes')
    for note in tone.melody.notes:
        beats = note.duration * .25 / note.denom
        a = .3 + .08 * beats
        ampl = f.get_linear_decay(beats, a, .8)
        print(note.freq, beats, a)
        tone_ = f.render(note.freq, ampl, beats, )
        tones.append(tone_)
    song = np.concatenate(tones)
    print(len(song))
    play(f, song)


def play(tone_factory, notes):
    fn = "placeholder.wav"
    write_wave(tone_factory, notes, fn)
    play_wav(fn)


def write_wave(tone_factory, notes, filename):
    notes = np.array(notes, SIZES[tone_factory.width])
    wavfile.write(filename, tone_factory.framerate, notes)


def play_wav(filename):
    chunk = 1024 * 64

    f = wave.open(filename, "rb")
    p = pyaudio.PyAudio()
    print("width", f.getsampwidth())
    nframes = f.getnframes()
    print("frames", f.getframerate())
    stream = p.open(format=p.get_format_from_width(f.getsampwidth()),
                    channels=f.getnchannels(),
                    rate=f.getframerate(),
                    output=True)
    data = f.readframes(nframes)
    start = time.time()
    stream.write(data)

    stream.stop_stream()
    stream.close()
    print(time.time() - start)

    p.terminate()


test_case()

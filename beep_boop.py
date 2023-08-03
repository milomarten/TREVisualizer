from pygame import mixer
from pygame.mixer import Sound

enabled = True

mixer.init()
mixer.set_num_channels(16)

circle_of_fifths_major = [
    Sound(file="sounds/Piano.mf.C4.ogg"),
    Sound(file="sounds/Piano.mf.G4.ogg"),
    Sound(file="sounds/Piano.mf.D4.ogg"),
    Sound(file="sounds/Piano.mf.A4.ogg"),
    Sound(file="sounds/Piano.mf.E4.ogg"),
    Sound(file="sounds/Piano.mf.B4.ogg"),
    Sound(file="sounds/Piano.mf.Gb4.ogg"),
    Sound(file="sounds/Piano.mf.Db4.ogg"),
    Sound(file="sounds/Piano.mf.Ab5.ogg"),
    Sound(file="sounds/Piano.mf.Eb4.ogg"),
    Sound(file="sounds/Piano.mf.Bb4.ogg"),
    Sound(file="sounds/Piano.mf.F4.ogg"),
]

circle_of_fifths_minor = [
    Sound(file="sounds/Piano.mf.A4.ogg"),
    Sound(file="sounds/Piano.mf.E4.ogg"),
    Sound(file="sounds/Piano.mf.B4.ogg"),
    Sound(file="sounds/Piano.mf.Gb4.ogg"),
    Sound(file="sounds/Piano.mf.Db4.ogg"),
    Sound(file="sounds/Piano.mf.Ab5.ogg"),
    Sound(file="sounds/Piano.mf.Eb4.ogg"),
    Sound(file="sounds/Piano.mf.Bb4.ogg"),
    Sound(file="sounds/Piano.mf.F4.ogg"),
    Sound(file="sounds/Piano.mf.C4.ogg"),
    Sound(file="sounds/Piano.mf.G4.ogg"),
    Sound(file="sounds/Piano.mf.D4.ogg"),
]

[s.set_volume(0.4) for s in circle_of_fifths_minor]


def play_major(idx: int):
    if enabled:
        idx = idx % len(circle_of_fifths_major)
        circle_of_fifths_major[idx].play(maxtime=2000)


def play_minor(idx: int):
    if enabled:
        idx = idx % len(circle_of_fifths_minor)
        circle_of_fifths_minor[idx].play(maxtime=2000)
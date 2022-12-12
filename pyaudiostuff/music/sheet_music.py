import abc
import enum
import time
import typing

import pandas as pd
import pygame
import pygame.gfxdraw

from music.tone import NamedTone

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GRAY = (200, 200, 200)

BASE_C = pd.Series(range(7), index=(6, 8, 10, 11, 1, 3, 5))


class PrimaryConfig:
    def __init__(self, note_width, note_height, note_config):
        self.note_width = note_width
        self.note_height = note_height
        self.note_config = note_config


class BaseNoteConfig:
    def __init__(self, v_offset, h_offset):
        self.v_offset = v_offset
        self.h_offset = h_offset

    def adjust_position(self, x, y):
        return x + self.h_offset, y + self.v_offset

    def draw(self, note, h_position, staff):
        pass


class ExpectedPosition(enum.Enum):
    CenterV = "CenterVertical"
    CenterH = "CenterHorizontal"
    StemTip = "StemTip"


class EqualityMixin(object):
    def _eq_parts(self):
        raise NotImplementedError(type(self))

    def __hash__(self):
        return hash(self._eq_parts())

    def __eq__(self, other):
        if isinstance(other, EqualityMixin):
            return self._eq_parts() == other._eq_parts()
        return False


class Note(EqualityMixin):
    """
    The information about a note that is notation-independent
    """
    def __init__(self, named_tone, beat, duration, ornaments, dynamic):
        self.named_tone = named_tone
        self.beat = beat
        self.duration = duration
        self.ornaments = ornaments
        self.dynamic = dynamic

    def _eq_parts(self):
        return self.named_tone, self.beat

    @classmethod
    def from_note(cls, note: "Note") -> "Note":
        """
        Convenience for downgrading subclasses.
        """
        return cls(named_tone=note.named_tone,
                   beat=note.beat,
                   duration=note.duration,
                   ornaments=note.ornaments,
                   dynamic=note.dynamic)


class RenderableNote(Note):
    """
    A note with the voicing metadata required to render it.
    """
    def __init__(self, note: Note, clef, orientation):
        super().__init__(**note.__dict__)
        self.clef = clef
        self.orientation = orientation

    @property
    def clef_rank(self):
        return self.named_tone.rank - self.clef.baseline.rank

    @property
    def lined(self):
        if self.clef_rank % 2 == 0 and (self.clef_rank < 0 or self.clef_rank > 10):
            return True
        return False

    @classmethod
    def from_note(cls, note):
        return cls(note=Note.from_note(note), clef=note.clef, orientation=note.orirentation)


class MeasuredNote(RenderableNote):
    """
    A note that has been processed relative to its measure, and is ready to be displayed.
    """
    def __init__(self, note: Note, h_offset, accidental):
        super().__init__(**note.__dict__)
        self.h_offset = h_offset
        self.accidental = accidental

    @classmethod
    def from_note(cls, note: "MeasuredNote"):
        return cls(note=RenderableNote.from_note(note), h_offset=note.h_offset, accidental=note.accidental)


class MeasureBuilder:
    def __init__(self, notes: typing.List[RenderableNote], key, config):
        self.beats = sorted(set(x.beat for x in notes))
        raw_notes = {x: [] for x in beats}
        for note in notes:
            raw_notes[note.beat].append(note)
        self.effective_key = key
        self.effective_keys = dict((x.clef, key) for x in notes)


class Clefs(enum.Enum):
    Treble = 0
    Bass = 1


top_notes = {
    Clefs.Treble: NamedTone('F', 5),
    Clefs.Bass: NamedTone('A', 3)
}


class Screen(object):
    margin = 10
    staff_height = 100
    staffs_per_group = 2

    def __init__(self, width, height):
        """
        :param width: int
        :param height: int
        """
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        self.staves = []  # type: list[BaseStaff]
        self.clock = pygame.time.Clock()
        self.width = width
        self.height = height
        self._fonts = {}

    def run(self):
        self.clock.tick(10)
        self.draw()

    def draw(self):
        self.screen.fill(WHITE)
        for staff in self.staves:
            staff.draw(self.screen)
        pygame.display.flip()


class BaseStaff(object, metaclass=abc.ABCMeta):
    sub_staves = []
    staves = 1
    white_space = 1

    def __init__(self, left, top, width, staff_height):
        self.left = left
        self.right = self.left + width
        self.top = top
        self.bottom = self.top + (self.staves + (self.staves - 1) * self.white_space) * staff_height
        self.staff_height = staff_height
        self.space = int(staff_height // 4)
        self.note_width = int(1.5 * self.space)
        self.width = width
        self.notes = [1, 2, 3, 13, 6, 8, 10, 9, 4, 3, 2]  # Placeholder, should be typed

    def draw_veritical_line(self, screen, position):
        pygame.draw.line(screen, BLACK, (position, self.top), (position, self.bottom))

    def draw_caps(self, screen):
        for side in [self.left, self.right]:
            self.draw_veritical_line(screen, side)

    def draw_staves(self, screen):
        for stave in self.sub_staves:
            for i in range(5):
                top = stave.top + self.space * i
                pygame.draw.line(screen, BLACK, (stave.left, top), (stave.right, top))

    def draw(self, screen):
        self.draw_staves(screen)
        self.draw_caps(screen)
        for i, note in enumerate(self.notes):
            print(note)
            self.draw_note(screen, note, i * 60, 1,)

    @abc.abstractmethod
    def draw_note(self, screen, note, offset, beats, accidental=0, up=True, sub_staff=0):
        pass


class Staff(BaseStaff):
    staves = 1

    def __init__(self, left, top, width, staff_height, clef):
        super().__init__(left, top, width, staff_height)
        self.clef = clef

    @property
    def sub_staves(self):
        return [self]

    def draw(self, screen):
        super(Staff, self).draw(screen)

    def draw_note(self, screen, note, offset, beats, accidental=0, up=True, sub_staff=0):
        space = self.space
        vert_mid = self.top + int(space * note/2)
        rendered_note = DottedHalfNote(offset, vert_mid, self.note_width, self.space)
        rendered_note.draw(screen)
        rendered_note.finalize(screen)
        overhang = rendered_note.overhang * rendered_note.width
        o_left = rendered_note.left - overhang
        o_right = rendered_note.right + overhang
        for y in range(self.bottom, rendered_note.bottom, space):
            pygame.draw.line(screen, rendered_note.color, (o_left, y), (o_right, y))
        for y in range(self.top, rendered_note.top, -space):
            pygame.draw.line(screen, rendered_note.color, (o_left, y), (o_right, y))


def light_color(color):
    return LIGHT_GRAY


class Orientations(enum.Enum):
    DownRight = 0
    DownLeft = 1
    Left = 1
    UpRight = 2
    Up = 2
    UpLeft = 3
    

class RenderedNote:
    overhang = .15
    dot_distance = .35
    dot_offset = .25
    center_offset = 0
    stem_multiplier = 3

    def __init__(self, x, y, width, height, orientation=Orientations.UpRight, color=BLACK, ornaments=()):
        self.x = x
        self.y = y + self.center_offset
        self.width = width
        self.height = height
        self.orientation = orientation
        self.color = color
        x_rad = int(width/2)
        y_rad = int(height/2)
        self.x_rad = x_rad
        self.y_rad = y_rad
        self.left = x - x_rad
        self.right = x + x_rad
        self.top = y - y_rad
        self.bottom = y + y_rad
        self.ornaments = ()
        self.gfx_elipse_args = (x, y, x_rad, y_rad)
        self.rect_args = ((self.left, self.top), (width, height))
        if orientation.value & Orientations.Left.value:
            self.stem_base = self.left, y
        else:
            self.stem_base = self.right, y
        if orientation.value & Orientations.Up.value:
            self.stem_tip = self.stem_base[0], y - self.stem_multiplier * self.height
        else:
            self.stem_tip = self.stem_base[0], y + self.stem_multiplier * self.height

    def draw_elipse(self, screen):
        pygame.gfxdraw.aaellipse(screen, *self.gfx_elipse_args, self.color)

    def draw_stem(self, screen):
        pygame.draw.line(screen, self.color, self.stem_base, self.stem_tip)

    def draw_extra(self, screen):
        pass
    
    def draw_ornaments(self, screen):
        pass

    def draw(self, screen):
        self.draw_elipse(screen)
        self.draw_extra(screen)
        self.draw_ornaments(screen)

    def finalize(self, screen):
        self.draw_stem(screen)


class WholeNote(RenderedNote):
    def draw_stem(self):
        pass


class HalfNote(RenderedNote):
    pass


class QuarterNote(RenderedNote):
    def draw_elipse(self, screen):
        super().draw_elipse(screen)
        pygame.gfxdraw.filled_ellipse(screen, *self.gfx_elipse_args, self.color)
        

class _DottedNote(RenderedNote):
    def draw_extra(self, screen):
        super().draw_extra(screen)
        distance = int(self.dot_distance * self.width)
        offset = int(self.dot_offset * self.height)
        # LoL
        pygame.gfxdraw.filled_circle(screen, self.right + distance, self.y + offset, 1, self.color)


class DottedWholeNote(WholeNote, _DottedNote):
    pass

class DottedQuarterNote(QuarterNote, _DottedNote):
    pass


class DottedHalfNote(HalfNote, _DottedNote):
    pass


class FlagNote(QuarterNote):
    pass


class DottedFlagNote(FlagNote, _DottedNote):
    pass


class GreatStaff(BaseStaff):
    staves = 2

    def __init__(self, left, top, width, staff_height):
        super().__init__(left, top, width, staff_height)
        self.sub_staves = [
            Staff(left, top + int((1 + self.white_space) * i * staff_height), width, staff_height, Clefs(i))
            for i in range(self.staves)]

    def draw(self, screen):
        super(GreatStaff, self).draw(screen)

    def draw_note(self, screen, note, offset, beats, accidental=0, up=True, sub_staff=0):
        self.sub_staves[sub_staff].draw_note(screen, note, offset, beats, accidental)


screen = Screen(800, 600)
screen.staves.append(GreatStaff(20, 20, 760, 36))
screen.draw()
running = True
while running:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.KEYDOWN:
            print(event.key)
            if event.key == pygame.K_x:
                running = False
            elif event.key == pygame.K_r:
                screen = Screen(800, 600)
                screen.staves.append(GreatStaff(20, 200, 760, 36))
                screen.draw()

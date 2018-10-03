import abc
import enum
import time

import pandas as pd
import pygame
import pygame.gfxdraw

from player.tone import WesternNote

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

BASE_C = pd.Series(range(7), index=(6, 8, 10, 11, 1, 3, 5))


class Clefs(enum.Enum):
    Treble = 0
    Bass = 1


top_notes = {
    Clefs.Treble: WesternNote('F', 5),
    Clefs.Bass: WesternNote('A', 3)
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

    def run(self):
        self.clock.tick(10)
        self.draw()

    def draw(self):
        self.screen.fill(WHITE)
        for staff in self.staves:
            staff.draw(self.screen)
        pygame.display.flip()


class Note(object):
    def __init__(self, ):
        pass


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
        self.notes = [1]  # Placeholder, should be typed

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
        for note in self.notes:
            self.draw_note(screen, note, 60, 1,)

    @abc.abstractmethod
    def draw_note(self, screen, note, offset, beats, accidental=0, up=True, skew=0, sub_staff=0):
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

    def draw_note(self, screen, note, offset, beats, accidental=0, up=True, skew=0, sub_staff=0):
        note_shift = 4 # place holder
        space = self.space
        vert_mid = self.top + int(space * note_shift/2)
        top = vert_mid + 1
        left = int(self.left + offset)
        right = int(left + self.note_width) - 2
        rect = pygame.Rect((left, top), (self.note_width, space))
        pygame.draw.ellipse(screen, BLACK, rect, 0 if beats < 2 else 2)
        pygame.gfxdraw.filled_ellipse(screen, left+100, top, int(self.note_width/2), int(space/2), BLACK)
        pygame.gfxdraw.aaellipse(screen, left+100, top, int(self.note_width/2), int(space/2), BLACK)
        if beats < 4:
            midpoint = int(top + space/2)
            if up:
                pygame.draw.line(screen, BLACK, (right, midpoint), (right, int(top - 3 * space)))
            else:
                pygame.draw.line(screen, BLACK, (left, midpoint), (left, int(top + 3 * space)))
        if note_shift % 2 == 0 and (note_shift < 0 or note_shift > 4):
            extention = int(.2 * self.note_width)
            pygame.draw.line(screen, BLACK, (left - extention, vert_mid), (right + extention, vert_mid))



class GreatStaff(BaseStaff):
    staves = 2

    def __init__(self, left, top, width, staff_height):
        super().__init__(left, top, width, staff_height)
        self.sub_staves = [
            Staff(left, top + int((1 + self.white_space) * i * staff_height), width, staff_height, Clefs(i))
            for i in range(self.staves)]

    def draw(self, screen):
        super(GreatStaff, self).draw(screen)

    def draw_note(self, screen, note, offset, beats, accidental=0, up=True, skew=0, sub_staff=0):
        self.sub_staves[sub_staff].draw_note(screen, note, offset, beats, accidental)


screen = Screen(800, 600)
screen.staves.append(GreatStaff(20, 20, 760, 36))
screen.draw()
time.sleep(25)

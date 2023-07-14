import curses
import _curses

from typing import Callable, TypeVar

from acurses.keyhandler import KeyHandler
from acurses.io import align_style_print, fill_line_attr
from acurses.input_line import InputLine

T = TypeVar("T")

class SelectFromList(KeyHandler):
    choices: list[T]
    is_match: list[bool]
    head_str: str
    foot_str: str
    pad: _curses.window
    pad_scroll: int
    cursor_pos: int
    PAD_DISP_HEIGHT: int
    SCROLL_THRESHOLD: int

    def init_keybinds(self) -> None:
        self.keybind_map = \
        {
            'h': self.no_selection,
            'q': self.no_selection,
            'j': self.move_down,
            'k': self.move_up,
            '/': self.search,
            'n': self.next_match,
            'N': self.prev_match,
            'f': lambda: self.screen_down(curses.LINES - 4),
            'b': lambda: self.screen_up(curses.LINES - 4),
            'd': lambda: self.screen_down((curses.LINES - 4) // 2),
            'u': lambda: self.screen_up((curses.LINES - 4) // 2),
            'g': lambda: self.screen_up(1e18), # go to top
            'G': lambda: self.screen_down(1e18), # go to bottom
            'l': lambda: True,
        }

        self.keys_handled_by_parent = [':']

    def __init__(self,
        mm,
        parent: KeyHandler,
        prompt: str,
        choices: list[T],
        elem_to_strs: Callable[[T], tuple[str, str, str]],
        elem_is_match: Callable[[T, str], bool] = lambda e, s: False,
        keybind_help = "hq=back  jk=navigate  l=select"):

        self.mm = mm
        self.parent = parent

        self.head_str = f"{prompt}  |  {keybind_help}"
        self.foot_str = ""

        self.choices = choices
        self.is_match = [False for c in choices]
        self.elem_to_strs = elem_to_strs
        self.elem_is_match = elem_is_match

        self.pad = curses.newpad(len(self.choices), curses.COLS)
        self.pad_scroll = 0
        self.cursor_pos = 0
        self.PAD_DISP_HEIGHT = curses.LINES - 4
        self.SCROLL_THRESHOLD = max(1, curses.LINES // 6)

        self.init_keybinds()

    def draw_pad(self) -> None:
        self.pad.clear()

        for i, elem in enumerate(self.choices):
            attr = "normal"
            if i == self.cursor_pos:
                attr = "so"
                fill_line_attr(self.pad, i, curses.A_STANDOUT)

            left, center, right = self.elem_to_strs(elem)

            if i < self.pad_scroll or i > self.pad_scroll + self.PAD_DISP_HEIGHT:
                continue # don't print elems off of window

            align_style_print(self.pad, i, 1, f"<{attr}> {left}</{attr}>")
            align_style_print(self.pad, i, 2, f"<{attr}>{center}</{attr}>")
            align_style_print(self.pad, i, 3, f"<{attr}>{right} </{attr}>")

    def move_down(self) -> None:
        """Increment self.cursor_pos if possible, incrementing pad_scroll if
        necessary"""
        if self.cursor_pos != len(self.choices) - 1:
            self.cursor_pos += 1

        past_threshold = self.cursor_pos > self.pad_scroll + self.PAD_DISP_HEIGHT - self.SCROLL_THRESHOLD
        elem_off_screen = len(self.choices) > self.pad_scroll + self.PAD_DISP_HEIGHT

        if past_threshold and elem_off_screen:
            self.pad_scroll += 1

    def move_up(self) -> None:
        """Decrement self.cursor_pos if possible, decrementing pad_scroll if
        necessary"""
        if self.cursor_pos != 0:
            self.cursor_pos -= 1

        if self.cursor_pos < self.pad_scroll + self.SCROLL_THRESHOLD and self.pad_scroll > 0:
            self.pad_scroll -= 1

    def screen_down(self, count: int) -> None:
        """Increment self.pad_scroll and self.cursor_pos, if possible, up to the
        given count"""
        pad_inc = min(count, len(self.choices) - (self.pad_scroll + self.PAD_DISP_HEIGHT))
        cursor_inc = min(count, len(self.choices) - 1 - self.cursor_pos)

        self.pad_scroll += pad_inc
        self.cursor_pos += cursor_inc

    def screen_up(self, count: int) -> None:
        """Decrement self.pad_scroll and self.cursor_pos, if possible, up to the
        given count"""
        pad_dec = min(count, self.pad_scroll)
        cursor_dec = min(count, self.cursor_pos)

        self.pad_scroll -= pad_dec
        self.cursor_pos -= cursor_dec

    def refresh_pad(self) -> None:
        self.pad.refresh(self.pad_scroll, 0, 2, 0, curses.LINES - 3, curses.COLS - 1)

    def redraw(self) -> None:
        self.mm.redraw_scr(self.head_str, self.foot_str)

    def mainloop(self) -> None:
        self.redraw()

        while True:
            self.pad.clear()
            self.draw_pad()
            self.refresh_pad()

            if self.handle_key(self.mm.scr.getch()):
                break

        # clear pad before returning
        self.pad.erase()
        self.refresh_pad()

    def no_selection(self) -> bool:
        self.cursor_pos = -1
        return True

    def get_selection(self) -> T:
        return None if self.cursor_pos == -1 else self.choices[self.cursor_pos]

    def set_choices(self, choices: list[T]):
        assert(len(choices) == len(self.choices)) # can't change height of pad

        self.choices = choices

    def search(self) -> None:
        def update(query: str) -> None:
            query = query[1:] # ignore '/'
            for i, elem in enumerate(self.choices):
                self.is_match[i] = self.elem_is_match(elem, query)

            # go to next match
            self.next_match(0)
            self.pad.clear()
            self.draw_pad()
            self.refresh_pad()

        update(InputLine(self.mm, "", "/", True, update).out())

    def next_match(self, offset: int = 1) -> None:
        for i in range(offset, offset + len(self.choices)):
            if self.is_match[(self.cursor_pos + i) % len(self.choices)]:
                target = (self.cursor_pos + i) % len(self.choices)
                diff = target - self.cursor_pos

                if diff < 0:
                    self.screen_up(-diff)
                else:
                    self.screen_down(diff)

                return

        self.mm.set_foot("<red>No match found</red>")

    def prev_match(self, offset: int = 1) -> None:
        for i in range(offset, len(self.choices) + offset):
            if self.is_match[(self.cursor_pos - i) % len(self.choices)]:
                target = (self.cursor_pos - i) % len(self.choices)
                diff = target - self.cursor_pos

                if diff < 0:
                    self.screen_up(-diff)
                else:
                    self.screen_down(diff)
                return

        self.mm.set_foot("<red>No match found</red>")

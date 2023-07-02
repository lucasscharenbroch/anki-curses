import curses
import _curses

from anki import decks_pb2
from anki.collection import Collection
from anki.decks import DeckManager

from acurses.keyhandler import KeyHandler
from acurses.io import align_style_print, fill_line_attr
from acurses.reviewer import Reviewer

DeckNameId = decks_pb2.DeckNameId
DeckTreeNode = decks_pb2.DeckTreeNode

class DeckManager(KeyHandler):
    col: Collection
    deck_list: list[tuple[str, int, tuple[int, int, int]]]
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
            'q': lambda: True, # quit
            'j': self.move_down,
            'k': self.move_up,
            'l': self.study,
            'L': self.study_all,
        }

        self.keys_handled_by_parent = [':']

    def __init__(self, mm, col: Collection):
        self.mm = mm
        self.parent = mm

        self.col = col
        self.deck_list = [(nameid.name, nameid.id, self.get_deck_counts(nameid)) 
                          for nameid in self.col.decks.all_names_and_ids(skip_empty_default = True)]

        self.head_str = "Deck Manager |  q=quit  jk=navigate  l=study  L=study-all"
        self.foot_str = ""

        self.pad = curses.newpad(len(self.deck_list), curses.COLS)
        self.pad_scroll = 0
        self.cursor_pos = 0
        self.PAD_DISP_HEIGHT = curses.LINES - 4
        self.SCROLL_THRESHOLD = max(1, curses.LINES // 6)

        self.init_keybinds()

    def get_deck_counts(self, deck: DeckNameId) -> tuple[int, int, int]:
        self.col.decks.set_current(deck.id)
        self.col.sched.reset()
        return self.col.sched.counts()

    def draw_pad(self) -> None:
        self.pad.clear()

        for i, deck in enumerate(self.deck_list):
            attr = "normal"
            if i == self.cursor_pos:
                attr = "so"
                fill_line_attr(self.pad, i, curses.A_STANDOUT)

            new, lrn, rev = deck[2]
            count_str = f"<{attr}><blue>{new}</blue> <red>{lrn}</red> <green>{rev}</green> </{attr}>"

            name = deck[0]

            align_style_print(self.pad, i, 1, f"<{attr}> {name}</{attr}>")
            align_style_print(self.pad, i, 3, count_str)

    def move_down(self) -> None:
        if self.cursor_pos != len(self.deck_list) - 1:
            self.cursor_pos += 1

        past_threshold = self.cursor_pos > self.pad_scroll + self.PAD_DISP_HEIGHT - self.SCROLL_THRESHOLD
        deck_off_screen = len(self.deck_list) > self.pad_scroll + self.PAD_DISP_HEIGHT

        if past_threshold and deck_off_screen:
            self.pad_scroll += 1

        self.draw_pad()
        self.refresh_pad()

    def move_up(self) -> None:
        if self.cursor_pos != 0:
            self.cursor_pos -= 1

        if self.cursor_pos < self.pad_scroll + self.SCROLL_THRESHOLD and self.pad_scroll > 0:
            self.pad_scroll -= 1

        self.draw_pad()
        self.refresh_pad()

    def refresh_pad(self) -> None:
        self.pad.refresh(self.pad_scroll, 0, 2, 0, curses.LINES - 3, curses.COLS - 1)

    def mainloop(self) -> None:
        self.mm.redraw_scr(self.head_str, self.foot_str)

        while True:
            self.mm.set_head(self.head_str)
            self.mm.set_foot(self.foot_str)
            self.draw_pad()
            self.refresh_pad()

            if self.handle_key(self.mm.scr.getch()):
                break

    def study(self) -> None:
        Reviewer(self, [self.cursor_pos]).mainloop()
        self.mm.redraw_scr(self.head_str, self.foot_str)

    def study_all(self) -> None:
        all_decks = []
        for i, deck in enumerate(self.deck_list):
            if deck[2] != (0, 0, 0):
                all_decks.append(i)

        Reviewer(self, all_decks).mainloop()
        self.mm.redraw_scr(self.head_str, self.foot_str)

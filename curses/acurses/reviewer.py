import _curses
import curses

from textwrap import fill

from anki.collection import Collection
from anki.cards import Card

from acurses.io import align_style_print, fill_line, fill_line_attr
from acurses.keyhandler import KeyHandler
from acurses.html import CardHtmlParser

PAD_HEIGHT = 1000

CARD_TYPE_NEW = 0
CARD_TYPE_LRN = 1
CARD_TYPE_REV = 2

AGAIN = 1
HARD = 2
EASY = 3
GOOD = 4

class Reviewer(KeyHandler):
    col: Collection
    deck_queue: list[int]
    q_idx: int
    head_str: str
    foot_str: str
    pad: _curses.window
    pad_scroll: int
    lines_displayed: int
    card: Card
    answer_displayed: bool
    PAD_DISP_HEIGHT: int

    def init_keybinds(self) -> None:
        self.keybind_map = \
        {
            'H' : lambda s: True,
            'q' : lambda s: True,
            ' ' : Reviewer.flip,
            'a' : lambda s: s.answer_card(AGAIN),
            '1' : lambda s: s.answer_card(AGAIN),
            'h' : lambda s: s.answer_card(HARD),
            '2' : lambda s: s.answer_card(HARD),
            '3' : lambda s: s.answer_card(GOOD),
            'g' : lambda s: s.answer_card(GOOD),
            '4' : lambda s: s.answer_card(EASY),
            'e' : lambda s: s.answer_card(EASY),
            'j': Reviewer.scroll_down,
            'k': Reviewer.scroll_up,
        }

    def __init__(self, dm, deck_queue: list[int]):
        self.dm = dm
        self.parent = None
        self.mm = dm.mm
        self.col = dm.col

        self.pad = curses.newpad(PAD_HEIGHT, curses.COLS)
        self.pad_scroll = 0
        self.lines_displayed = 0
        self.PAD_DISP_HEIGHT = curses.LINES - 6

        self.head_str = "Reviewer |  Hq=back  <space>=flip  jk=scroll  1a=again  2h=hard  3g=good  4e=easy"
        self.foot_str = ""

        self.deck_queue = deck_queue
        self.deck_list = self.dm.deck_list

        self.init_keybinds()

    def refresh_pad(self) -> None:
        self.pad.refresh(self.pad_scroll, 0, 4, 0, curses.LINES - 3, curses.COLS - 1)

    def scroll_down(self) -> None:
        if self.pad_scroll + self.PAD_DISP_HEIGHT < self.lines_displayed:
            self.pad_scroll += 1
        self.refresh_pad()

    def scroll_up(self) -> None:
        if self.pad_scroll > 0:
            self.pad_scroll -= 1
        self.refresh_pad()

    def display_header(self):
        "Prints deck name and counts on the first line of the main window"
        fill_line(self.mm.mw, 0, char = " ")

        new, lrn, rev = self.col.sched.counts()

        if self.card.type == CARD_TYPE_NEW:
            count_str = f"<ul><blue>{new}</blue></ul> <red>{lrn}</red> <green>{rev}</green> "
        elif self.card.type == CARD_TYPE_LRN:
            count_str = f"<blue>{new}</blue> <ul><red>{lrn}</red></ul> <green>{rev}</green> "
        else:
            count_str = f"<blue>{new}</blue> <red>{lrn}</red> <ul><green>{rev}</green></ul> "

        align_style_print(self.mm.mw, 0, 1, f" [deck {1 + self.q_idx} of {len(self.deck_queue)}]")
        align_style_print(self.mm.mw, 0, 2, f"<ul>{self.deck_list[self.deck_queue[self.q_idx]][0]}</ul>")
        align_style_print(self.mm.mw, 0, 3, count_str)

        fill_line(self.mm.mw, 1, char = "~")
        self.mm.mw.refresh()

    def flip(self):
        if self.answer_displayed:
            self.display_question()
        else:
            self.display_answer()

    def display_wrapped_string(self, s: str):
        lines = fill(s, width = curses.COLS, expand_tabs = False, replace_whitespace = False,
                                               drop_whitespace = False).split("\n")

        self.pad_scroll = 0
        self.lines_displayed = len(lines)

        self.pad.clear()

        for i, line in enumerate(lines):
            align_style_print(self.pad, i, 2, line)

        self.refresh_pad()

    def display_question(self):
        "Prints the question onto the pad"

        self.answer_displayed = False
        self.display_wrapped_string(CardHtmlParser.parse(self.card.question()))

    def display_answer(self):
        "Prints the answer onto the pad"

        self.answer_displayed = True
        self.display_wrapped_string(CardHtmlParser.parse(self.card.answer()))

    def answer_card(self, ease: int) -> None:
        assert 1 <= ease <= 4
        self.col.sched.answerCard(self.card, ease)

        idx = self.deck_queue[self.q_idx]
        self.deck_list[idx] = (*self.deck_list[idx][0:2], self.col.sched.counts())
        self.next_card()

    def next_card(self) -> None:
        self.card = self.col.sched.getCard()
        if self.card is None:
            return
        self.display_header()
        self.display_question()

    def study_decks_in_queue(self) -> None:
        for q_idx, idx in enumerate(self.deck_queue):
            self.q_idx = q_idx
            self.col.decks.set_current(self.deck_list[idx][1])
            self.col.sched.reset()
            self.next_card()

            while self.card != None:
                if self.handle_key(self.mm.scr.getch()):
                    return

    def mainloop(self) -> None:
        self.mm.redraw_scr(self.head_str, self.foot_str)

        self.study_decks_in_queue()
        self.col.save()

import _curses
import curses

from textwrap import wrap

from anki.collection import Collection
from anki.cards import Card

from acurses.io import align_style_print, align_style_print_block, fill_line, fill_line_attr
from acurses.keyhandler import KeyHandler
from acurses.html import CardParser, NoteParser
from acurses.wrappers import DeckInfo

PAD_HEIGHT = 1000

CARD_TYPE_NEW = 0
CARD_TYPE_LRN = 1
CARD_TYPE_REV = 2

AGAIN = 1
HARD = 2
GOOD = 3
EASY = 4

class Reviewer(KeyHandler):
    col: Collection
    deck_queue: list[int]
    deck_list: list[DeckInfo]
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
            'H': lambda: True,
            'q': lambda: True,
            ' ': self.flip,
            'a': lambda: self.answer_card(AGAIN),
            '1': lambda: self.answer_card(AGAIN),
            'h': lambda: self.answer_card(HARD),
            '2': lambda: self.answer_card(HARD),
            '3': lambda: self.answer_card(GOOD),
            'g': lambda: self.answer_card(GOOD),
            '4': lambda: self.answer_card(EASY),
            'e': lambda: self.answer_card(EASY),
            'j': self.scroll_down,
            'k': self.scroll_up,
            'v': self.edit_note,
        }

        self.keys_handled_by_parent = [':']

    def __init__(self, dm, deck_queue: list[int]):
        self.dm = dm
        self.parent = dm
        self.mm = dm.mm
        self.col = dm.col

        self.pad = curses.newpad(PAD_HEIGHT, curses.COLS)
        self.pad_scroll = 0
        self.lines_displayed = 0
        self.PAD_DISP_HEIGHT = curses.LINES - 6

        self.head_str = "Reviewer  |  Hq=back  <space>=flip  jk=scroll  1a=again  2h=hard  3g=good  4e=easy  v=edit-note"
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

    def curr_deck_cards_remaining(self) -> tuple[int, int, int]:
        """Returns the (new, learn, review) count sum across all decks in the queue"""
        pass

    def display_header(self):
        """Prints deck name and counts on the first line of the main window"""
        fill_line(self.mm.mw, 0, char = " ")

        new, lrn, rev = self.deck_list[self.deck_queue[0]].counts

        # totals
        tnew = sum([self.deck_list[i].counts[0] for i in self.deck_queue])
        tlrn = sum([self.deck_list[i].counts[1] for i in self.deck_queue])
        trev = sum([self.deck_list[i].counts[2] for i in self.deck_queue])

        if self.card.type == CARD_TYPE_NEW:
            count_str = f"<u><blue>{new}</blue></u> <red>{lrn}</red> <green>{rev}</green> "
        elif self.card.type == CARD_TYPE_LRN:
            count_str = f"<blue>{new}</blue> <u><red>{lrn}</red></u> <green>{rev}</green> "
        else:
            count_str = f"<blue>{new}</blue> <red>{lrn}</red> <u><green>{rev}</green></u> "

        remaining_str = f" [{len(self.deck_queue)} deck{'s' if len(self.deck_queue) > 1 else ''} " \
                        f"remaining (<blue>{tnew}</blue> <red>{tlrn}</red> <green>{trev}</green>)]"

        deck_name_str = self.col.decks.name(self.card.did)

        align_style_print(self.mm.mw, 0, 1, remaining_str)
        align_style_print(self.mm.mw, 0, 2, f"<u>{deck_name_str}</u>")
        align_style_print(self.mm.mw, 0, 3, count_str)

        fill_line(self.mm.mw, 1, char = "~")
        self.mm.mw.refresh()

    def flip(self):
        if self.answer_displayed:
            self.display_question()
        else:
            self.display_answer()

    def display_wrapped_string(self, s: str):
        lines = []

        for l in s.strip().split("\n"):
            if len(l) < curses.COLS:
                lines.append(l)
            else:
                lines += wrap(l, width = curses.COLS, expand_tabs = False,
                                 replace_whitespace = False, drop_whitespace = False)

        self.pad_scroll = 0
        self.lines_displayed = len(lines)

        self.pad.clear()

        align_style_print_block(self.pad, 0, 2, lines)

        self.refresh_pad()

    def display_question(self):
        "Prints the question onto the pad"

        self.answer_displayed = False
        self.display_wrapped_string(CardParser.parse(self.card.question()))

    def display_answer(self):
        "Prints the answer onto the pad"

        self.answer_displayed = True
        self.display_wrapped_string(CardParser.parse(self.card.answer()))

    def answer_card(self, ease: int) -> None:
        assert 1 <= ease <= 4
        self.col.sched.answerCard(self.card, ease)

        idx = self.deck_queue[0]
        self.deck_list[idx].counts = self.col.sched.counts()
        self.next_card()

    def next_card(self) -> None:
        self.card = self.col.sched.getCard()

        if self.card is None:
            return

        self.display_header()
        self.display_question()

    def edit_note(self) -> None:
        self.mm.edit_note(self.card.note())
        self.card.load()
        self.display_header()
        self.display_question()

    def study_decks_in_queue(self) -> None:
        while self.deck_queue:
            idx = self.deck_queue[0]
            self.col.decks.set_current(self.deck_list[idx].id)
            self.col.sched.reset()
            self.next_card()

            while self.card != None:
                if self.handle_key(self.mm.scr.getch()):
                    return

            self.deck_queue.pop(0)

    def redraw(self) -> None:
        self.mm.redraw_scr(self.head_str, self.foot_str)
        self.display_header()
        self.display_answer() if self.answer_displayed else self.display_question()

    def mainloop(self) -> None:
        self.mm.redraw_scr(self.head_str, self.foot_str)
        self.study_decks_in_queue()

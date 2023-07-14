from anki import decks_pb2
from anki.collection import Collection
from anki.decks import DeckManager

from acurses.keyhandler import KeyHandler
from acurses.io import align_style_print, fill_line_attr
from acurses.reviewer import Reviewer
from acurses.wrappers import DeckInfo
from acurses.select_from_list import SelectFromList

DeckNameId = decks_pb2.DeckNameId
DeckTreeNode = decks_pb2.DeckTreeNode

class DeckManager(SelectFromList):
    col: Collection
    deck_list: list[DeckInfo]

    def init_keybinds(self) -> None:
        super().init_keybinds()

        self.keybind_map |= \
        {
            'l': self.study,
            'L': self.study_all,
            'r': self.refresh_deck_list,
        }

        del self.keybind_map['h'] # don't quit on 'h' press

    def __init__(self, mm, col: Collection):
        self.col = col
        self.mm = mm

        self.init_deck_list()

        super().__init__(mm, mm, "Deck Manager", self.deck_list, self.deck_info_to_strs,
                         lambda d, s: s in d.name, "q=quit  jk=navigate  l=study  L=study-all  r=refresh")

    def init_deck_list(self):
        self.deck_list = [DeckInfo(nameid.name, nameid.id, self.get_deck_counts(nameid))
                          for nameid in self.col.decks.all_names_and_ids(skip_empty_default = True)]

        if self.mm.conf.hide_child_decks:
            self.deck_list = list(filter(lambda d: "::" not in d.name, self.deck_list))

    def refresh_deck_list(self):
        self.init_deck_list()
        self.set_choices(self.deck_list)

    def get_deck_counts(self, deck: DeckNameId) -> tuple[int, int, int]:
        self.col.decks.set_current(deck.id)
        self.col.sched.reset()
        return self.col.sched.counts()

    def deck_info_to_strs(self, deck: DeckInfo) -> tuple[str, str, str]:
        new, lrn, rev = deck.counts
        count_str = f"<blue>{new}</blue> <red>{lrn}</red> <green>{rev}</green>"
        name = deck.name

        return (name, "", count_str)

    def study(self) -> None:
        Reviewer(self, [self.cursor_pos]).mainloop()
        self.mm.redraw_scr(self.head_str, self.foot_str)

    def study_all(self) -> None:
        all_decks = []
        for i, deck in enumerate(self.deck_list):
            if deck.counts != (0, 0, 0):
                all_decks.append(i)

        Reviewer(self, all_decks).mainloop()
        self.mm.redraw_scr(self.head_str, self.foot_str)

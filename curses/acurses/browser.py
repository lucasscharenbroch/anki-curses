from typing import Sequence

from anki.notes import Note, NoteId
from anki.collection import Collection

from acurses.keyhandler import KeyHandler
from acurses.select_from_list import SelectFromList
from acurses.html import NoteParser
from acurses.wrappers import NoteInfo

class NoteBrowser(SelectFromList):
    col: Collection
    note_list: list[NoteInfo]

    def init_keybinds(self) -> None:
        super().init_keybinds()

        self.keybind_map |= \
        {
            'l': self.edit_current,
        }

    def __init__(self, mm, col: Collection, note_ids: Sequence[NoteId]):
        self.col = col
        self.mm = mm

        self.note_list = [NoteInfo(self.col, self.col.get_note(id)) for id in note_ids]

        super().__init__(mm, mm, f"Select a Note to edit ({len(self.note_list)} matches)",
                         self.note_list, self.note_info_to_strs, lambda n, s: any([s in f for f in n.fields]))

    def note_info_to_strs(self, note: NoteInfo) -> tuple[str, str, str]:
        return (note.field_str, "", note.deck_str)

    def edit_current(self) -> None:
        note_obj = self.note_list[self.cursor_pos].note_obj
        self.mm.edit_note(note_obj)
        self.note_list[self.cursor_pos] = NoteInfo(self.col, note_obj)

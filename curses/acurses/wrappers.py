import curses
import html

from anki.decks import DeckId
from anki.notes import Note
from anki.collection import Collection

from acurses.html import NoteParser

class DeckInfo:
    name: str
    id: DeckId
    counts: tuple[int, int, int]

    def __init__(self, name: str, id: int, counts: tuple[int, int, int]):
        self.name = name
        self.id = id
        self.counts = counts

class NoteInfo:
    note_obj: Note
    fields: list[str]
    field_str: str
    deck_str: str

    def __init__(self, col: Collection, note_obj: Note):
        self.note_obj = note_obj

        self.fields = list(self.note_obj.values())

        field_str = " / ".join([NoteParser.decode(f) for f in self.fields])
        field_str = field_str.replace('\n', ' ')

        max_field_str_sz = 2 * (curses.COLS - 6) // 3

        self.field_str = field_str[:max_field_str_sz]
        if len(field_str) > max_field_str_sz:
            self.field_str = self.field_str[:-3] + "..."
        self.field_str = html.escape(self.field_str)

        self.deck_str = ", ".join({col.decks.name(c.did) for c in note_obj.cards()})

from __future__ import annotations

import curses
import _curses
import curses.textpad

import tempfile
import os
import subprocess

from anki import decks_pb2
from anki import search_pb2
from anki.collection import Collection
from anki.models import NotetypeDict, NotetypeId, NotetypeNameId
from anki.notes import Note, NoteId

from acurses.conf import ConfigManager
from acurses.keyhandler import KeyHandler
from acurses.decks import DeckManager
from acurses.io import fill_line, align_style_print
from acurses.sync import sync_collection
from acurses.style import init_style
from acurses.select_from_list import SelectFromList
from acurses.wrappers import DeckInfo
from acurses.html import NoteParser
from acurses.browser import NoteBrowser
from acurses.input_line import InputLine

DeckNameId = decks_pb2.DeckNameId
SearchNode = search_pb2.SearchNode

class MainMenu(KeyHandler):
    scr: _curses.window
    head_str: str
    foot_str: str
    col: Collection
    conf: ConfigManager
    mw: _curses.window
    command_map: dict[str, Callable[[MainMenu], None] | Callable[[MainMenu], str]]
    edited_note_ids: set[NoteId]

    def init_keybinds(self) -> None:
        self.keybind_map = \
        {
            'q': lambda: True, # quit
            ':': lambda child: self.exec_command(child),
        }

    def init_commands(self) -> None:
        self.command_map = \
        {
            "q!": self.force_quit,
            "wq": self.write_and_quit,
            "sq": self.sync_and_quit,
            "w": self.write_col,
            "s": self.sync,
            "new": self.new_note,
            "add": self.new_note,
            "": lambda: None,
            "find": self.find_notes,
            "findin": self.find_notes_in,
            "edits": self.browse_edited_notes,
        }

    def init_curses(self) -> None:
        self.scr.keypad(False) # ignore non-keyboard input
        curses.noecho() # don't echo user input
        init_style()
        self.redraw_scr(self.head_str, self.foot_str)
        curses.curs_set(0) # make cursor invisible

    def init_collection(self) -> None:
        if self.conf.collection_path is not None:
            col_path = self.conf.collection_path
        else:
            col_path = self.prompt("Enter collection db path:")

        try:
            self.col = Collection(col_path)
        except Exception as e:
            self.dump_debug(f"Error opening collection db: {e}")

    def __init__(self, scr: _curses.window):
        self.parent = None
        self.scr = scr
        self.head_str = "Main Menu  |  q=quit"
        self.foot_str = "Loading collection..."
        self.mw = curses.newwin(curses.LINES - 4, curses.COLS, 2, 0)
        self.edited_note_ids = set()

        self.init_curses()
        self.init_keybinds()
        self.init_commands()

        self.conf = ConfigManager(self)

        self.init_collection()

    def set_head(self, s: str) -> None:
        """Clear the head-line and place the given string into it"""
        fill_line(self.scr, 0, ' ')
        align_style_print(self.scr, 0, 1, s)
        self.scr.refresh()

    def set_foot(self, s: str) -> None:
        fill_line(self.scr, -1, ' ')
        align_style_print(self.scr, curses.LINES - 1, 1, s)
        self.scr.refresh()

    def dump_debug(self, text: str, pause: bool = True) -> None:
        """Dumps the given string directly into the screen;
        If pause is True, waits for a key input from the user before proceeding
        """

        self.mw.clear()
        self.mw.addstr(f"{text}")
        self.mw.refresh()

        if pause:
            self.mw.addstr(" (Press any key to continue) ")
            self.mw.refresh()
            self.mw.getch()

    def ask_yn(self, prompt: str) -> bool:
        """Prints the given prompt to the bottom line of the screen, and gets a y/n
        response from the user
        """

        user_input = ""

        while not user_input or user_input[0] not in ['y', 'n']:
            user_input = self.prompt(f"{prompt} (y/n) :")

        return user_input[0].lower() == 'y'

    def redraw_scr(self, head_str: str, foot_str: str) -> None:
        """Clears the screen entirely and redraws the basic layout"""
        self.scr.clear()

        self.set_head(head_str)
        self.set_foot(foot_str)
        fill_line(self.scr, 1)
        fill_line(self.scr, -2)

        self.scr.refresh()

    def prompt(self, prompt: str, init_txt: str = "", quit_on_empty: bool = False) -> str:
        curses.curs_set(2) # set cursor to "very visible"

        out = InputLine(self, prompt, init_txt, quit_on_empty).out()

        curses.curs_set(0) # restore invisible cursor
        return out

    def exec_command(self, active_keyhandler: KeyHandler) -> None:
        """Opens a vim-like command mode"""
        cmd = self.prompt("", ":", True)[1:]

        if cmd in self.command_map:
            result = self.command_map[cmd]()
            active_keyhandler.redraw()
            if result: self.set_foot(result)
        else:
            self.set_foot("<red>Invalid command</red>")

    def consent_to_sync(self) -> bool:
        if self.conf.sync is not None:
            return self.conf.sync

        return self.ask_yn("Sync collection?")

    def sync(self) -> None:
        try:
            sync_collection(self.conf, self.col, self.set_foot, self.prompt)
        except Exception as e:
            self.dump_debug(f"Error while syncing: {e}")

    def sync_if_consented(self) -> None:
        if self.consent_to_sync():
            self.sync()

    def force_quit(self) -> None:
        exit()

    def write_col(self) -> None:
        self.col.save()

    def write_and_quit(self) -> None:
        self.write_col()
        exit()

    def sync_and_quit(self) -> None:
        self.write_col()
        self.sync()
        exit()

    def select_notetype(self) -> NotetypeNameId | None:
        notetypes = self.col.models.all_names_and_ids()

        def notetype_to_strs(notetype: NotetypeNameId) -> tuple[str, str, str]:
            return (notetype.name, "", "")

        selector = SelectFromList(self, self, "Select a note type", notetypes, notetype_to_strs,
                                  lambda nid, s: s in nid.name)
        selector.mainloop()
        return selector.get_selection()

    def current_deck_nameid(self) -> DeckNameId:
        current_id = self.col.decks.get_current_id()
        current_name = self.col.decks.name(current_id)
        return DeckNameId(name = current_name, id = current_id)

    def select_deck(self) -> DeckNameId | None:
        deck_list = list(self.col.decks.all_names_and_ids(skip_empty_default = True))
        curr_nameid = self.current_deck_nameid()

        if curr_nameid in deck_list:
            deck_list.remove(curr_nameid)
            deck_list.insert(0, curr_nameid)

        def deck_nameid_to_strs(deck: DeckNameId) -> tuple[str, str, str]:
            return (deck.name, "", "")

        selector = SelectFromList(self, self, "Select a deck", deck_list, deck_nameid_to_strs,
                                  lambda dnid, s: s in dnid.name)
        selector.mainloop()
        return selector.get_selection()

    def new_note(self) -> None:
        while True:
            if (notetype := self.select_notetype()) is None: return
            if (deck := self.select_deck()) is not None: break

        note = self.col.new_note(self.col.models.get(notetype.id))
        self.col.add_note(note, deck.id)
        self.edit_note(note)

    def edit_note(self, note: Note) -> None:
        self.edited_note_ids.add(note.id)
        fields = note.items()

        EDITOR = os.environ.get("EDITOR", "vim")

        curses.endwin()

        for k, v in fields:
            with tempfile.NamedTemporaryFile(prefix = f"{k}__", suffix = ".tmp") as tf:
                tf.write(str.encode(NoteParser.decode(v)))
                tf.flush()

                subprocess.call([EDITOR, tf.name])

                tf.seek(0)
                new_v = NoteParser.encode(tf.read().decode())

            note[k] = new_v

        note.flush() # update cards that rely on this note

    def find_notes(self, regex: bool = False) -> str:
        query = self.prompt("search for literal text:")
        matches = self.col.find_notes(self.col.build_search_string(SearchNode(literal_text=query)))

        if matches:
            NoteBrowser(self, self.col, matches).mainloop()
        else:
            return "<red>No matches</red>"

        return ""

    def find_notes_in(self, regex: bool = False) -> str:
        deck = self.select_deck()
        if deck is None: return
        query = self.prompt("search for literal text:")
        search_str = self.col.build_search_string(SearchNode(literal_text=query), SearchNode(deck=deck.name))
        matches = self.col.find_notes(search_str)

        if matches:
            NoteBrowser(self, self.col, matches).mainloop()
        else:
            return "<red>No matches</red>"

        return ""

    def browse_edited_notes(self) -> str:
        if not self.edited_note_ids:
            return "<red>No matches</red>"

        NoteBrowser(self, self.col, self.edited_note_ids).mainloop()

        return ""

    def redraw(self) -> None:
        self.redraw_scr(self.head_str, self.foot_str)

    def mainloop(self) -> None:
        self.sync_if_consented()
        DeckManager(self, self.col).mainloop()

        self.write_col()
        self.sync_if_consented()

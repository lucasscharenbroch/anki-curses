from __future__ import annotations

import curses
import _curses
import curses.textpad

from anki.collection import Collection
from acurses.conf import ConfigManager
from acurses.keyhandler import KeyHandler
from acurses.decks import DeckManager
from acurses.io import fill_line
from acurses.sync import sync_collection
from acurses.style import init_style

class MainMenu(KeyHandler):
    scr: _curses.window
    head_str: str
    foot_str: str
    col: Collection
    conf: ConfigManager
    mw: _curses.window

    def init_keybinds(self) -> None:
        self. keybind_map = \
        {
            'q': lambda: True, # quit
            ':': self.exec_command,
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
        self.head_str = "Main Menu | q=quit"
        self.foot_str = "Loading collection..."
        self.mw = curses.newwin(curses.LINES - 4, curses.COLS, 2, 0)

        self.init_curses()
        self.init_keybinds()

        self.conf = ConfigManager(self)

        self.init_collection()

    def set_head(self, s: str) -> None:
        """Clear the head-line and place the given string into it"""
        fill_line(self.scr, 0, ' ')
        self.scr.addstr(0, 0, s)
        self.scr.refresh()

    def set_foot(self, s: str) -> None:
        fill_line(self.scr, -1, ' ')
        self.scr.addstr(curses.LINES - 1, 0, s)
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

    def prompt(self, prompt: str = ":") -> str:
        curses.curs_set(2) # set cursor to "very visible"

        self.scr.addstr(curses.LINES - 1, 0, prompt) # draw prompt
        self.scr.refresh()

        foot_window = curses.newwin(1, curses.COLS - len(prompt), curses.LINES - 1, len(prompt))
        foot_window.clear()
        textbox = curses.textpad.Textbox(foot_window)

        input_string = textbox.edit()[:-1]
        curses.curs_set(0) # restore invisible cursor
        return input_string

    def exec_command(self) -> None:
        """Opens a vim-like command mode"""
        cmd = self.prompt()
        self.dump_debug(f"exec command {cmd}") # TODO

    def consent_to_sync(self) -> bool:
        if self.conf.sync is not None:
            return self.conf.sync

        return self.ask_yn("Sync collection?")

    def sync_if_consented(self) -> None:
        if self.consent_to_sync():
            try:
                sync_collection(self.conf, self.col, self.set_foot, self.prompt)
            except Exception as e:
                self.dump_debug(f"Error while syncing: {e}")

    def mainloop(self) -> None:
        self.sync_if_consented()
        DeckManager(self, self.col).mainloop()
        self.sync_if_consented()

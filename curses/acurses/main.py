from __future__ import annotations

import curses
import _curses
import curses.textpad
import os
import json

from anki.collection import Collection
from acurses.keyhandler import KeyHandler
from acurses.decks import DeckManager
from acurses.io import fill_line
from acurses.sync import sync_collection
from acurses.style import init_style

CONFIG_RELATIVE_PATH = "/.config/anki-curses/anki-curses.conf"

class MainMenu(KeyHandler):
    scr: _curses.window
    head_str: str
    foot_str: str
    col: Collection
    conf_data: dict[str, str] | None
    mw: _curses.window

    def init_keybinds(self) -> None:
        self.keybind_map = \
        {
            'q' : lambda s: True, # quit
        }

    def init_curses(self) -> None:
        self.scr.keypad(False) # ignore non-keyboard input
        curses.noecho() # don't echo user input
        init_style()
        self.redraw_scr(self.head_str, self.foot_str)

    def init_config_data(self) -> None:
        self.conf_data = None

        try:
            home_dir = os.environ["HOME"]
            path = home_dir + CONFIG_RELATIVE_PATH
            with open(path) as file:
                self.conf_data = json.load(file)
        except FileNotFoundError:
            self.dump_debug(f"Could not open {path}. "
                            f"The config should be in $HOME{CONFIG_RELATIVE_PATH}.")
        except json.JSONDecodeError as e:
            self.dump_debug(f"Error decoding config file JSON: {e}")
        except Exception as e:
            self.dump_debug(f"Error loading config file: {e}")

        if self.conf_data is None:
            self.conf_data = {}

    def init_collection(self) -> None:
        if self.conf_data and "collection" in self.conf_data:
            col_path = self.conf_data["collection"]
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

        self.init_keybinds()
        self.init_curses()
        self.init_config_data()
        self.init_collection()

    def set_head(self, s: str) -> None:
        "Clear the head-line and place the given string into it"
        fill_line(self.scr, 0, ' ')
        self.scr.addstr(0, 0, s)
        self.scr.refresh()

    def set_foot(self, s: str) -> None:
        fill_line(self.scr, -1, ' ')
        self.scr.addstr(curses.LINES - 1, 0, s)
        self.scr.refresh()

    def dump_debug(self, text: str, pause: bool = True) -> None:
        """Dumps the given string directly into the screen;
        If pause is True, waits for a key input from the user before proceeding"""

        self.mw.clear()
        self.mw.addstr(f"{text}")
        self.mw.refresh()

        if pause:
            self.mw.addstr(" (Press any key to continue) ")
            self.mw.refresh()
            self.mw.getch()

    def ask_yn(self, prompt: str) -> bool:
        """Prints the given prompt to the bottom line of the screen, and gets a y/n
        response from the user"""

        user_input = ""

        while not user_input or user_input[0] not in ['y', 'n']:
            user_input = self.prompt(f"{prompt} (y/n) :")

        return user_input[0].lower() == 'y'

    def redraw_scr(self, head_str: str, foot_str: str) -> None:
        "Clears the screen entirely and redraws the basic layout"
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

    def consent_to_sync(self) -> bool:
        if "sync" in self.conf_data:
            if self.conf_data["sync"].lower() == "false": return False
            if self.conf_data["sync"].lower() == "true": return True

        return self.ask_yn("Sync collection")

    def sync_if_consented(self) -> None:
        if self.consent_to_sync():
            try:
                sync_collection(self.conf_data, self.col, self.set_foot, self.prompt)
            except Exception as e:
                self.dump_debug(f"Error while syncing: {e}")

    def mainloop(self) -> None:
        self.sync_if_consented()
        DeckManager(self, self.col).mainloop()
        self.sync_if_consented()

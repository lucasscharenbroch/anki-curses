import curses

from typing import Callable

VALID_CHARS = "~`!1@2#3$4%5^6&7*8(9)0_-+=QqWwEeRrTtYyUuIiOoPp{[}]|\\AaSsDdFfGgHhJjKkLl:;\"'ZzXxCcVvBbNnMm<,>.?/ "

class InputLine():
    """A vim-like bottom-line textbox for entering commands or prompting"""
    prompt: str
    txt: str
    quit_on_empty: bool

    def __init__(self, mm, prompt: str, init_txt: str = "", quit_on_empty: bool = False,
                 on_update: Callable[[str], None] = lambda s: None):
        self.mm = mm
        self.prompt = prompt
        self.txt = init_txt
        self.quit_on_empty = quit_on_empty
        self.on_update = on_update
        self.win = win = curses.newwin(1, curses.COLS, curses.LINES - 1, 0)

    def out(self) -> str:
        self.win.clear()

        curses.curs_set(2) # set cursor to "very visible"

        result = ""

        while True:
            self.on_update(self.txt)
            self.win.hline(0, 0, " ", curses.COLS)
            self.win.addnstr(0, 0, self.prompt + self.txt, curses.COLS - 1)
            self.win.refresh()

            if not (self.prompt + self.txt) and self.quit_on_empty:
                result = ""
                break

            kc = self.mm.scr.getch()

            if kc == curses.KEY_ENTER or kc == ord('\n'): # enter
                result = self.txt
                break
            elif kc == curses.KEY_BACKSPACE or kc == 127: # backspace / delete
                self.txt = self.txt[:-1]
            elif kc == 27: # escape
                result = ""
                break
            elif kc in range(255) and chr(kc) in VALID_CHARS:
                self.txt += chr(kc)

        curses.curs_set(0) # restore invisible cursor
        return result

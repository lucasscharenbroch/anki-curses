import curses
import _curses

import acurses.main

def run_mm(scr: _curses.window) -> None:
    mm = main.MainMenu(scr)
    mm.mainloop()

def run() -> None:
    curses.wrapper(run_mm)

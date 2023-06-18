from typing import Literal

import curses
import _curses

from acurses.html import AttrParser

def fill_line(win: _curses.window, line: int, char: chr = None) -> None:
    "Overwrites the given line with repeated instances of the given character"

    if char is None: # workaround to default param; curses.ACS_HLINE is not available immediately
        char = curses.ACS_HLINE

    if line < 0:
        line = curses.LINES + line # support python-style negative-indexing

    win.hline(line, 0, char, curses.COLS)

def fill_line_attr(win: _curses.window, line: int, attr: int = 0) -> None:
    "Fills the given line with the given attribute"
    win.chgat(line, 0, win.getmaxyx()[1], attr)

def print_text_and_attrs(
    win: _curses.window,
    line: int,
    col: int,
    raw_text: str,
    attrs: list[int]
    ) -> None:
    for i in range(len(raw_text)):
        if col + i >= win.getmaxyx()[1]: # out of bounds
            return

        win.insstr(line, col + i, raw_text[i], attrs[i])

def print_styled_mu(win: _curses.window, line: int, col:int, text: str) -> None:
    raw_text, attrs = AttrParser.parse(text)
    print_text_and_attrs(win, line, col, raw_text, attrs)

def align_style_print_block(
    win: _curses.window,
    start_line: int,
    align: Literal[1, 2, 3],
    lines: list[str]
    ) -> None:

    width = win.getmaxyx()[1]

    parser = AttrParser()

    for i, text in enumerate(lines):
        parser.feed(text)
        raw_text, attrs = parser.parsed_text, parser.attr_list
        parser.parsed_text, parser.attr_list = "", []

        if align == 1: # left-align
            print_text_and_attrs(win, start_line + i, 0, raw_text, attrs) # directly on left
        elif align == 3: # right-align
            print_text_and_attrs(win, start_line + i, width - len(raw_text), raw_text, attrs)
        else: # centered
            print_text_and_attrs(win, start_line + i, (width - len(raw_text)) // 2, raw_text, attrs)

def align_style_print(win: _curses.window, line: int, align: Literal[1, 2, 3], text: str) -> None:
    align_style_print_block(win, line, align, [text])

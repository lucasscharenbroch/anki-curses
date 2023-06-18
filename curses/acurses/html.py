import curses
import html

from html.parser import HTMLParser
from acurses.style import *

class CardParser(HTMLParser):
    """Strips any non-cloze html from the given card (i.e. style tags),
    re-wrapping inactive cloze-span tags with REPLACEMENT_CLOZE_TAG"""

    tag_stack: list[str]
    attr_stack: list[str]
    parsed_text: str
    seen_div: bool

    def __init__(self):
        super().__init__()
        self.tag_stack = []
        self.attr_stack = []
        self.parsed_text = ""

    def handle_starttag(self, tag: str, attrs: list[str]) -> None:
        self.tag_stack.append(tag)
        self.attr_stack.append(attrs)
        if ('class', 'cloze') in attrs and not ('class', 'close-inactive') in attrs:
            self.parsed_text += f"<{REPLACEMENT_CLOZE_TAG}>"
        elif tag == 'div':
            self.parsed_text += "\n"

    def handle_endtag(self, tag: str) -> None:
        assert self.tag_stack and self.tag_stack[-1] == tag
        self.tag_stack.pop()
        attrs = self.attr_stack.pop()
        if ('class', 'cloze') in attrs and not ('class', 'close-inactive') in attrs:
            self.parsed_text += f"</{REPLACEMENT_CLOZE_TAG}>"

    def handle_data(self, data: str) -> None:
        if not "style" in self.tag_stack:
            self.parsed_text += html.escape(data) # re-escape '<>&' so card data isn't interpreted
                                                  # as a style tag

    @staticmethod
    def parse(card: str) -> str:
        card = card.replace("<br>", "\n").replace("<div><br></div>", "\n")
        parser = CardParser()
        parser.feed(card)
        return parser.parsed_text

class AttrParser(HTMLParser):
    """Converts style-marked text (with tags exclusively from ATTR_TAGS) into
    a (un-marked text, attribute-list) pair for printing to the screen"""

    parsed_text: str
    tag_stack: list[str]
    attr_list: list[int]
    current_attr: int

    def __init__(self):
        super().__init__()
        self.parsed_text = ""
        self.tag_stack = []
        self.attr_list = []
        self.current_attr = 0

    def handle_starttag(self, tag: str, attrs: list[str]) -> None:
        if not tag in ATTR_TAGS:
            return

        self.tag_stack.append(tag)
        self.current_attr |= ATTR_TAGS[tag]

    def handle_endtag(self, tag: str) -> None:
        assert tag in ATTR_TAGS
        assert tag in self.tag_stack

        self.tag_stack.remove(tag)
        self.current_attr ^= ATTR_TAGS[tag]

    def handle_data(self, data: str) -> None:
        self.parsed_text += data
        self.attr_list += [self.current_attr] * len(data)

    @staticmethod
    def parse(s: str) -> str:
        parser = AttrParser()
        parser.feed(s)
        return (parser.parsed_text, parser.attr_list)

class NoteParser(HTMLParser):
    """Converts html escape characters (by default) and divs to lines"""

    parsed_text: str

    def __init__(self):
        super().__init__()
        self.parsed_text = ""

    def handle_starttag(self, tag: str, attrs: list[str]) -> None:
        if tag == "div":
            self.parsed_text += "\n"

    def handle_endtag(self, tag: str) -> None:
        pass

    def handle_data(self, data: str) -> None:
        self.parsed_text += data

    @staticmethod
    def decode(s: str) -> str:
        s = s.replace("<br>", "\n")
        parser = NoteParser()
        parser.feed(s)
        return parser.parsed_text

    @staticmethod
    def encode(s: str) -> str:
        s = html.escape(s)

        result = ""

        for i, line in enumerate(s.split("\n")):
            if line == "":
                line = "<br>"

            if i == 0:
                result += line
            else:
                result += f"<div>{line}</div>"

        return result

import curses

REPLACEMENT_CLOZE_TAG = "blue" # make inactive cloze text blue

DEFAULT_ATTR = 0
ATTR_TAGS = {}

COLOR_PAIR_IDS = \
{
    "blue": 1,
    "red": 2,
    "green": 3,
}

BARE_COLORS = \
{
    "blue": curses.COLOR_BLUE,
    "red": curses.COLOR_RED,
    "green": curses.COLOR_GREEN,
}

def init_attr_tags():
    global ATTR_TAGS

    ATTR_TAGS |= \
    {
        "normal": 0,
        "so": curses.A_STANDOUT,
        "u": curses.A_UNDERLINE,
        "b": curses.A_BOLD,
        "i": curses.A_ITALIC,
    }

    for name, pair_id in COLOR_PAIR_IDS.items():
        curses.init_pair(pair_id, BARE_COLORS[name], -1)
        ATTR_TAGS[name] = curses.color_pair(pair_id)

def init_style() -> None:
    curses.use_default_colors()
    curses.curs_set(0) # invisible cursor
    init_attr_tags()
    assert ATTR_TAGS is not None

def get_attr_tags() -> dict[str, int]:
    return ATTR_TAGS

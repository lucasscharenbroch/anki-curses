# Anki-Curses

A fork of [Anki](https://github.com/ankitects/anki) with a curses front-end.

<image src="screenshot.png">

The curses interface is not currently capable of being a complete replacement for the GUI (qt), but its features (see below) aim to cover most typical studying requirements.

## Features
- Basic Deck Browsing
- Support for Basic Cards and Cloze Cards (Cloze deletion)
- Note Editing
- Note Lookup
- Adding Notes
- Sync
- Configuration File

## Usage
Anki-curses works directly on top of Anki's backend, so Anki can be built normally. This mainly entails installing dependencies and executing "run". See [Anki's github](https://github.com/ankitects/anki) for details.

Anki-curses relies on Anki for profile management, so the qt app must be run ("./run --qt") to set up the "collection.anki2" file. The curses interfaces prompts the user for this file if it isn't provided in the config.

## Config File

The default location for the config file is "~/.config/anki-curses/config.toml" (defined in curses/acurses/conf.py as CONFIG_RELATIVE_PATH). Here's an example config.

````toml
collection_path = "/home/lucas/.local/share/Anki2/User 1/collection.anki2"
endpoint = "https://sync.ankiweb.net" # this is the default
username = "plaintext-username" # not necessary if hkey is provided
password = "plaintext-password" # not necessary if hkey is provided
hkey = "plaintext-hkey" # generated (and printed by the curses program) after a plaintext authentication
sync = true # if this isn't set, the program will prompt for a sync on start and exit
hide_child_decks = true # hides nested decks in the deck manager
````

## Keybinds

Most of the keybinds are specified in the header of the window. Some repeated ones (':' for command, '/' for search, 'dufb' for navigation) are occasionally excluded

## Command-Mode Commands

A vim-style command-entry mode is used.

- **:q!** - force quit
- **:w** - write db (save)
- **:s** - sync (and save)
- **:wq** - write and quit
- **:sq** - sync and quit
- **:new**, **:add** - new note
- **:find** - find note
- **:findin** - find note in a specific deck
- **:edits** - browse edited notes

By default, when quitting the program, the database is saved, and sync is prompted for (unless 'sync' is set in the config).

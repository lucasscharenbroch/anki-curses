import os
import toml

class ConfigManager:
    CONFIG_RELATIVE_PATH = "/.config/anki-curses/config.toml"
    CONFIG_OPTIONS = {
        "collection_path": str,
        "endpoint": str,
        "username": str,
        "password": str,
        "hkey": str,
        "sync": bool,
        "hide_child_decks": bool,
    }

    def __init__(self, mm):
        self.mm = mm
        conf_data = {}

        try:
            home_dir = os.environ["HOME"]
            path = home_dir + self.CONFIG_RELATIVE_PATH
            with open(path) as file:
                conf_data = toml.load(file)
        except FileNotFoundError:
            self.mm.dump_debug(f"Could not open {path}. "
                          f"The config should be in $HOME{self.CONFIG_RELATIVE_PATH}.")
        except toml.TomlDecodeError as e:
            self.mm.dump_debug(f"Error decoding config file TOML: {e}")
        except Exception as e:
            self.mm.dump_debug(f"Error loading config file: {e}")
        else:
            self.init_fields(conf_data)
            return

        self.init_fields({})

    def init_fields(self, conf_data: dict[str, any]) -> None:
        """initializes this object's fields based on conf_data"""
        for (k, v) in conf_data.items():
            if k not in self.CONFIG_OPTIONS:
                self.mm.dump_debug(f"Invalid key in config: '{k}'")
            elif not isinstance(v, self.CONFIG_OPTIONS[k]):
                self.mm.dump_debug(f"Invalid value type for key '{k}' in config: expected "
                                   f"{self.CONFIG_OPTIONS[k]}, recieved {type(v)}")
            else:
                setattr(self, k, v)

        # fill remaining fields with none
        for k in self.CONFIG_OPTIONS:
            if not hasattr(self, k):
                setattr(self, k, None)

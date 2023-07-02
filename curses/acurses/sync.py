from typing import Callable

import anki.collection as collection

from anki.sync import SyncAuth
from anki.errors import SyncError

from acurses.conf import ConfigManager

DEFAULT_ENDPOINT = "https://sync.ankiweb.net"

def get_sync_auth(
conf: ConfigManager,
col: collection.Collection,
prompt: Callable[[str], str]
) -> SyncAuth:
    if conf.endpoint is not None:
        endpoint = conf.endpoint
    else:
        raise Exception(f"'endpoint' not in config file: defaulting to {DEFAULT_ENDPOINT}")
        endpoint = DEFAULT_ENDPOINT

    if conf.hkey is not None:
        return SyncAuth(hkey = conf.hkey, endpoint = endpoint, io_timeout_secs = 30)

    username = conf.username if conf.username is not None else prompt("Username:")
    password = conf.password if conf.password is not None else prompt("Password:")

    auth = col.sync_login(username, password, endpoint)

    if auth.hkey is not None and prompt("Plaintext auth successful, print hkey? ").lower() == 'y':
        prompt(f"{auth.hkey} (Press enter to continue) ")

    return auth

def sync_collection(
conf: ConfigManager,
col: collection.Collection,
status: Callable[[str], None],
prompt: Callable[[str], str]
) -> None:
    col.save(trx = False)

    status("Syncing... (authenticating)")

    auth = None

    while auth is None:
        try:
            auth = get_sync_auth(conf, col, prompt)
        except SyncError as e:
            raise Exception(f"Authentication error: {e}")

    status("Syncing...")

    try:
        result = col.sync_collection(auth)
    except Exception as e:
        raise Exception(f"Error while syncing: {e}")
    else:
        if result.required == result.NO_CHANGES:
            return
        else:
            raise Exception("Full sync required. Please use qt.")

    status("Success")

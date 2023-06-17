from typing import Callable

import anki.collection as collection

from anki.sync import SyncAuth
from anki.errors import SyncError

DEFAULT_ENDPOINT = "https://sync.ankiweb.net"

def get_sync_auth(
conf_data: dict[str, str],
col: collection.Collection,
prompt: Callable[[str], str]
) -> SyncAuth:
    if "endpoint" in conf_data:
        endpoint = conf_data["endpoint"]
    else:
        raise Exception(f"'endpoint' not in config file: defaulting to {DEFAULT_ENDPOINT}")
        endpoint = DEFAULT_ENDPOINT

    if "hkey" in conf_data:
        return SyncAuth(hkey = conf_data["hkey"], endpoint = endpoint, io_timeout_secs = 30)

    username = conf_data["username"] if "username" in conf_data else prompt("Username:")
    password = conf_data["password"] if "password" in conf_data else prompt("Password:")

    return col.sync_login(username, password, endpoint)

def sync_collection(
conf_data: dict[str, str],
col: collection.Collection,
status: Callable[[str], None],
prompt: Callable[[str], str]
) -> None:
    col.save(trx = False)

    status("Syncing... (authenticating)")

    auth = None

    while auth is None:
        try:
            auth = get_sync_auth(conf_data, col, prompt)
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

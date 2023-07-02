from __future__ import annotations

class KeyHandler:
    parent: KeyHandler | None
    keys_handled_by_parent: set[int] | None
    keybind_map: dict[int, Callable[[], bool] | Callable[[], None]]
    mainloop: Callable[[KeyHandler], None]

    def handle_key(self, keycode: int) -> bool:
        """Calls the method corresponding to the given key, passing it up to
        parent if the key is in keys_handled_by_parent and not in keybind_map;
        True is returned to signal a termination request, otherwise False is returned
        """
        key = chr(keycode)

        if key in self.keybind_map:
            return self.keybind_map[key]()
        elif key in self.keys_handled_by_parent:
            return self.parent.handle_key(keycode)
        else:
            return False

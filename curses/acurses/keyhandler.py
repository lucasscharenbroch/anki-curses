from __future__ import annotations

class KeyHandler:
    parent: KeyHandler | None
    keys_handled_by_parent: set[int] | None
    keybind_map: dict[int, Callable[[], bool] | Callable[[], None] |
                           Callable[[KeyHandler], bool] | Callable[[KeyHandler], None]]
    mainloop: Callable[[KeyHandler], None]

    def handle_key(self, keycode: int, child: KeyHandler = None) -> bool:
        """Calls the method corresponding to the given key, passing it up to
        parent if the key is in keys_handled_by_parent and not in keybind_map;
        True is returned to signal a termination request, otherwise False is returned
        """
        key = chr(keycode)

        if key in self.keybind_map:
            return self.keybind_map[key](child) if child else self.keybind_map[key]()
        elif self.keys_handled_by_parent and key in self.keys_handled_by_parent:
            return self.parent.handle_key(keycode, self if child is None else child)
        else:
            return False

    def redraw(self) -> None:
        """Redraw the entire screen (header, footer, etc.)- blank in superclass"""

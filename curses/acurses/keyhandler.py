from __future__ import annotations

class KeyHandler:
    parent: KeyHandler | None
    keybind_map: dict[int, Callable[[KeyHandler], bool] | Callable[[KeyHandler], None]]
    mainloop: Callable[[KeyHandler], None]

    def handle_key(self, keycode: int) -> bool:
        key = chr(keycode)

        if key in self.keybind_map:
            return self.keybind_map[key](self)

"""Global constants are stored here."""
from __future__ import annotations
from typing import Final
from tcod.event import KeySym

ACCEPT_KEYS: Final = [
    KeySym.RETURN,
    KeySym.RETURN2,
    KeySym.KP_ENTER,
    KeySym.z
]

DIRECTION_KEYS: Final = {
    # Arrow keys
    KeySym.LEFT: (-1, 0),
    KeySym.RIGHT: (1, 0),
    KeySym.UP: (0, -1),
    KeySym.DOWN: (0, 1),
    # Arrow key diagonals
    KeySym.HOME: (-1, -1),
    KeySym.END: (-1, 1),
    KeySym.PAGEUP: (1, -1),
    KeySym.PAGEDOWN: (1, 1),
    # Keypad
    KeySym.KP_4: (-1, 0),
    KeySym.KP_6: (1, 0),
    KeySym.KP_8: (0, -1),
    KeySym.KP_2: (0, 1),
    KeySym.KP_7: (-1, -1),
    KeySym.KP_1: (-1, 1),
    KeySym.KP_9: (1, -1),
    KeySym.KP_3: (1, 1),
    # VI keys
    KeySym.h: (-1, 0),
    KeySym.l: (1, 0),
    KeySym.k: (0, -1),
    KeySym.j: (0, 1),
    KeySym.y: (-1, -1),
    KeySym.b: (-1, 1),
    KeySym.u: (1, -1),
    KeySym.n: (1, 1),
}

gameframe_left: Final = 21
gameframe_right: Final = 79
gameframe_top: Final = 1
gameframe_bottom: Final = 39

logframe_bottom: Final = 49
logframe_top: Final = 41
logframe_left: Final = 21
logframe_right: Final = 79

NOISE_COLLISION_THRESH = 0.5
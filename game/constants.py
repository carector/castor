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

COLOR_PALLETE: Final = {
    0: (255, 255, 255),
    1: (255, 106, 0),
    2: (0, 255, 0),
    3: (128, 128, 128),
    4: (128, 0, 128),
    5: (64, 64, 255),
    6: (255, 0, 0),
    7: (232, 183, 150)
}

GAMEFRAME_LEFT: Final = 21
GAMEFRAME_RIGHT: Final = 79
GAMEFRAME_TOP: Final = 1
GAMEFRAME_BOTTOM: Final = 39

LOGFRAME_LEFT: Final = 21
LOGFRAME_RIGHT: Final = 79
LOGFRAME_TOP: Final = 41
LOGFRAME_BOTTOM: Final = 49

NOISE_COLLISION_THRESH = 0.5
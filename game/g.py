"""This module stores globally mutable variables used by this program.\n
    (Basically singleton)"""
from __future__ import annotations

import numpy as np
import game.components
import game.state
import game.menus
import tcod.context
import tcod.ecs
import tcod.sdl.audio

context: tcod.context.Context
"""The window managed by tcod."""

world: tcod.ecs.Registry
"""The active ECS registry and current session."""

states: list[game.state.States] = []
"""A stack of states with the last item being the active state."""

console: tcod.console.Console
"""The current main console."""

mixer: tcod.sdl.audio.BasicMixer
"""Mixer for handling game music."""

log: game.menus.LogMenu

noise: tcod.noise.Noise
"""Sampler for generating terrain"""

grid: np.ndarray
"""Final rendered noise grid from this frame."""

current_actor: game.components.Actor = None
"""Current actor the player is interacting with."""

# Current idea:
# - Use a constant seed game-wide
# - Find interesting spots and place handcrafted encounters there
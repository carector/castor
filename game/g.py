"""This module stores globally mutable variables used by this program.\n
    (Basically singleton)"""
from __future__ import annotations

import game.state
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

#player: object
"""Singleton reference to player object"""
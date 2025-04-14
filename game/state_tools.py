"""Handles events and rendering of the global state."""
from __future__ import annotations

from game import g
from game.state import Pop, Push, Reset, State, StateResult

import tcod.context
import tcod.ecs

def main_draw() -> None:
    if not g.states:
        return
    g.console.clear()
    g.states[-1].on_draw(g.console)
    g.context.present(g.console)

def apply_state_result(result: StateResult) -> None:
    match result:
        case Push(state=state):
            g.states.append(state)
        case Pop():
            g.states.pop()
        case Reset(state=state):
            while g.states:
                apply_state_result(Pop())
            apply_state_result(Push(state))
        case None:
            pass
        case _:
            raise TypeError(result)
        
def main_loop() -> None:
    while g.states:         # Exit if no state exists
        main_draw()
        for event in tcod.event.wait():
            tile_event = g.context.convert_event(event)     # Mouse coord events should be converted to tiles
            if g.states:
                apply_state_result(g.states[-1].on_event(tile_event))   # Pass event and handle potential state changes at the same time
            
def get_previous_state(state: State) -> State | None:
    current_index = next(index for index, value in enumerate(g.states) if value is state)
    return g.states[current_index - 1] if current_index > 0 else None

def draw_previous_state(state: State, console: tcod.console.Console, dim: bool = True) -> None:
    prev_state = get_previous_state(state)
    if prev_state is None: return
    
    prev_state.on_draw(console)
    if dim and state is g.states[-1]:
        console.rgb["fg"] //= 4
        console.rgb["bg"] //= 4
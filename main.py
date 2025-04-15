"""Main entry-point module. This script is used to start the program."""
from __future__ import annotations

import attrs
import tcod.tileset
import tcod.event
import tcod.console
import tcod.context

from game import g
import game.state_tools
import game.states
import game.world_tools


def main() -> None:
    tileset = tcod.tileset.load_tilesheet(
        "data/spr/alloycurses.png", columns=16, rows=16, charmap=tcod.tileset.CHARMAP_CP437
    )
    
    tcod.tileset.procedural_block_elements(tileset=tileset)
    g.console = tcod.console.Console(100, 50)
    g.states = [game.states.MainMenu()]
    # Game loop
    with tcod.context.new(tileset=tileset, console=g.console) as g.context:
        game.state_tools.main_loop()
    
            

if __name__ == "__main__":
    main()
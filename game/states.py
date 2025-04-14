"""Global constants are stored here."""
from __future__ import annotations
import attrs
import tcod.event
import tcod.console

from game import g
from game.components import Gold, Graphic, Position
from game.constants import DIRECTION_KEYS
from game.tags import IsItem, IsPlayer

@attrs.define()
class InGame:
    """Primary in-game state.\n
    States will always use g.world to access the ECS registry."""
    
    # Handle event draw
    def on_draw(self, console: tcod.console.Console) -> None:
        """Draw the standard screen."""
        # We can draw entities if they have both a Position and a Graphic
        for entity in g.world.Q.all_of(components=[Position, Graphic]):
            pos = entity.components[Position]
            graphic = entity.components[Graphic]

            if not (0 <= pos.x < console.width and 0 <= pos.y < console.height): continue   # Ignore offscreen
            console.rgb[["ch", "fg"]][pos.y, pos.x] = graphic.ch, graphic.fg
        
        # Print text component if it exists
        if text := g.world[None].components.get(("Text", str)):
            console.print(x=1, y=console.height - 2, string=f"> {text}", fg=(255,255,255), bg=(0,0,0))

    # Handle events        
    def on_event(self, event: tcod.event.Event) -> None:
        """Handle events for the in-game state."""
        (player,) = g.world.Q.all_of(components=[], tags=[IsPlayer])
        match event:
            # Movement
            case tcod.event.KeyDown(sym=sym) if sym in DIRECTION_KEYS:
                player.components[Position] += DIRECTION_KEYS[sym]
                
                # Pick up gold on the same space as the player
                for gold in g.world.Q.all_of(components=[Gold], tags=[player.components[Position], IsItem]):
                    player.components[Gold] += gold.components[Gold]
                    text = f"Picked up {gold.components[Gold]}g, total: {player.components[Gold]}g"
                    g.world[None].components[("Text", str)] = text
                    gold.clear()
                
            # Handle quit
            case tcod.event.Quit():
                raise SystemExit    
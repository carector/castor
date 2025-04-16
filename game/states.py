"""Global constants are stored here."""
from __future__ import annotations
import soundfile
import attrs
import tcod.event
import tcod.console
import tcod.sdl.audio
from tcod.event import KeySym

from game import g
from game.components import Gold, Graphic, Position
from game.constants import DIRECTION_KEYS, gameframe_left, gameframe_right, gameframe_top, gameframe_bottom, logframe_bottom, logframe_top, logframe_right, logframe_left
from game.tags import IsItem, IsPlayer
from game.state import State, StateResult, Pop, Push, Reset
import game.menus
import game.world_tools
from tcod import libtcodpy

@attrs.define()
class MainMenu(game.menus.ListMenu):
    """Main menu state."""
    
    __slots__ = ()
    
    def __init__(self) -> None:
        """Initialize main menu"""
        items = [
            game.menus.SelectItem("New game", self.new_game),
            game.menus.SelectItem("Quit", self.quit)
        ]
        
        # Continue if world already exists from this session
        if hasattr(g, "world"):
            items.insert(0, game.menus.SelectItem("Continue", self.continue_))
            
        super().__init__(
            items = tuple(items),
            selected=0,
            x=5,
            y=5
        )

    @staticmethod        
    def new_game() -> StateResult:
        g.world = game.world_tools.new_world()
        g.log = game.menus.LogMenu(x=21, y=48, w=58, h=8)
        return Reset(InGame())

    
    @staticmethod        
    def continue_():
        return Reset(InGame())
    
    @staticmethod        
    def quit():
        raise SystemExit
    
    
@attrs.define()
class InGame(State):
    """Primary in-game state.\n
    States will always use g.world to access the ECS registry."""
    
    #def __init__(self) -> None:
        # Play music
        # g.mixer = tcod.sdl.audio.BasicMixer(tcod.sdl.audio.open())
        # sound, sample_rate = soundfile.read("data/mus/mus_sadspiritiv.ogg")
        # sound = g.mixer.device.convert(sound, sample_rate)
        # channel = g.mixer.play(sound)
    
    # Handle event draw
    def on_draw(self, console: tcod.console.Console) -> None:
        """Draw the standard screen."""
        (player,) = g.world.Q.all_of(components=[], tags=[IsPlayer])
        player_pos = player.components[Position]
        offset_x = player_pos.x - 49
        offset_y = player_pos.y - 20
        
        gameframe_decor = "╝═╚║ ║╗═╔"
        console.draw_frame(0, 0, 20, 40, fg=(128, 128, 128), decoration=gameframe_decor)    # Inventory frame
        console.draw_frame(80, 0, 20, 50, fg=(128, 128, 128), decoration=gameframe_decor)   # Right panel frame
        console.draw_frame(20, 0, 60, 40, fg=(255, 200, 255), decoration=gameframe_decor)   # Game frame
        console.print(x=20, y=0, width=60, height=1, fg=(255, 255, 0), string="World of Wowzers", alignment=libtcodpy.CENTER)
        console.draw_frame(0, 40, 20, 10, fg=(128, 128, 128), decoration=gameframe_decor)   # World stats frame
        console.draw_frame(20, 40, 60, 10, fg=(128, 128, 128), decoration=gameframe_decor)  # Log frame
        
        
        g.log.on_draw(console=console)
        
        # We can draw entities if they have both a Position and a Graphic
        for entity in g.world.Q.all_of(components=[Position, Graphic]):
            pos = entity.components[Position]
            graphic = entity.components[Graphic]

            if not (gameframe_left <= pos.x-offset_x < gameframe_right and gameframe_top <= pos.y-offset_y < gameframe_bottom): continue   # Ignore offscreen
            console.rgb[["ch", "fg", "bg"]][pos.y-offset_y, pos.x-offset_x] = graphic.ch, graphic.fg, (0,0,0)
        
        # Print text component if it exists
        if text := g.world[None].components.get(("Text", str)):
            console.print(x=logframe_left, y=logframe_bottom-1, string=f"> {text}", fg=(255,255,255))

    # Handle events        
    def on_event(self, event: tcod.event.Event) -> StateResult:
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
                    g.log.add_item(f"Picked up {gold.components[Gold]}g, total: {player.components[Gold]}g")
                    gold.clear()
                return None
            
            # Handle quit
            case tcod.event.KeyDown(sym=KeySym.ESCAPE):
                #g.mixer.stop()
                return Push(MainMenu())
            case tcod.event.Quit:
                raise SystemExit
            case _:
                return None
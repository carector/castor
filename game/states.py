"""Global constants are stored here."""
from __future__ import annotations
import soundfile
import attrs
import tcod.event
import tcod.console
import tcod.sdl.audio
import numpy as np
from tcod.event import KeySym
import game.g as g
from game.components import Gold, Graphic, Position, Actor, LevelContainer
from game.constants import DIRECTION_KEYS, NOISE_COLLISION_THRESH, gameframe_left, gameframe_right, gameframe_top, gameframe_bottom, logframe_bottom, logframe_top, logframe_right, logframe_left
from game.tags import IsItem, IsPlayer, IsActor
from game.state import State, StateResult, Pop, Push, Reset
import game.menus
import game.world_tools
from tcod import libtcodpy
from random import Random

from game.utils import clamp

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
    
    zones: list = []
    area_name: str = ""
    count: int = 0
    
    def __init__(self) -> None:
        self.count = 0
        g.world = game.world_tools.new_world()
        g.log = game.menus.LogMenu(x=21, y=48, w=58, h=8)
        self.update_area_name("World of Wowzers")
        print(g.dungeon.bsp.__repr__())
        # Play music
        # g.mixer = tcod.sdl.audio.BasicMixer(tcod.sdl.audio.open())
        # sound, sample_rate = soundfile.read("data/mus/mus_sadspiritiv.ogg")
        # sound = g.mixer.device.convert(sound, sample_rate)
        # channel = g.mixer.play(sound, volume=0.25)
    
    def update_area_name(self, name: str) -> None:
        self.area_name = name
    
    # Handle event draw
    def on_draw(self, console: tcod.console.Console) -> None:
        """Draw the standard screen."""
        (player,) = g.world.Q.all_of(components=[], tags=[IsPlayer])
        player_pos = player.components[Position]
        offset_x = player_pos.x - 49
        offset_y = player_pos.y - 20
        
        # Draw overworld
        #self.overworld_draw(player_pos, console)
        
        # BSP dungeon test
        rand = Random()
        count = 0
        for n in g.dungeon.bsp.post_order():            
            if not n.children:
                console.draw_frame(x=n.x-offset_x, y=n.y-offset_y, width=n.width, height=n.height, clear=False, fg=(255, 255, 255))
            else:
                node1, node2 = n.children
                color = (rand.randint(0, 255), rand.randint(0, 255), rand.randint(0, 255))
                
                if(node1.children): node1 = g.dungeon.get_nearest_room(n.children[0], True)
                if(node2.children): node2 = g.dungeon.get_nearest_room(n.children[1], False)
                
                x1, y1 = node1.x, node1.y
                x2, y2 = node2.x, node2.y
                frame_color = (255, 255, 255)
                
                # x1 = clamp(n.position, x1+1, x1+node1.width-2)
                # x2 = clamp(n.position, x2+1, x2+node2.width-2)
                # y1 = clamp(n.position, y1+1, y1+node1.height-2)
                # y2 = clamp(n.position, y2+1, y2+node2.height-2)
                
                # x1, y1 = g.dungeon.get_closest_coords(node2, node1)
                # x2, y2 = g.dungeon.get_closest_coords(node1, node2)
                
                
                if not n.horizontal:
                    x1 = clamp(n.position, x1+1, x1+node1.width-2)
                    x2 = clamp(n.position, x2+1, x2+node2.width-2)
                    y1 = (y1 + y2 + node2.height - 1)//2
                    y2 = y1
                else:
                    y1 = clamp(n.position, y1+1, y1+node1.height-2)
                    y2 = clamp(n.position, y2+1, y2+node2.height-2)
                    x1 = (x1 + x2 + node2.width - 1)//2
                    x2 = x1

                w = x2 - x1+1
                h = y2 - y1+1
     
                console.draw_frame(x1-offset_x, y1-offset_y, w, h, fg=frame_color)
                console.print(x1-offset_x, y1-offset_y, "1", fg=color)
                console.print(x2-offset_x, y2-offset_y, "2", fg=color)    
                count += 1
                
        console.print(1, 1, f"Connections: {count}")

        # Entities
        for entity in g.world.Q.all_of(components=[Position, Graphic]):
            pos = entity.components[Position]
            graphic = entity.components[Graphic]

            if not (gameframe_left <= pos.x-offset_x < gameframe_right and gameframe_top <= pos.y-offset_y < gameframe_bottom): continue   # Ignore offscreen
            console.rgb[["ch", "fg", "bg"]][pos.y-offset_y, pos.x-offset_x] = graphic.ch, graphic.fg, (0,0,0)
        
        #self.gui_draw(player_pos, console)
        
    def overworld_draw(self, player_pos: Position, console: tcod.console.Console) -> None:
        offset_x = player_pos.x - 49
        offset_y = player_pos.y - 20
        
        # Terrain
        scale = 0.025
        g.grid = g.noise[tcod.noise.grid(
            shape=(58, 38), 
            scale=scale, 
            indexing="ij", 
            origin=(offset_x*scale, offset_y*scale))
        ]
        
        chars = [".", ",", "'", "`"]
        cols = [32, 16, 48, 64]
        it = np.nditer(g.grid, flags=['multi_index'])
        for pos in it:
            ch = ord("^")
            col = (0, 128, 0)
            if(pos < -0.25): 
                rand = int(g.noise.get_point(offset_y + it.multi_index[1], offset_x + it.multi_index[0])*4)
                ch = ord(chars[rand%4])
                col = (0, cols[rand%4], 0)
            elif(pos <= 0): col = (153, 141, 85)
            if(pos > NOISE_COLLISION_THRESH): ch = 0x2660
            console.rgb[["ch", "fg"]][it.multi_index[1] + 1, it.multi_index[0] + 21] = ch, col
                
        # Level data
        for level_entity in g.world.Q.all_of(components=[LevelContainer]):
            # TODO: Check if level is on screen
            level = level_entity.components[LevelContainer]
            tiles = np.nditer(level.tiles, flags=['multi_index'])
            intgrid = level.intgrid
            for tile in tiles:
                if tile == 0: continue
                t = tile
                col = (255, 255, 255)
                col_ind = intgrid[tiles.multi_index]
                tx = tiles.multi_index[0]
                ty = tiles.multi_index[1]
                if not (gameframe_left <= tx+level.x-offset_x < gameframe_right and gameframe_top <= ty+level.y-offset_y < gameframe_bottom): continue   # Ignore offscreen
                match col_ind:
                    case 2: col = (0, 255, 0)
                    case 4: col = (128, 0, 128)
                console.rgb[["ch", "fg"]][ty+level.y-offset_y, tx+level.x-offset_x] = t, col

    def gui_draw(self, player_pos: Position, console: tcod.console.Console) -> None:
        # Windows
        gameframe_decor = "╝═╚║ ║╗═╔"
        console.draw_frame(0, 0, 20, 40, fg=(128, 128, 128), decoration=gameframe_decor)    # Dialog frame
        console.draw_frame(80, 0, 20, 50, fg=(128, 128, 128), decoration=gameframe_decor)   # Inventory frame
        console.draw_frame(20, 0, 60, 40, fg=(200, 200, 200), decoration=gameframe_decor, clear=False)   # Game frame
        console.print(x=20, y=0, width=60, height=1, fg=(255, 255, 0), string=f"╣ {self.area_name} ╠", alignment=libtcodpy.CENTER)
        console.draw_frame(0, 40, 20, 10, fg=(128, 128, 128), decoration=gameframe_decor)   # World stats frame
        console.draw_frame(20, 40, 60, 10, fg=(128, 128, 128), decoration=gameframe_decor)  # Log frame
        g.log.on_draw(console=console)
        
        # Current actor info
        if g.current_actor is not None:
            console.print(x=0, y=0, width=20, height=1, fg=(255, 255, 0), string=f"╣ {g.current_actor.name} ╠", alignment=libtcodpy.CENTER)
            console.print(x=2, y=2, width=16, height=36, fg=(255, 255, 255), string=g.current_actor.text)
            #for i in range(g.current_actor.choices):
                
        # Player coords
        console.print(x=0, y=47, width=20, alignment=libtcodpy.CENTER, text=f"({player_pos.x}, {player_pos.y})", fg=(255, 255, 0))

    # Handle events        
    def on_event(self, event: tcod.event.Event) -> StateResult:
        """Handle events for the in-game state."""
        (player,) = g.world.Q.all_of(components=[], tags=[IsPlayer])
        match event:
            # Movement
            case tcod.event.KeyDown(sym=sym) if sym in DIRECTION_KEYS:
                player_pos = player.components[Position]
                # Check for actor collision
                for actor in g.world.Q.all_of(tags=[player_pos + DIRECTION_KEYS[sym], IsActor]): 
                    actor.components[Actor].on_interact()
                    return
                g.current_actor = None

                # Check for terrain collision
                #val = g.grid[28 + DIRECTION_KEYS[sym][0], 19 + DIRECTION_KEYS[sym][1]]
                #if val > NOISE_COLLISION_THRESH: return None
                
                # Check for level collision
                for level in g.world.Q.all_of(components=[LevelContainer]):
                    if not level.components[LevelContainer].within_bounds(player_pos.x, player_pos.y): continue
                    self.update_area_name(level.components[LevelContainer].id)
                    if level.components[LevelContainer].is_space_occupied(player_pos.x + DIRECTION_KEYS[sym][0], player_pos.y+DIRECTION_KEYS[sym][1]): return
                
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
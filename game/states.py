"""Global constants are stored here."""
from __future__ import annotations
import soundfile
import attrs
import tcod.event
import tcod.console
import tcod.sdl.audio
import numpy as np
from tcod.event import KeySym
import game.constants
import game.g as g
from game.components import Gold, Graphic, Position, Actor, LevelContainer, Transfer, Enemy
from game.constants import DIRECTION_KEYS, NOISE_COLLISION_THRESH, gameframe_left, gameframe_right, gameframe_top, gameframe_bottom, logframe_bottom, logframe_top, logframe_right, logframe_left
from game.tags import IsItem, IsPlayer
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
    
    dungeon_floors: list[game.world_tools.Dungeon] = []
    area_name: str = ""
    
    def __init__(self) -> None:
        g.world = game.world_tools.new_world()
        g.log = game.menus.LogMenu(x=21, y=48, w=58, h=8)
        self.update_area_name("World of Wowzers")
        self.dungeon_floors = []
        # Play music
        # if g.mixer:
        #     g.mixer.stop()
        # g.mixer = tcod.sdl.audio.BasicMixer(tcod.sdl.audio.open())
        # sound, sample_rate = soundfile.read("data/mus/mus_sadspiritiv.ogg")
        # sound = g.mixer.device.convert(sound, sample_rate)
        # channel = g.mixer.play(sound, volume=0.25)
    
    def update_area_name(self, name: str) -> None:
        self.area_name = name
    
    # Handle event draw
    def on_draw(self, console: tcod.console.Console) -> None:
        """Draw the standard screen."""
        
        world = g.world if len(self.dungeon_floors) == 0 else self.dungeon_floors[-1].world
        
        (player,) = g.world.Q.all_of(components=[], tags=[IsPlayer])
        player_pos = player.components[Position]
        offset_x = player_pos.x - 49
        offset_y = player_pos.y - 20
        
        # Don't follow player if we're in a dungeon
        if len(self.dungeon_floors) > 0:
            offset_x = -22
            offset_y = -2
        
        # Draw overworld or dungeon
        if len(self.dungeon_floors) > 0:
            self.dungeon_draw(dungeon=self.dungeon_floors[-1], console=console)
        
        else:
            self.overworld_draw(player_pos, console)
        
        # Draw entities
        for entity in world.Q.all_of(components=[Position, Graphic]):
            if entity == player: continue
            pos = entity.components[Position]
            graphic = entity.components[Graphic]

            if not (gameframe_left <= pos.x-offset_x < gameframe_right and gameframe_top <= pos.y-offset_y < gameframe_bottom): continue   # Ignore offscreen
            console.rgb[["ch", "fg", "bg"]][pos.y-offset_y, pos.x-offset_x] = graphic.ch, graphic.fg, (0,0,0)
        
        # Draw player
        console.rgb[["ch", "fg", "bg"]][player_pos.y-offset_y, player_pos.x-offset_x] = player.components[Graphic].ch, player.components[Graphic].fg, (0,0,0)
        
        # Draw GUI
        self.gui_draw(player_pos, console)
    
    def go_down_floor(self, exit_transfer_x: int, exit_transfer_y: int) -> None:
        new_dungeon = game.world_tools.Dungeon(x=0, y=0, width=56, height=36, max_depth=6, seed=123444, exit_x=exit_transfer_x, exit_y=exit_transfer_y)
        if len(self.dungeon_floors) == 0:
            g.log.add_item("You venture into the dungeon.")
        else:
            g.log.add_item("You venture further into the dungeon.")
        self.dungeon_floors.append(new_dungeon)
        self.update_area_name(f"Floor {len(self.dungeon_floors)}")
        
        
    def go_up_floor(self) -> None:
        g.log.add_item("You exit the dungeon floor.")
        d = self.dungeon_floors.pop()
        if len(self.dungeon_floors) > 0: self.update_area_name(f"Floor {len(self.dungeon_floors)}")
    
    def dungeon_draw(self, dungeon: game.world_tools.Dungeon, console: tcod.console.Console) -> None:
        offset_x = -22
        offset_y = -2
        rand = Random()
        
        for x in range(dungeon.width):
            for y in range(dungeon.height):    
                dx = x-offset_x
                dy = y-offset_y
                if dx >= console.width or dy >= console.height or dx < 0 or dy < 0: continue
                if dungeon.map[max(0, x-1), y] == 1 and dungeon.map[min(x+1, dungeon.width-1), y] == 1 and dungeon.map[x, max(0, y-1)] == 1 and dungeon.map[x, min(y+1, dungeon.height-1)] == 1: continue
                col = (0, 255, 0)
                ch = ord("#")
                match dungeon.map[x, y]:
                    case 0:
                        col = (128, 128, 128)
                        ch = ord(".")
                    case 2:
                        col = (255, 0, 0)
                        ch = ord("^")
                        
                #console.put_char(dx, dy, ch)
                console.rgb[["ch", "fg"]][dy, dx] = ch, col
        
        #console.draw_frame(dungeon.door_room.x-offset_x, dungeon.door_room.y-offset_y, dungeon.door_room.width, dungeon.door_room.height, clear=False)
                    
        # for node in dungeon.bsp.inverted_level_order():
        #     if not node.children:
        #         console.draw_frame(node.x-dungeon.bsp.x, node.y-dungeon.bsp.y, node.width, node.height, clear=False)
                
    def overworld_draw(self, player_pos: Position, console: tcod.console.Console) -> None:
        
        lock_to_screen = True
        offset_x = player_pos.x - 49
        offset_y = player_pos.y - 20
        
        # Terrain
        scale = 0.025
        g.grid = g.noise[tcod.noise.grid(
            shape=(100, 50), 
            scale=scale, 
            indexing="ij", 
            origin=(offset_x*scale, offset_y*scale))
        ]
        
        # Draw grass and terrain
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
            console.rgb[["ch", "fg"]][it.multi_index[1], it.multi_index[0]] = ch, col
                
        # Draw level containers
        for level_entity in g.world.Q.all_of(components=[LevelContainer]):
            # TODO: Check if level is on screen
            level = level_entity.components[LevelContainer]
            tiles = np.nditer(level.tiles, flags=['multi_index'])
            colors = level.colors
            for tile in tiles:
                if tile == 0: continue
                ch = tcod.tileset.CHARMAP_CP437[int(tile)]    # CP437 to ASCII
                col = game.constants.COLOR_PALLETE[colors[tiles.multi_index]]
                tx = tiles.multi_index[0]
                ty = tiles.multi_index[1]
                if not (0 <= tx+level.x-offset_x < 100 and 0 <= ty+level.y-offset_y < 50): continue   # Ignore offscreen
                console.rgb[["ch", "fg"]][ty+level.y-offset_y, tx+level.x-offset_x] = ch, col

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
        world = g.world if len(self.dungeon_floors) == 0 else self.dungeon_floors[-1].world
        (player,) = g.world.Q.all_of(components=[], tags=[IsPlayer])
        match event:
            # Movement
            case tcod.event.KeyDown(sym=sym) if sym in DIRECTION_KEYS:
                player_pos = player.components[Position]
                
                # Check for actor collision
                for actor in world.Q.all_of(tags=[player_pos + DIRECTION_KEYS[sym]], components=[Actor]): 
                    actor.components[Actor].on_interact()
                    return
                g.current_actor = None
                
                # Check for transfers
                for transferobj in world.Q.all_of(tags=[player_pos + DIRECTION_KEYS[sym]], components=[Transfer]): 
                    transfer = transferobj.components[Transfer]
                    if transfer.is_down:
                        self.go_down_floor(exit_transfer_x=player_pos.x, exit_transfer_y=player_pos.y)
                    else:
                        self.go_up_floor()
                        player.components[Position] = Position(transfer.transfer_x, transfer.transfer_y)
                        player_pos = player.components[Position]
                    return
                
                # Check for overworld collision
                if len(self.dungeon_floors) == 0:
                    # Terrain
                    # val = g.grid[28 + DIRECTION_KEYS[sym][0], 19 + DIRECTION_KEYS[sym][1]]
                    # if val > NOISE_COLLISION_THRESH: return None
                    
                    # LDtk levels
                    found_level = False
                    for level in world.Q.all_of(components=[LevelContainer]):
                        if not level.components[LevelContainer].within_bounds(player_pos.x, player_pos.y): continue
                        found_level = True
                        self.update_area_name(level.components[LevelContainer].field_instances["name"])
                        if level.components[LevelContainer].is_space_occupied(player_pos.x + DIRECTION_KEYS[sym][0], player_pos.y+DIRECTION_KEYS[sym][1]): return
                        
                    if not found_level: self.update_area_name("Woods of Gloom")
                
                # Check for dungeon collision
                else:
                    dungeon = self.dungeon_floors[-1]
                    if dungeon.map[player_pos.x + DIRECTION_KEYS[sym][0], player_pos.y + DIRECTION_KEYS[sym][1]] == 1: return
                    
                    # Enemy movement
                    #for enemy in world.Q.all_of(components=[Enemy]):
                        #enemy.components[Enemy].enemy_tick(player=player_pos)
                
                
                player.components[Position] += DIRECTION_KEYS[sym]
                
                # Pick up gold on the same space as the player
                for gold in world.Q.all_of(components=[Gold], tags=[player.components[Position], IsItem]):
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
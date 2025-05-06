"""Collection of common components."""
from __future__ import annotations
from typing import Final, Self
import attrs
import tcod.ecs.callbacks
from tcod.ecs import Entity
import game.g as g
import numpy as np
from game.tags import IsPlayer
from random import Random
import math
import libtcodpy

def clamp(value, min_value, max_value):
        return max(min(value, max_value), min_value)
    
@attrs.define(frozen=True)
class Position:
    """An entity's position."""
    x: int
    y: int
    
    def __add__(self, direction: tuple[int, int]) -> Self:
        """Add a vector to this position."""
        x, y = direction
        return self.__class__(self.x + x, self.y + y)
    
@tcod.ecs.callbacks.register_component_changed(component=Position)
def on_position_changed(entity: Entity, old: Position | None, new : Position | None) -> None:
    """Mirror position components as a tag."""
    if old == new: return
    if old is not None: entity.tags.discard(old)
    if new is not None: entity.tags.add(new)
    
@attrs.define(frozen=True)
class Graphic:
    """An entity's icon and color."""
    ch: int = ord("!")                              # Character
    fg: tuple[int, int, int] = (255, 255, 255)      # Color

# @attrs.define(frozen=True)
# class Box:

@attrs.define(frozen=True)
class Actor:
    """Displays text on interaction"""
    
    name: str = "Sign"
    text: str = "This sign is blank."
    interact_msg: str = "You read a sign"
    choices: tuple[(str, str)] = {}
    
    def on_interact(self):
        if g.current_actor == self: return
        g.current_actor = self
        g.log.add_item(self.interact_msg)
     
@attrs.define(frozen=False)
class Dungeon:
    """Stores all data related to a dungeon."""
    x: int = 0
    y: int = 0
    max_depth: int = 3
    width: int = 100
    height: int = 100
    seed: int = 12345

    rooms: list[tcod.bsp.BSP] = attrs.field(init=False)
    door_room: tcod.bsp.BSP = attrs.field(init=False)
    map: np.ndarray = attrs.field(init=False)
    rng: Random = attrs.field(init=False)
    bsp: tcod.bsp.BSP = attrs.field(init=False)    
    
    def __init__(self, x: int, y: int, width: int, height: int, seed: int = 12345, max_depth: int = 3, world: tcod.ecs.Registry = None):
        super().__init__()
        
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.seed = seed
        self.rng = Random(seed)
        self.bsp = tcod.bsp.BSP(x=x, y=y, width=width, height=height)
        self.map = np.ones(shape=(width, height))
        self.rooms = []
        
        MIN_WIDTH = 5
        MIN_HEIGHT = 5
        
        self.max_depth = max_depth
        
        # Generate BSP
        self.bsp.split_recursive(
            depth=self.max_depth, 
            min_width=MIN_WIDTH+1, 
            min_height=MIN_HEIGHT+1,
            max_horizontal_ratio=1.5, 
            max_vertical_ratio=1.5
        )
        
        # Generate rooms and corridors
        for node in self.bsp.inverted_level_order():
            # Room
            if not node.children:
                minx = node.x + 1
                maxx = node.x + node.width - 1
                miny = node.y + 1
                maxy = node.y + node.height - 1
                
                # Randomize room size
                minx = self.rng.randint(minx, maxx - MIN_WIDTH + 1)
                miny = self.rng.randint(miny, maxy - MIN_HEIGHT + 1)
                maxx = self.rng.randint(minx + MIN_WIDTH - 2, maxx)
                maxy = self.rng.randint(miny + MIN_HEIGHT - 2, maxy)
                
                node.x = minx
                node.y = miny
                node.width = maxx-minx + 1
                node.height = maxy-miny + 1
                
                # Dig out room
                for dx in range(minx, maxx + 1):
                    for dy in range(miny, maxy + 1):
                        self.map[dx, dy] = 0      # 1 = blocked, 0 = unblocked
                                                # TODO: Add attributes for `blocked`, `blocked_sight`, and `visited`
                                                
                self.rooms.append(node) #((minx + maxx) / 2, (miny + maxy) / 2))
                
            # Corridor
            else:
                left, right = node.children
                node.x = min(left.x, right.x)
                node.y = min(left.y, right.y)
                node.width = max(left.x+left.width, right.x+right.width) - node.x
                node.height = max(left.y+left.height, right.y+right.height) - node.y
                
                if node.horizontal:
                    if left.x + left.width - 1 < right.x or right.x + right.width - 1 < left.x:
                        x1 = self.rng.randint(left.x, left.x + left.width - 1)
                        x2 = self.rng.randint(right.x, right.x + right.width - 1)
                        y = self.rng.randint(left.y + left.height, right.y)
                        self.vline_up(x1, y-1)
                        self.hline(x1, y, x2)
                        self.vline_down(x2, y+1)
                        
                    else:
                        minx = max(left.x, right.x)
                        maxx = min(left.x + left.width - 1, right.x + right.width - 1)
                        x = self.rng.randint(minx, maxx)
                        
                        while x > self.width - 1:
                            x -= 1
                        
                        self.vline_down(x, right.y)
                        self.vline_up(x, right.y - 1)
                
                else:
                    if left.y + left.height - 1 < right.y or right.y + right.height - 1 < left.y:
                        y1 = self.rng.randint(left.y, left.y + left.height - 1)
                        y2 = self.rng.randint(right.y, right.y + right.height - 1)
                        x = self.rng.randint(left.x + left.width, right.x)
                        self.hline_left(x-1, y1)
                        self.vline(x, y1, y2)
                        self.hline_right(x+1, y2)
                        
                    else:
                        miny = max(left.y, right.y)
                        maxy = min(left.y + left.height - 1, right.y + right.height - 1)
                        y = self.rng.randint(miny, maxy)
                        
                        while y > self.height - 1:
                            y -= 1
                        
                        self.hline_left(right.x-1, y)
                        self.hline_right(right.x, y)
                        
        # Remove any 1-char width walls        
        for ry in range(self.height-1):
            for rx in range(self.width-1):
                if self.map[rx, ry] != 1: continue
                if self.map[rx-1, ry] == 0 and self.map[rx+1, ry] == 0:
                    self.map[rx, ry] = 0
                    
        for rx in range(self.width-2):
            for ry in range(self.height-2):            
                if self.map[rx, ry] != 1: continue
                if self.map[rx, ry-1] == 0 and self.map[rx, ry+1] == 0:
                    self.map[rx, ry] = 0
                    
        # Restore border of dungeon
        self.map[0] = np.ones(self.height)
        self.map[self.width-1] = np.ones(self.height)
        self.map[:, 0] = np.ones(self.width)
        self.map[:, self.height-1] = np.ones(self.width)
        
        # Move player
        player_room = self.rooms[self.rng.randint(0, len(self.rooms)-1)]
        (player,) = world.Q.all_of(components=[], tags=[IsPlayer])
        player.components[Position] = Position(player_room.x + self.rng.randint(1, player_room.width-2), player_room.y + self.rng.randint(1, player_room.height-2))
        
        # Place entrance in same room as player
        up_door = world[object()]
        # This sucks ass
        up_door.components[Position] = Position(player_room.x + self.rng.randint(1, player_room.width-2), player_room.y + self.rng.randint(1, player_room.height-2))
        while(player.components[Position].x == up_door.components[Position].x and player.components[Position].y == up_door.components[Position].y):
            up_door.components[Position] = Position(player_room.x + self.rng.randint(1, player_room.width-2), player_room.y + self.rng.randint(1, player_room.height-2))
        up_door.components[Graphic] = Graphic(ord("<"), fg=(255, 255, 255))
        
        
        # Place exit
        self.door_room = self.rooms[self.rng.randint(0, len(self.rooms)-1)]
        while player_room == self.door_room:
            self.door_room = self.rooms[self.rng.randint(0, len(self.rooms)-1)]
            
        down_door = world[object()]
        down_door.components[Position] = Position(self.door_room.x + self.rng.randint(1, self.door_room.width-2), self.door_room.y + self.rng.randint(1, self.door_room.height-2))
        down_door.components[Graphic] = Graphic(ord(">"), fg=(255, 255, 255))
        
            
    # https://www.roguebasin.com/index.php?title=Complete_Roguelike_Tutorial,_using_Python%2Blibtcod,_extras#BSP_Dungeon_Generator
        
    # TODO - move to dedicated dungeon file later
    def vline(self, x, y1, y2):
        if y1 > y2:
            y1,y2 = y2,y1

        for y in range(y1,y2+1):
            self.map[x, y] = 0
        
    def vline_up(self, x, y):
        while y >= 0 and self.map[x, y] == 1:
            self.map[x, y] = 0
            y -= 1
            
    def vline_down(self, x, y):
        while y < self.height and self.map[x, y] == 1:
            self.map[x, y] = 0
            y += 1
            
    def hline(self, x1, y, x2):
        if x1 > x2:
            x1,x2 = x2,x1
        for x in range(x1,x2+1):
            self.map[x, y] = 0
            
    def hline_left(self, x, y):
        while x >= 0 and self.map[x, y] == 1:
            self.map[x, y] = 0
            x -= 1
            
    def hline_right(self, x, y):
        while x < self.width and self.map[x, y] == 1:
            self.map[x, y] = 0
            x += 1
            
            
                
            
        
    
    # def get_closest_coords(self, node: tcod.bsp.BSP, other: tcod.bsp.BSP):
    #     """Returns coords within `other`'s bounds that are the closest to `node`'s."""
    #     x = node.x
    #     y = node.y
    #     return (clamp(x, other.x+1, other.x+other.width-2), clamp(y, other.y+1, other.y+other.height-2))
    
    # def get_nearest_room(self, node: tcod.bsp.BSP, use_max: bool) -> tcod.bsp.BSP:
    #     if not self.bsp.contains(node.x, node.y): return None
    #     cur = node
    #     x = node.x
    #     y = node.y
    #     w = node.width
    #     h = node.height
    #     nx = node.x+1 + (node.width-2 if use_max else 0)
    #     ny = node.y+1 + (node.height-2 if use_max else 0)

    #     while cur.children:
    #         node1, node2 = cur.children
    #         if cur.horizontal:
    #             cur = node2 if ny >= cur.position else node1
    #         else:
    #             cur = node2 if nx >= cur.position else node1
    #     return cur

@attrs.define(frozen=False)
class LevelContainer:
    """Stores JSON data for handcrafted levels."""
    
    # Private fields
    x: int = attrs.field(init=False)
    y: int = attrs.field(init=False)
    width: int = attrs.field(init=False)
    height: int = attrs.field(init=False)
    intgrid: np.ndarray = attrs.field(init=False)
    tiles: np.ndarray = attrs.field(init=False)
    id: str = attrs.field(init=False)
    
    def __init__(self, data: map) -> None:
        self.x = data["x"]
        self.y = data["y"]
        self.width = data["width"]
        self.height = data["height"]
        self.intgrid = np.reshape(data["intgrid"], (self.width, self.height), order="F")
        
        x, y, t = [], [], []
        for tile in data["tiles"]:
            x.append(tile["x"])
            y.append(tile["y"])
            t.append(tile["t"])        
        tilesnd = np.zeros((self.width, self.height))
        tilesnd[x, y] = t
        self.tiles = tilesnd
        self.id = data["id"]
    
    # Top left corner is (0, 0) level local space
    # def level_visible(self, x: int, y: int, w: int, h: int) -> bool:
    #     """Returns true if any part of the level is on-screen."""
    #     return max(x, x+w) > min(self.x, self.x+self.width) and max(self.x, self.x+self.width)
    
    def within_bounds(self, x: int, y: int) -> bool:
        """Returns true if the coordinates are within the bounding rectangle of the level."""
        return 0 <= x - self.x <= self.width and 0 <= y - self.y <= self.height
    
    def is_space_occupied(self, x: int, y: int) -> bool:
        """Returns true if intgrid tile is marked as solid."""
        return self.intgrid[(x-self.x)%self.width, (y-self.y)%self.height] == 1
    
    
    

Gold: Final = ("Gold", int)
"""Amount of gold."""
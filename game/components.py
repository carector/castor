"""Collection of common components."""
from __future__ import annotations
from typing import Final, Self
import attrs
import tcod.ecs.callbacks
from tcod.ecs import Entity
import game.g as g
import numpy as np
from random import Random
import math

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
    x: int
    y: int
    max_depth: int
    width: int
    height: int
    seed: int = 12345

    #connections: 
    rng: Random = attrs.field(init=False)
    bsp: tcod.bsp.BSP = attrs.field(init=False)
    
    def __init__(self, x: int, y: int, width: int, height: int, seed: int = 12345, max_depth: int = 3):
        super().__init__()
        
        self.rng = Random(seed)
        self.bsp = tcod.bsp.BSP(x=x, y=y, width=width, height=height)
        
        MIN_WIDTH = 4
        MIN_HEIGHT = 4
        
        self.max_depth = max_depth
        
        # Generate rooms
        self.bsp.split_recursive(
            depth=self.max_depth, 
            min_width=MIN_WIDTH+3, 
            min_height=MIN_HEIGHT+3, 
            max_horizontal_ratio=1.5, 
            max_vertical_ratio=1.5
        )
        
        for node in self.bsp.inverted_level_order():
            # Generate rooms and add corridors between rooms
            if not node.children:
                # Randomize node values a bit
                #old_width = node.width
                old_height = node.height
                node.width = self.rng.randint(max(MIN_WIDTH, node.width//2), node.width)
                node.height = self.rng.randint(max(MIN_HEIGHT, node.height//2), node.height)
                # node.x += self.rng.randint(-(old_width - node.width), old_width - node.width)
                # node.y += self.rng.randint(-(old_height - node.height), old_height - node.height)//2
    
    def traverse(self, console):
        for node in self.bsp.inverted_level_order():
            self.traverse_node(console=console, node=node)
            
    def traverse_node(self, console, node: tcod.bsp.BSP):
        # TODO: https://www.roguebasin.com/index.php?title=Complete_Roguelike_Tutorial,_using_Python%2Blibtcod,_extras#BSP_Dungeon_Generator
        
        # Room
        if not node.children:
            minx = node.x + 1
            maxx = node.x + node.width - 1
            miny = node.y + 1
            maxy = node.y + node.height - 1
            
            node.x = minx
            node.y = miny
            node.width = maxx-minx + 1
            node.height = maxy-miny + 1
            
            # Dig
            #for x in range(minx, maxx):
                
            
        
    
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
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
class Transfer:
    """Transfers the player from one location to another."""
    transfer_x: int = 0
    transfer_y: int = 0
    is_down: bool = True       # Whether this leads to a lower dungeon floor
                        # If false, leads upwards 
    
    def __init__(self, transfer_x: int, transfer_y: int, is_down: bool) -> None:
        self.transfer_x = transfer_x
        self.transfer_y = transfer_y
        self.is_down = is_down

@attrs.define(frozen=False)
class LevelContainer:
    """Stores JSON data for handcrafted levels."""
    
    # Private fields
    x: int = attrs.field(init=False)
    y: int = attrs.field(init=False)
    width: int = attrs.field(init=False)
    height: int = attrs.field(init=False)
    colors: np.ndarray = attrs.field(init=False)
    collision: np.ndarray = attrs.field(init=False)
    field_instances: map = attrs.field(init=False)
    
    tiles: np.ndarray = attrs.field(init=False)
    id: str = attrs.field(init=False)
    
    def __init__(self, data: map, world: tcod.ecs.Registry) -> None:
        self.x = data["x"]
        self.y = data["y"]
        self.width = data["width"]
        self.height = data["height"]
        self.colors = np.reshape(data["colors"], (self.width, self.height), order="F")
        self.collision = np.reshape(data["collision"], (self.width, self.height), order="F")
        
        x, y, t = [], [], []
        for tile in data["tiles"]:
            x.append(tile["x"])
            y.append(tile["y"])
            t.append(tile["t"])
        tilesnd = np.zeros((self.width, self.height))
        tilesnd[x, y] = t
        self.tiles = tilesnd
        self.id = data["id"]
        
        self.field_instances = {}
        for fi in data["field_instances"]:
            self.field_instances[fi["id"]] = fi["value"]
            
        for entity in data["entities"]:
            e = world[object()]
            e.components[Position] = Position(entity["x"] + self.x, entity["y"] + self.y)
            
            match entity["id"]:
                case "transfer":
                    e.components[Transfer] = Transfer(0, 0, True)
                    e.components[Graphic] = Graphic(ch=ord(">"))
    
    # Top left corner is (0, 0) level local space
    # def level_visible(self, x: int, y: int, w: int, h: int) -> bool:
    #     """Returns true if any part of the level is on-screen."""
    #     return max(x, x+w) > min(self.x, self.x+self.width) and max(self.x, self.x+self.width)
    
    def within_bounds(self, x: int, y: int) -> bool:
        """Returns true if the coordinates are within the bounding rectangle of the level."""
        return 0 <= x - self.x <= self.width and 0 <= y - self.y <= self.height
    
    def is_space_occupied(self, x: int, y: int) -> bool:
        """Returns true if collision tile is marked as solid."""
        return self.collision[(x-self.x)%self.width, (y-self.y)%self.height] == 1
    
    
    

Gold: Final = ("Gold", int)
"""Amount of gold."""
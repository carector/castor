"""Collection of world gen tools."""
from __future__ import annotations
from random import Random
from tcod.ecs import Registry
from game.components import Gold, Graphic, Position
from game.tags import IsActor, IsItem, IsPlayer

import os
import json

def new_world() -> Registry:
    world = Registry()          # Entities are referenced with the syntax world[unique_id]
                                # New objects are created with new_entity = world[object()] because object() is always unique
                                # world[None] is used to define global entities
    
    rng = world[None].components[Random] = Random()
    
    # Test import from LDtk map
    level = json.loads(open("data/ldtk/data/Level_0.json", 'r').read())
    layer = level["layerInstances"][1]
    width = layer["__cWid"]
    height = layer["__cHei"]
    intgrid = layer["intGridCsv"]
    tileIndex = 0
    for y in range(height):
        for x in range(width):
            val = intgrid[tileIndex]
            if not val == 0:
                color = (255, 255, 255)
                match val:
                    case 2: color = (0, 255, 0)
                    case 3: color = (311, 3, 50)
                    case 5: color = (0, 0, 255)
                tile = world[object()]
                tile.components[Position] = Position(x, y)
                tile.components[Graphic] = Graphic(ord("+"), fg=color)                    
            tileIndex += 1
    
    
    # Define player
    player = world[object()]
    player.components[Position] = Position(5, 5)
    player.components[Graphic] = Graphic(ord("@"), fg=(255, 106, 0)) # 24 100 100
    player.components[Gold] = 0
    player.tags |= {IsPlayer, IsActor}
    
    # Random gold placement
    for _ in range(10):
        g = world[object()]
        g.components[Position] = Position(rng.randint(0, 20), rng.randint(0, 20))
        g.components[Graphic] = Graphic(ord("$"), fg=(255, 255, 0))
        g.components[Gold] = rng.randint(1, 10)
        g.tags |= {IsItem}
    
    return world
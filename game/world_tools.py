"""Collection of world gen tools."""
from __future__ import annotations
from random import Random
from tcod.ecs import Registry
from game.components import Gold, Graphic, Position, Actor, LevelContainer, Dungeon
from game.tags import IsActor, IsItem, IsPlayer
from game import g

import tcod.noise
import tcod.bsp

import os
import json

def new_world() -> Registry:
    world = Registry()          # Entities are referenced with the syntax world[unique_id]
                                # New objects are created with new_entity = world[object()] because object() is always unique
                                # world[None] is used to define global entities
    
    rng = world[None].components[Random] = Random()
    
    # Define player
    player = world[object()]
    player.components[Position] = Position(0, 0)
    player.components[Graphic] = Graphic(ord("@"), fg=(255, 106, 0)) # 24 100 100
    player.components[Gold] = 0
    player.tags |= {IsPlayer, IsActor}
    
    # Actor test
    actor = world[object()]
    actor.components[Actor] = Actor(
        name="Evil sign", 
        text="Welcome to evil town. We're all evil here. We're really good at it.\n\nDon't test us.",
        choices={("O-okay, I'm sorry...", "Leave")})
    actor.components[Graphic] = Graphic(ord("Φ"), fg=(127+32, 51+32, 0))
    actor.components[Position] = Position(-8, 1)
    actor.tags |= {IsActor}
    
    # Dungeon test
    g.dungeon = Dungeon(x=0, y=0, width=56, height=36, max_depth=5, world=world)
    
    # Import LDtk levels
    for _, _, files in os.walk("data/ldtk/data", topdown=False):
        for name in files:
            level_data = json.loads(open(f"data/ldtk/data/{name}", 'r').read())
            level = world[object()]
            level.components[LevelContainer] = LevelContainer(level_data)
    
    # Random gold placement
    # for _ in range(10):
    #     g = world[object()]
    #     g.components[Position] = Position(rng.randint(0, 20), rng.randint(0, 20))
    #     g.components[Graphic] = Graphic(ord("$"), fg=(255, 255, 0))
    #     g.components[Gold] = rng.randint(1, 10)
    #     g.tags |= {IsItem}
    
    return world
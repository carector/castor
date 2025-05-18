"""Collection of world gen tools."""
from __future__ import annotations
from random import Random
from tcod.ecs import Registry
import tcod.ecs
import game.components as gc
from game.tags import IsActor, IsItem, IsPlayer
from game import g
import attrs
import tcod.noise
import tcod.bsp
import numpy as np
import os
import json

def new_world() -> Registry:
    world = Registry()          # Entities are referenced with the syntax world[unique_id]
                                # New objects are created with new_entity = world[object()] because object() is always unique
                                # world[None] is used to define global entities
    
    rng = world[None].components[Random] = Random()
    
    # Define player
    player = world[object()]
    player.components[gc.Position] = gc.Position(-11, 5)
    player.components[gc.Graphic] = gc.Graphic(ord("@"), fg=(255, 106, 0)) # 24 100 100
    player.components[gc.Gold] = 0
    player.tags |= {IsPlayer, IsActor}
    
    # Actor test
    actor = world[object()]
    actor.components[gc.Actor] = gc.Actor(
        name="Evil sign", 
        text="Welcome to evil town. We're all evil here. We're really good at it.\n\nDon't test us.",
        choices={("O-okay, I'm sorry...", "Leave")})
    actor.components[gc.Graphic] = gc.Graphic(ord("Φ"), fg=(127+32, 51+32, 0))
    actor.components[gc.Position] = gc.Position(-8, 1)
    actor.tags |= {IsActor}
    
    # Dungeon entrance
    #dungeon_entrance = world[object()]
    #dungeon_entrance.components[Position] = Position(0, -10)
    #dungeon_entrance.components[Transfer] = Transfer(0, 0, True)
    #dungeon_entrance.components[Graphic] = Graphic(ord(">"), fg=(255, 255, 255))
    
    #dungeon_entrance.tags |= {}
    
    # Import LDtk levels
    for _, _, files in os.walk("data/ldtk/data", topdown=False):
        for name in files:
            level_data = json.loads(open(f"data/ldtk/data/{name}", 'r').read())
            level = world[object()]
            level.components[gc.LevelContainer] = gc.LevelContainer(level_data, world=world)
    
    # Random gold placement
    # for _ in range(10):
    #     g = world[object()]
    #     g.components[Position] = Position(rng.randint(0, 20), rng.randint(0, 20))
    #     g.components[Graphic] = Graphic(ord("$"), fg=(255, 255, 0))
    #     g.components[Gold] = rng.randint(1, 10)
    #     g.tags |= {IsItem}
    
    return world

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
    map: tcod.map.Map = attrs.field(init=False)
    explored: np.ndarray = attrs.field(init=False)
    rng: Random = attrs.field(init=False)
    bsp: tcod.bsp.BSP = attrs.field(init=False)
    world: tcod.ecs.Registry = attrs.field(init=False)
    entrance: object = attrs.field(init=False)
    exit: object = attrs.field(init=False)
    
    def __init__(self, x: int, y: int, width: int, height: int, seed: int = 12345, max_depth: int = 3, exit_x: int = 0, exit_y: int = 0):
        super().__init__()
        
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.seed = seed
        self.rng = tcod.random.Random(seed)
        self.bsp = tcod.bsp.BSP(x=x, y=y, width=width, height=height)
        self.map = np.zeros(shape=(width, height), dtype = np.uint32)
        self.map = tcod.map.Map(width=width, height=height, order='F')
        self.explored = np.zeros(shape=(width, height), dtype=np.uint32, order='F')
        self.rooms = []
        self.world = Registry()
        
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
                        self.map.transparent[dx, dy] = True
                        self.map.walkable[dx, dy] = True
                                                
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
                if self.map.transparent[rx, ry]: continue
                if self.map.transparent[rx-1, ry] and self.map.transparent[rx+1, ry]:
                    self.map.transparent[rx, ry] = True
                    self.map.walkable[rx, ry] = True
                    
        for rx in range(self.width-2):
            for ry in range(self.height-2):            
                if self.map.transparent[rx, ry]: continue
                if self.map.transparent[rx, ry-1] and self.map.transparent[rx, ry+1]:
                    self.map.transparent[rx, ry] = True
                    self.map.walkable[rx, ry] = True
                    
        # Restore border of dungeon
        self.map.transparent[0] = np.zeros(self.height, dtype=np.bool)
        self.map.walkable[0] = np.zeros(self.height, dtype=np.bool)
        self.map.transparent[self.width-1] = np.zeros(self.height, dtype=np.bool)
        self.map.walkable[self.width-1] = np.zeros(self.height, dtype=np.bool)
        self.map.transparent[:, 0] = np.zeros(self.width, dtype=np.bool)
        self.map.walkable[:, 0] = np.zeros(self.width, dtype=np.bool)
        self.map.transparent[:, self.height-1] = np.zeros(self.width, dtype=np.bool)
        self.map.walkable[:, self.height-1] = np.zeros(self.width, dtype=np.bool)
        
        
        # Move player
        player_room = self.rooms[self.rng.randint(0, len(self.rooms)-1)]
        (player,) = g.world.Q.all_of(components=[], tags=[IsPlayer])
        player.components[gc.Position] = gc.Position(player_room.x + self.rng.randint(1, player_room.width-2), player_room.y + self.rng.randint(1, player_room.height-2))
        
        # Place entrance in same room as player
        up_door = self.world[object()]
        up_door.components[gc.Transfer] = gc.Transfer(exit_x, exit_y, False)
        self.entrance = up_door
        
        up_door.components[gc.Position] = gc.Position(player_room.x + self.rng.randint(1, player_room.width-2), player_room.y + self.rng.randint(1, player_room.height-2))
        while(player.components[gc.Position].x == up_door.components[gc.Position].x and player.components[gc.Position].y == up_door.components[gc.Position].y):
            up_door.components[gc.Position] = gc.Position(player_room.x + self.rng.randint(1, player_room.width-2), player_room.y + self.rng.randint(1, player_room.height-2))
        up_door.components[gc.Graphic] = gc.Graphic(ord("<"), fg=(255, 255, 255))
        
        # Place exit
        self.door_room = self.rooms[self.rng.randint(0, len(self.rooms)-1)]
        while player_room == self.door_room:
            self.door_room = self.rooms[self.rng.randint(0, len(self.rooms)-1)]
            
        down_door = self.world[object()]
        down_door.components[gc.Position] = gc.Position(self.door_room.x + self.rng.randint(1, self.door_room.width-2), self.door_room.y + self.rng.randint(1, self.door_room.height-2))
        down_door.components[gc.Graphic] = gc.Graphic(ord(">"), fg=(255, 255, 255))
        down_door.components[gc.Transfer] = gc.Transfer(0, 0, True)
        self.exit = down_door
        
        # Place test enemy
        enemy = self.world[object()]
        enemy_room = self.rooms[self.rng.randint(0, len(self.rooms)-1)]
        enemy.components[gc.Position] = gc.Position(enemy_room.x + self.rng.randint(1, enemy_room.width-2), enemy_room.y + self.rng.randint(1, enemy_room.height-2))
        enemy.components[gc.Graphic] = gc.Graphic(ord("F"), (255, 0, 0))
        enemy.components[gc.Enemy] = gc.Enemy(name="Foul Beast", path=tcod.path.AStar(cost=self.map))
        
        
            
    # https://www.roguebasin.com/index.php?title=Complete_Roguelike_Tutorial,_using_Python%2Blibtcod,_extras#BSP_Dungeon_Generator
    
    
    
    def vline(self, x, y1, y2):
        if y1 > y2:
            y1,y2 = y2,y1

        for y in range(y1,y2+1):
            self.map.transparent[x, y] = True
            self.map.walkable[x, y] = True    
        
    def vline_up(self, x, y):
        while y >= 0 and not self.map.transparent[x, y]:
            self.map.transparent[x, y] = True
            self.map.walkable[x, y] = True    
            y -= 1
            
    def vline_down(self, x, y):
        while y < self.height and not self.map.transparent[x, y]:
            self.map.transparent[x, y] = True
            self.map.walkable[x, y] = True    
            y += 1
            
    def hline(self, x1, y, x2):
        if x1 > x2:
            x1,x2 = x2,x1
        for x in range(x1,x2+1):
            self.map.transparent[x, y] = True
            self.map.walkable[x, y] = True    
            
    def hline_left(self, x, y):
        while x >= 0 and not self.map.transparent[x, y]:
            self.map.transparent[x, y] = True
            self.map.walkable[x, y] = True    
            x -= 1
            
    def hline_right(self, x, y):
        while x < self.width and not self.map.transparent[x, y]:
            self.map.transparent[x, y] = True
            self.map.walkable[x, y] = True    
            x += 1
                
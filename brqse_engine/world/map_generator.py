import random
from typing import Dict, Any, List, Tuple
from scripts.world_engine import Scene

# TILE CONSTANTS
TILE_WALL = 0
TILE_FLOOR = 1
TILE_COVER = 2
TILE_ENEMY = 3
TILE_DOOR = 4
TILE_HAZARD = 5
TILE_LOOT = 6
TILE_ENTRANCE = 7

class MapGenerator:
    """
    Generates map layouts with diverse objects and tags.
    """
    ROWS, COLS = 20, 20

    def __init__(self, chaos_manager=None):
        self.chaos = chaos_manager
        
    def generate_map(self, scene: Scene) -> Scene:
        # 1. Select Shape
        shape_type = "RECTANGLE"
        if "Tunnel" in scene.text: shape_type = "TUNNEL"
        if "Cavern" in scene.text or "Ruins" in scene.text: shape_type = "CAVE"
        
        grid = self._generate_shape(shape_type)
        
        # 2. Ports
        start_pos = (1, self.ROWS//2)
        end_pos = (self.COLS-2, self.ROWS//2)
        grid[end_pos[1]][end_pos[0]] = TILE_DOOR
        grid[start_pos[1]][start_pos[0]] = TILE_ENTRANCE
        
        # 3. Furnish with enriched objects
        grid, objects = self._furnish_biome(grid, scene.biome)
        
        # 4. Save
        scene.set_grid(grid, [start_pos], [end_pos], objects)
        
        if scene.encounter_type == "COMBAT":
            self._place_enemies(grid)
            
        return scene

    def _generate_shape(self, shape_type: str) -> List[List[int]]:
        grid = [[TILE_WALL for _ in range(self.COLS)] for _ in range(self.ROWS)]
        for y in range(2, self.ROWS-2):
            for x in range(2, self.COLS-2): grid[y][x] = TILE_FLOOR
        return grid

    def _furnish_biome(self, grid: List[List[int]], biome: str) -> Tuple[List[List[int]], List[Dict]]:
        interactables = []
        
        # Object Bank with Tags
        # added 'cover' and 'elevation' tags
        BANK = {
            "Barrel": ["smash", "search", "push", "cover"],
            "Crate": ["smash", "search", "push", "vault", "cover", "elevation"],
            "Table": ["climb", "push", "flip", "elevation"],
            "Logs": ["search", "vault", "cover"],
            "Stone": ["climb", "push", "cover", "elevation"],
            "Chandelier": ["break", "drop"],
            "Chest": ["open", "search", "smash", "cover"]
        }

        object_types = list(BANK.keys())

        for y in range(len(grid)):
            for x in range(len(grid[0])):
                if grid[y][x] == TILE_FLOOR:
                    r = random.random()
                    
                    if r > 0.95:
                        obj_type = random.choice(object_types)
                        interactables.append({
                            "x": x, "y": y, 
                            "type": obj_type, 
                            "tags": BANK[obj_type],
                            "is_blocking": True
                        })
                        grid[y][x] = TILE_LOOT 
                        
        return grid, interactables

    def _place_enemies(self, grid: List[List[int]]):
        count = random.randint(1, 4)
        placed = 0
        while placed < count:
            ex, ey = random.randint(5, self.COLS-2), random.randint(2, self.ROWS-2)
            if grid[ey][ex] == TILE_FLOOR:
                grid[ey][ex] = TILE_ENEMY
                placed += 1

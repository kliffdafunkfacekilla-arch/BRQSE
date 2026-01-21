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

class MapGenerator:
    """
    Generates map layouts (20x20 grids) for Scenes.
    """
    
    ROWS, COLS = 20, 20

    def __init__(self, chaos_manager=None):
        self.chaos = chaos_manager
        
    def generate_map(self, scene: Scene) -> Scene:
        """
        Populates a Scene object with a grid map based on its type/text.
        """
        # 1. Select Shape
        shape_type = "RECTANGLE"
        if "Tunnel" in scene.text: shape_type = "TUNNEL"
        if "Cavern" in scene.text or "Ruins" in scene.text: shape_type = "CAVE"
        
        grid = self._generate_shape(shape_type)
        
        # 2. Add Entrances/Exits (Heuristic: Left -> Right for now)
        entrances = [(1, self.ROWS//2)]
        exits = [(self.COLS-2, self.ROWS//2)]
        
        # Ensure path exists (Simple horizontal tunnel carve if blocked)
        # For now, shape generation guarantees connectivity usually
        
        # 3. Furnish (Biome)
        grid, loot_nodes = self._furnish_biome(grid, scene.biome, scene.encounter_type)
        
        # 4. Save to Scene
        scene.set_grid(grid, entrances, exits, loot_nodes)
        
        # 5. Place Spawn Points (for combat)
        # (This logic might move to GameLoop or stay here as metadata)
        # We can store spawns in loot_nodes or separate list if needed, 
        # but for now we follow the blueprint: grid stores "3" for Enemy?
        # Blueprint said: 20x20 array of tiles (0=Wall, 1=Floor, 2=Cover, 3=Enemy)
        
        if scene.encounter_type == "COMBAT":
            self._place_enemies(grid)
            
        return scene

    def _generate_shape(self, shape_type: str) -> List[List[int]]:
        # Initialize solid walls
        grid = [[TILE_WALL for _ in range(self.COLS)] for _ in range(self.ROWS)]
        
        if shape_type == "RECTANGLE":
            # Simple Room with padding
            for y in range(2, self.ROWS-2):
                for x in range(2, self.COLS-2):
                    grid[y][x] = TILE_FLOOR
                    
        elif shape_type == "TUNNEL":
            # Narrow corridor
            cy = self.ROWS // 2
            for x in range(1, self.COLS-1):
                grid[cy][x] = TILE_FLOOR
                grid[cy+1][x] = TILE_FLOOR
                if x % 5 == 0: # Niches
                    grid[cy-1][x] = TILE_FLOOR
                    grid[cy+2][x] = TILE_FLOOR

        elif shape_type == "CAVE":
            # Simple Cellular Automata or randomness
            for y in range(1, self.ROWS-1):
                for x in range(1, self.COLS-1):
                    if random.random() > 0.4:
                        grid[y][x] = TILE_FLOOR
            # Smoothing (skipped for brevity, just ensuring center path)
            cy = self.ROWS // 2
            for x in range(1, self.COLS-1):
                grid[cy][x] = TILE_FLOOR
                
        return grid

    def _furnish_biome(self, grid: List[List[int]], biome: str, encounter: str) -> Tuple[List[List[int]], List[Dict]]:
        loot_nodes = []
        
        # Biome Settings
        # (Floor Tile is 1 by default, usually Grass/Stone depending on texture pack. 
        # But we can override 1 with specific tiles if we had specific IDs for "SWAMP_GROUND")
        # For now, we reuse existing constants:
        # TILE_COVER (2) -> Trees/Pillars
        # TILE_HAZARD (5) -> Spikes/Mud
        
        chance_cover = 0.05
        chance_hazard = 0.02
        
        if biome == "SWAMP":
            chance_cover = 0.10 # More trees
            chance_hazard = 0.15 # Lots of mud/water (using HAZARD for now)
            
        elif biome == "TAVERN":
            chance_cover = 0.15 # Tables
            chance_hazard = 0.00
            
        # Add Hazards/Cover based on Biome
        for y in range(len(grid)):
            for x in range(len(grid[0])):
                if grid[y][x] == TILE_FLOOR:
                    # Random Cover
                    if random.random() < chance_cover:
                        grid[y][x] = TILE_COVER
                        
                    # Random Hazards (if High Chaos? or explicit biome trait)
                    elif random.random() < chance_hazard:
                        grid[y][x] = TILE_HAZARD

        # Place Loot (Chest)
        if random.random() < 0.3:
            # Find a floor tile
            for _ in range(10):
                lx, ly = random.randint(1, self.COLS-2), random.randint(1, self.ROWS-2)
                if grid[ly][lx] == TILE_FLOOR:
                    grid[ly][lx] = TILE_LOOT
                    loot_nodes.append({"x": lx, "y": ly, "type": "CHEST"})
                    break
                    
        return grid, loot_nodes

    def _place_enemies(self, grid: List[List[int]]):
        count = random.randint(1, 3)
        placed = 0
        attempts = 0
        while placed < count and attempts < 100:
            ex, ey = random.randint(5, self.COLS-2), random.randint(2, self.ROWS-2)
            if grid[ey][ex] == TILE_FLOOR:
                grid[ey][ex] = TILE_ENEMY
                placed += 1
            attempts += 1

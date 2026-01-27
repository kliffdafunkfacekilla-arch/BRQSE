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
TILE_DOOR = 2
TILE_TAVERN = 3
TILE_MERCHANT = 4
TILE_LOOT = 5
TILE_ENEMY = 6
TILE_HAZARD = 7

# Donjon Flags (Mirroring donjon_generator.py)
DJ_NOTHING     = 0
DJ_BLOCKED     = 1
DJ_ROOM        = 2
DJ_CORRIDOR    = 4
DJ_PERIMETER   = 8
DJ_ENTRANCE    = 16
DJ_DOOR        = 0x20000
DJ_STAIR_DN    = 0x200000
DJ_STAIR_UP    = 0x400000

class MapGenerator:
    """
    Generates map layouts with diverse objects and tags.
    """

    def __init__(self, chaos_manager=None):
        self.chaos = chaos_manager
        
        
        # 3. Furnish with enriched objects
        grid, objects = self._furnish_biome(grid, scene.biome, scene.encounter_type)
        
        # 4. Save
        scene.set_grid(grid, [start_pos], [end_pos], objects)
        
        if scene.encounter_type == "COMBAT" or "FINALE" in scene.text:
            count = random.randint(3, 6) if "FINALE" in scene.text else random.randint(1, 4)
            self._place_enemies(grid, count)
        elif scene.encounter_type == "STEALTH":
            # Fewer enemies, but they are stationary or in key spots
            self._place_enemies(grid, 2)
            
        return scene

    def _generate_shape(self, shape_type: str) -> List[List[int]]:
        grid = [[TILE_WALL for _ in range(self.COLS)] for _ in range(self.ROWS)]
        for y in range(2, self.ROWS-2):
            for x in range(2, self.COLS-2): grid[y][x] = TILE_FLOOR
        return grid

    def _furnish_biome(self, grid: List[List[int]], biome: str, enc_type: str = "EMPTY") -> Tuple[List[List[int]], List[Dict]]:
        interactables = []
        
        # Standard Obstacles
        BANK = {
            "Barrel": ["smash", "search", "push", "cover"],
            "Crate": ["smash", "search", "push", "vault", "cover", "elevation"],
            "Table": ["climb", "push", "flip", "elevation"],
            "Logs": ["search", "vault", "cover"],
            "Stone": ["climb", "push", "cover", "elevation"],
            "Chandelier": ["break", "drop"],
            "Chest": ["open", "search", "smash", "cover"]
        }

        # Special Objects by Encounter Type
        SPECIALS = {
            "SOCIAL": {"NPC": ["talk", "trade"], "Campfire": ["rest", "cook"]},
            "PUZZLE": {"Lever": ["pull"], "Statue": ["inspect", "rotate"], "Pedestal": ["place"]},
            "DECISION": {"Altar": ["pray", "defile"], "Cage": ["open", "unlock"], "Mystic Fountain": ["drink"]},
            "STEALTH": {"Curtain": ["hide", "peek"], "Wardrobe": ["hide", "search"]},
            "TREASURE": {"Ornate Chest": ["unlock", "search"], "Pile of Gold": ["loot"]},
            "SAFE_HAVEN": {"Bedroll": ["rest"], "Repair Kit": ["repair"]}
        }

        object_types = list(BANK.keys())
        specials = SPECIALS.get(enc_type, {})

        for y in range(len(grid)):
            for x in range(len(grid[0])):
                if grid[y][x] == TILE_FLOOR:
                    r = random.random()
                    
                    # Place Specials with higher priority but lower frequency
                    if specials and r > 0.98:
                        obj_type = random.choice(list(specials.keys()))
                        interactables.append({
                            "x": x, "y": y, 
                            "type": obj_type, 
                            "tags": specials[obj_type],
                            "is_blocking": True
                        })
                        grid[y][x] = TILE_LOOT
                    elif r > 0.95:
                        obj_type = random.choice(object_types)
                        interactables.append({
                            "x": x, "y": y, 
                            "type": obj_type, 
                            "tags": BANK[obj_type],
                            "is_blocking": True
                        })
                        grid[y][x] = TILE_LOOT 
                        
        return grid, interactables

    def _place_enemies(self, grid: List[List[int]], count: int = 1):
        placed = 0
        while placed < count:
            ex, ey = random.randint(5, self.COLS-2), random.randint(2, self.ROWS-2)
            if grid[ey][ex] == TILE_FLOOR:
                grid[ey][ex] = TILE_ENEMY
                placed += 1

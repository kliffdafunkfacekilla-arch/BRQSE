import random
from typing import Dict, Any, List, Tuple
from brqse_engine.world.world_system import Scene

from brqse_engine.world.donjon_generator import Cell

# TILE CONSTANTS (Synchronized with Arena.tsx)
# Note: Arena.tsx logic handles both simple ints (Old Generator) and Donjon Flags (New Generator)
# But for object placement we must respect the bitmask.

class MapGenerator:
    """
    Generates map layouts with diverse objects and tags.
    """

    def __init__(self, chaos_manager=None):
        self.chaos = chaos_manager

    def furnish_biome(self, grid: List[List[int]], biome: str, enc_type: str = "EMPTY") -> List[Dict]:
        """
        Populates a Donjon-generated grid with interactive objects.
        Respects Cell flags to avoid blocking doors/stairs.
        Returns a list of object dicts.
        """
        interactables = []
        rows = len(grid)
        cols = len(grid[0])
        
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

        for y in range(rows):
            for x in range(cols):
                cell_val = grid[y][x]
                
                # Check for Valid Floor (Must be a Room or Corridor)
                # AND NOT Blocking features (Door, Stairs, Blocked)
                if (cell_val & Cell.ROOM) and not (cell_val & (Cell.DOORSPACE | Cell.STAIR_DN | Cell.STAIR_UP | Cell.BLOCKED)):
                    
                    # Density Check (approx 5% chance per tile)
                    r = random.random()
                    
                    # Place Specials (Rare: 0.5% chance)
                    if specials and r > 0.995:
                        obj_type = random.choice(list(specials.keys()))
                        interactables.append({
                            "type": obj_type, 
                            "name": obj_type,
                            "x": x, "y": y, 
                            "tags": specials[obj_type],
                            "is_blocking": True
                        })
                        # NOTE: We do NOT modify the grid here because we don't want to break the Donjon bitmask.
                        # The client (Arena.tsx) renders objects on top.
                        
                    # Place Standard (Common: 3% chance)
                    elif r > 0.97:
                        obj_type = random.choice(object_types)
                        interactables.append({
                            "type": obj_type, 
                            "name": obj_type,
                            "x": x, "y": y, 
                            "tags": BANK[obj_type],
                            "is_blocking": True
                        })
                        
        return interactables

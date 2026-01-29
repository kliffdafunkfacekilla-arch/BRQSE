
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from brqse_engine.world.donjon_generator import DonjonGenerator, Cell
from brqse_engine.world.map_generator import MapGenerator

def test_map_population():
    print("[TEST] Initializing Generators...")
    dg = DonjonGenerator(seed=12345)
    mg = MapGenerator()
    
    print("[TEST] Generating Grid...")
    map_data = dg.generate(width=21, height=21)
    grid = map_data["grid"]
    
    print("[TEST] Furnishing Biome (Dungeon)...")
    objects = mg.furnish_biome(grid, "Dungeon", "SOCIAL")
    
    print(f"[TEST] Generated {len(objects)} objects.")
    
    if len(objects) == 0:
        print("[FAIL] No objects generated!")
        return
        
    for obj in objects[:5]:
        print(f"  - {obj['type']} at ({obj['x']}, {obj['y']}) Tags: {obj.get('tags')}")
        
    # Verify no objects on bad tiles
    valid = True
    for obj in objects:
        x, y = obj['x'], obj['y']
        cell = grid[y][x]
        if cell & (Cell.DOORSPACE | Cell.STAIR_DN | Cell.STAIR_UP):
            print(f"[FAIL] Object {obj['type']} placed on blocked tile: {cell}")
            valid = False
            
    if valid:
        print("[SUCCESS] All objects placed on valid tiles.")

if __name__ == "__main__":
    test_map_population()

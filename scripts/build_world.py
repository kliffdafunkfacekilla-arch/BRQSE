import sys
import os
import json
import random

# Add project root to path so imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from brqse_engine.world.donjon_generator import DonjonGenerator, Cell
from brqse_engine.world.story_director import StoryDirector
from brqse_engine.world.campaign_logger import CampaignLogger # NEW IMPORT

SAVE_DIR = "Saves/WorldStack"

def build_stack(depth=5):
    print("🌍 Starting World Construction...")
    
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
        
    # 1. Initialize Logger
    logger = CampaignLogger()
    logger.log(0, "SYSTEM", f"World Generation Started. Seed: {random.randint(1,9999)}")

    generator = DonjonGenerator()
    director = StoryDirector()
    
    manifest = {
        "depth": depth,
        "seed": generator.seed,
        "levels": {}
    }

    # We need to track where the stairs down were on the previous level
    # to align the stairs up on the new level.
    prev_down_coords = None

    for level in range(1, depth + 1):
        print(f"🔨 Generating Level {level}...")
        
        # 1. Generate Geometry
        map_data = generator.generate(width=51, height=41)
        grid = map_data["grid"]
        rooms = list(map_data["rooms"].values())

        # 2. Align Connectivity (Stairs)
        # Entry (Stairs Up)
        if prev_down_coords:
             # Find room closest to where the player came down from
             # For now, simplistic matching:
             start_room = rooms[0] # Simply pick Room 1 as entry for robustness
        else:
             start_room = rooms[0]
        
        sx, sy = start_room["center"]
        grid[sy][sx] |= Cell.STAIR_UP
        map_data["entry_point"] = (sx, sy)

        # Exit (Stairs Down)
        if level < depth:
            end_room = rooms[-1]
            ex, ey = end_room["center"]
            grid[ey][ex] |= Cell.STAIR_DN
            prev_down_coords = (ex, ey)
        
        # 3. Run ASI (Story Director)
        director.direct_scene(map_data, level, logger)

        # 4. Serialize grid (IntFlag not JSON serializable by default)
        # Convert the IntFlag grid to simple Integers
        serializable_grid = [[int(c) for c in row] for row in grid]
        map_data["grid"] = serializable_grid

        # 5. Save Level
        filename = f"level_{level}.json"
        with open(f"{SAVE_DIR}/{filename}", "w") as f:
            json.dump(map_data, f)
            
        manifest["levels"][str(level)] = filename
        
    logger.log(0, "SYSTEM", "World Generation Complete.")

    # Save Manifest
    with open(f"{SAVE_DIR}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print("✅ Stack Construction Complete.")

if __name__ == "__main__":
    build_stack()

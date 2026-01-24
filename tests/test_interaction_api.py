import sys
import os
sys.path.append(os.getcwd())

from brqse_engine.core.game_loop import GameLoopController
from scripts.world_engine import ChaosManager, Scene
from unittest.mock import MagicMock

# Constants
TILE_FLOOR = 1
TILE_LOOT = 6

def test_interaction():
    print("Testing Interaction Logic...")
    chaos = MagicMock()
    chaos.chaos_level = 0
    chaos.chaos_clock = 0
    chaos.roll_tension.return_value = "SAFE"
    chaos.add_tension = MagicMock()
    
    loop = GameLoopController(chaos)
    
    # Setup Scene with Interactable
    scene = Scene("Test Room")
    grid = [[TILE_FLOOR for _ in range(20)] for _ in range(20)]
    
    # Place Crate at 2,2
    grid[2][2] = TILE_LOOT
    interactables = [{
        "x": 2, "y": 2,
        "type": "Crate",
        "tags": ["push", "smash"],
        "is_blocking": True
    }]
    
    scene.set_grid(grid, [], [], interactables)
    loop.active_scene = scene
    loop.player_pos = (2, 3) # Adjacent
    loop.state = "EXPLORE"
    # Sync interactables
    loop.interactables = {(n['x'], n['y']): n for n in interactables}
    
    # 1. Test Options
    print("\n--- Testing Options ---")
    opts = loop.get_interaction_options(2, 2)
    print(f"Options at 2,2: {opts}")
    if "Smash" in opts and "Push" in opts:
        print("SUCCESS: Options match tags.")
    else:
        print("FAILURE: Missing options.")
        
    # 2. Test Smas (Direct)
    print("\n--- Testing Smash ---")
    res = loop.handle_interact(2, 2, action="Smash")
    print(f"Smash Result: {res}")
    
    if res['success'] and (2,2) not in loop.interactables:
        print("SUCCESS: Crate smashed and removed.")
    else:
        print("FAILURE: Crate persists or smash failed.")

if __name__ == "__main__":
    test_interaction()

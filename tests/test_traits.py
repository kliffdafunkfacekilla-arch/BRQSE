import sys
import os
sys.path.append(os.getcwd())

from brqse_engine.core.game_loop import GameLoopController
from scripts.world_engine import ChaosManager, Scene
from unittest.mock import MagicMock

# Hardcoded to bypass import hell in test environment
TILE_WALL = 0
TILE_FLOOR = 1
TILE_HAZARD = 5

def test_traits():
    print("Testing Movement Traits...")
    chaos = MagicMock()
    # Mock properties needed by other classes
    chaos.chaos_level = 5 
    chaos.roll_tension.return_value = "SAFE"
    
    loop = GameLoopController(chaos)
    
    # Setup Custom Grid
    # 0,0 = Floor
    # 0,1 = Wall (Climb test)
    # 0,2 = Hazard (Wing test)
    # 1,1 & 3,1 = Walls, 2,1 = Floor (Squeeze test)
    
    scene = Scene("Test Room")
    grid = [[TILE_FLOOR for _ in range(20)] for _ in range(20)]
    grid[1][0] = TILE_WALL
    grid[2][0] = TILE_HAZARD
    
    # Squeeze setup: Vertical Corridor at x=2
    # Walls at (1,1) and (3,1) with player at (2,1) moving to (2,2)?
    # Wait, check logic: "If moving horizontally... check up/down walls"
    # Let's test Horizontal Squeeze.
    # Player at (2,1). Move to (3,1).
    # Walls at (2,0) and (2,2)? No.
    # "If moving horizontally (to x+1), check walls at y-1 and y+1"
    # So if player at (2, 5) moving to (3, 5).
    # Walls at (3, 4) and (3, 6).
    grid[5][3] = TILE_FLOOR
    grid[4][3] = TILE_WALL
    grid[6][3] = TILE_WALL
    
    scene.grid = grid
    loop.active_scene = scene
    loop.player_pos = (0,0)
    
    # 1. Test Sticky Pads (Wall Climb)
    print("\n--- Sticky Pads Test ---")
    res = loop.handle_move(0, 1, traits=[])
    print(f"Normal vs Wall: {res['success']} (Expected: False)")
    
    res = loop.handle_move(0, 1, traits=["Sticky Pads"])
    print(f"Sticky vs Wall: {res['success']} (Expected: True)")
    if res['success']: loop.player_pos = (0,0) # Reset

    # 2. Test Huge Size (Squeeze)
    print("\n--- Huge Size Test ---")
    # Move to squeeze spot (3,5)
    loop.player_pos = (2, 5)
    loop.step_counter = 0
    res = loop.handle_move(3, 5, traits=[])
    print(f"Normal Step Cost: {loop.step_counter} (Expected: 1)")
    
    loop.player_pos = (2, 5)
    loop.step_counter = 0
    res = loop.handle_move(3, 5, traits=["Huge Size"])
    print(f"Huge Step Cost: {loop.step_counter} (Expected: 2 due to squeeze)")

    print("\nDone.")

if __name__ == "__main__":
    test_traits()

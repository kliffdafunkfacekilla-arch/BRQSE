
import sys
import os

# Setup path
sys.path.append(os.getcwd())

from brqse_engine.core.game_loop import GameLoopController
from scripts.world_engine import ChaosManager

def debug_movement():
    print("Initializing Game...")
    chaos = ChaosManager()
    controller = GameLoopController(chaos)
    
    state = controller.get_state()
    player_pos = state['player_pos']
    grid = state['grid']
    
    print(f"Player Init Pos: {player_pos}")
    
    px, py = player_pos
    
    # Check tile at player pos
    if 0 <= py < len(grid) and 0 <= px < len(grid[0]):
        print(f"Tile at Player: {grid[py][px]}")
    else:
        print("Player out of bounds!")
        
    # Check neighbors
    neighbors = [
        (px+1, py), (px-1, py), (px, py+1), (px, py-1),
        (px+1, py+1), (px-1, py-1), (px+1, py-1), (px-1, py+1)
    ]
    
    print("\nChecking Neighbors:")
    for nx, ny in neighbors:
        if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]):
            tile = grid[ny][nx]
            print(f"({nx}, {ny}): Tile {tile}")
            # Try move
            res = controller.handle_move(nx, ny)
            print(f"  Move Result: {res}")
        else:
            print(f"({nx}, {ny}): Out of bounds")

if __name__ == "__main__":
    debug_movement()

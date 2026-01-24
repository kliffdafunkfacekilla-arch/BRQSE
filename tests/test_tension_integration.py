import sys
import os
import json

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "c:/Users/krazy/Desktop/BRQSE"))

from brqse_engine.core.game_loop import GameLoopController
from scripts.world_engine import ChaosManager
from brqse_engine.world.map_generator import TILE_ENEMY, TILE_HAZARD, TILE_LOOT

class MockGameState:
    def get_player(self):
        return {"Name": "TestHero", "Species": "Mammal", "Stats": {"Might": 10}, "Level": 1}
    def get_staged_config_path(self):
        return os.path.join(os.getcwd(), "test_battle_staged.json")

def test_tension_integration():
    print("--- Testing Tension Integration in GameLoopController ---")
    
    cm = ChaosManager()
    # Force high tension threshold for testing
    cm.tension_threshold = 12 
    
    gl = GameLoopController(cm, game_state=MockGameState())
    
    # Simulate movement to trigger tension events
    event_counts = {"AMBUSH": 0, "HAZARD": 0, "TREASURE": 0, "SOCIAL": 0, "FLAVOR": 0}
    
    # We'll run a few "moves" and check the results
    for i in range(10):
        # We don't care if the move succeeds, we just want to trigger handle_action
        px, py = gl.player_pos
        res = gl.handle_action("move", px, py) # "Move" in place to roll tension
        print(f"Action Log: {res.get('log')}")
        
        if "tension" in res and res["tension"] == "EVENT":
            print(f"Event Triggered: {res.get('log')}")
            # Try to infer type from log or effect
            if gl.state == "COMBAT":
                event_counts["AMBUSH"] += 1
                print("  Effect: Combat Started!")
                # Reset to explore for next iteration
                gl.state = "EXPLORE"
                gl.player_combatant.hp = gl.player_combatant.max_hp_val # Keep alive
            elif any(TILE_HAZARD in row for row in gl.active_scene.grid):
                event_counts["HAZARD"] += 1
                print("  Effect: Hazard Spawned!")
                # Clean up hazard for next check
                for y, row in enumerate(gl.active_scene.grid):
                    for x, tile in enumerate(row):
                        if tile == TILE_HAZARD: gl.active_scene.grid[y][x] = 1 # Floor
            elif len(gl.interactables) > 0:
                # Check for new interactables near player
                found_new = False
                for pos, obj in gl.interactables.items():
                    if obj.get("type") in ["Ancient Crate", "Lost Satchel", "Shiny Bauble", "Hidden Cache"]:
                        event_counts["TREASURE"] += 1
                        found_new = True
                        print(f"  Effect: Treasure ({obj['type']}) Spawned!")
                        break
                    elif obj.get("type") in ["Abandoned Statue", "Mystic Fountain", "Wandering Merchant", "Prayer Altar"]:
                        event_counts["SOCIAL"] += 1
                        found_new = True
                        print(f"  Effect: Social ({obj['type']}) Spawned!")
                        break
                if found_new:
                    # Clear interactables for next check
                    gl.interactables = {}
                else:
                    event_counts["FLAVOR"] += 1
            else:
                event_counts["FLAVOR"] += 1
    
    print("\nSummary of Tension Results:")
    for k, v in event_counts.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    test_tension_integration()

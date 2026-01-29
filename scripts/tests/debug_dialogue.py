
import sys
import os
from unittest.mock import MagicMock

# MOCK MODULES BEFORE IMPORT
sys.modules["brqse_engine.world.map_generator"] = MagicMock()
sys.modules["brqse_engine.world.map_generator"].MapGenerator = MagicMock()
sys.modules["brqse_engine.combat.mechanics"] = MagicMock()
sys.modules["brqse_engine.combat.mechanics"].CombatEngine = MagicMock()
sys.modules["brqse_engine.world.story_director"] = MagicMock()
sys.modules["brqse_engine.world.narrator"] = MagicMock()
sys.modules["brqse_engine.core.event_engine"] = MagicMock()
sys.modules["brqse_engine.world.campaign_logger"] = MagicMock()
sys.modules["brqse_engine.world.donjon_generator"] = MagicMock()

# Patch constants
sys.modules["brqse_engine.world.map_generator"].TILE_WALL = 0
sys.modules["brqse_engine.world.map_generator"].TILE_FLOOR = 1
sys.modules["brqse_engine.world.map_generator"].TILE_LOOT = 6
sys.modules["brqse_engine.world.map_generator"].TILE_HAZARD = 8
sys.modules["brqse_engine.world.map_generator"].TILE_DOOR = 4
sys.modules["brqse_engine.world.map_generator"].TILE_ENTRANCE = 7
sys.modules["brqse_engine.world.map_generator"].TILE_TREE = 2
sys.modules["brqse_engine.world.map_generator"].TILE_ENEMY = 3

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from brqse_engine.core.game_loop import GameLoopController
from brqse_engine.world.world_system import ChaosManager

def run_debug():
    with open("debug_log.txt", "w") as log_file:
        try:
            print("Initializing Debug Test...", file=log_file)
            mock_sense = MagicMock()
            mock_sense.consult_oracle.return_value = "Debug Response"
            
            loop = GameLoopController(ChaosManager(), sensory_layer=mock_sense)
            
            # Setup Scene
            scene = MagicMock()
            scene.grid = [[1 for _ in range(20)] for _ in range(20)]
            loop.active_scene = scene
            loop.player_pos = (5, 5)
            
            # Add NPC
            npc_data = {
                "type": "Stranger", "name": "Debug NPC",
                "tags": ["npc", "talk"],
                "archetype": "Debug"
            }
            loop.interactables[(6, 5)] = npc_data
            
            print("Running handle_action('talk')...", file=log_file)
            result = loop.handle_action("talk", 6, 5)
            
            print("Result: " + str(result), file=log_file)
            
            if result.get("dialogue", {}).get("text") == "Debug Response":
                print("SUCCESS: Dialogue text matched.", file=log_file)
            else:
                print("FAILURE: Text mismatch.", file=log_file)
                
        except Exception as e:
            print("CRASHED:", file=log_file)
            import traceback
            traceback.print_exc(file=log_file)

if __name__ == "__main__":
    run_debug()

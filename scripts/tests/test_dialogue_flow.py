
import sys
import os
import unittest
from unittest.mock import MagicMock
import sys

# MOCK MODULES BEFORE IMPORT to avoid circular dep hell or missing deps
# We must mock entire sub-packages sometimes
sys.modules["brqse_engine.world.map_generator"] = MagicMock()
sys.modules["brqse_engine.world.map_generator"].MapGenerator = MagicMock()

sys.modules["brqse_engine.combat.mechanics"] = MagicMock()
sys.modules["brqse_engine.combat.mechanics"].CombatEngine = MagicMock()

sys.modules["brqse_engine.world.story_director"] = MagicMock()
sys.modules["brqse_engine.world.narrator"] = MagicMock()
sys.modules["brqse_engine.core.event_engine"] = MagicMock()
sys.modules["brqse_engine.world.campaign_logger"] = MagicMock()
sys.modules["brqse_engine.world.donjon_generator"] = MagicMock()

# Path Setup
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from brqse_engine.core.game_loop import GameLoopController
# Manually patch the constants that GameLoop imports from map_generator
sys.modules["brqse_engine.world.map_generator"].TILE_WALL = 0
sys.modules["brqse_engine.world.map_generator"].TILE_FLOOR = 1
sys.modules["brqse_engine.world.map_generator"].TILE_LOOT = 6
sys.modules["brqse_engine.world.map_generator"].TILE_HAZARD = 8
sys.modules["brqse_engine.world.map_generator"].TILE_DOOR = 4
sys.modules["brqse_engine.world.map_generator"].TILE_ENTRANCE = 7
sys.modules["brqse_engine.world.map_generator"].TILE_TREE = 2
sys.modules["brqse_engine.world.map_generator"].TILE_ENEMY = 3

from brqse_engine.world.world_system import ChaosManager
from brqse_engine.models.entity import Entity

class TestDialogueFlow(unittest.TestCase):
    def setUp(self):
        # Mock Sensory Layer
        self.mock_sense = MagicMock()
        self.mock_sense.consult_oracle.return_value = "Mysterious Response."
        
        self.loop = GameLoopController(ChaosManager(), sensory_layer=self.mock_sense)
        
        # Setup Scene
        scene = MagicMock()
        scene.grid = [[1 for _ in range(20)] for _ in range(20)] # All Floor
        scene.grid[5][5] = 1
        scene.biome = "Dungeon"
        self.loop.active_scene = scene
        self.loop.player_pos = (5, 5)
        
        # Add NPC
        npc_data = {
            "type": "Stranger", "name": "Mysterious Figure",
            "tags": ["npc", "talk"],
            "archetype": "Sage"
        }
        self.loop.interactables[(6, 5)] = npc_data

    def test_talk_action(self):
        try:
            # Act: Talk to NPC
            result = self.loop.handle_action("talk", 6, 5)
            
            # Assert: Check structure
            print("Result:", result)
            self.assertTrue(result["success"])
            self.assertIn("dialogue", result)
            self.assertEqual(result["dialogue"]["speaker"], "Mysterious Figure")
            self.assertEqual(result["dialogue"]["text"], "Mysterious Response.")
            self.assertEqual(result["dialogue"]["archetype"], "Sage")
            
            # Verify Oracle Call
            self.mock_sense.consult_oracle.assert_called_once()
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e
    
    def test_dialogue_reply(self):
        try:
            # Act: Reply
            result = self.loop.handle_action("talk", 6, 5, input="Who are you?")
            self.assertEqual(result["dialogue"]["text"], "Mysterious Response.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e

if __name__ == '__main__':
    unittest.main()

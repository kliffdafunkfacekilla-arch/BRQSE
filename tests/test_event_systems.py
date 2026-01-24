import os
import sys
import unittest
import random
from typing import Dict, Any

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brqse_engine.core.game_loop import GameLoopController
from scripts.world_engine import ChaosManager, SceneStack
from brqse_engine.world.encounter_table import EncounterTable

class TestEventSystems(unittest.TestCase):
    def setUp(self):
        self.chaos = ChaosManager()
        # Mock game state with no player for now (will load default)
        self.engine = GameLoopController(self.chaos)
        
    def test_entry_event(self):
        """Verify that advance_scene triggers an entry encounter."""
        # The constructor already calls advance_scene once.
        # Check if the grid has anything other than TILE_FLOOR and TILE_WALL near entrances
        # Or check the logs
        self.assertIsNotNone(self.engine.active_scene)
        # Force a new scene
        scene = self.engine.advance_scene()
        self.assertIsNotNone(self.engine.active_scene)
        
        # Check if any interactables were spawned (Tension/Entry should spawn them)
        # Entry encounters matching the scene type should exist
        if self.engine.active_scene.encounter_type != "EMPTY":
             self.assertTrue(len(self.engine.interactables) > 0 or "Combat" in self.engine.active_scene.text or self.engine.state == "COMBAT")

    def test_tension_event(self):
        """Verify that move actions trigger tension and physical spawns."""
        self.engine.state = "EXPLORE"
        # Force tension threshold to high to guarantee event (if we hack it)
        self.chaos.tension_threshold = 12 
        
        # Take a move action
        px, py = self.engine.player_pos
        res = self.engine.handle_action("move", px + 1, py)
        
        # Check if tension triggered
        self.assertIn("tension", res)
        # If threshold was 12, d12 roll will always be <= 12, triggering EVENT
        self.assertEqual(res["tension"], "EVENT")
        
        # Verify physical manifestation
        # Check if any new interactables or enemies exist
        # Or at least that the log contains an encounter message
        found_encounter = False
        for node in self.engine.interactables.values():
            if node.get("x") is not None:
                found_encounter = True
                break
        
        if not found_encounter:
             # Check for enemies
             for y in range(20):
                 for x in range(20):
                     if self.engine.active_scene.grid[y][x] in [3, 5, 6]: # Enemy, Hazard, Loot
                         found_encounter = True
                         break
        
        self.assertTrue(found_encounter or self.engine.state == "COMBAT")

    def test_chaos_surge(self):
        """Verify that matching chaos level triggers a surge."""
        self.engine.state = "EXPLORE"
        # Force chaos match
        self.chaos.chaos_level = 5
        # We can't easily force the die roll without mocking random
        # But we can verify the handler works if we call it
        
        result = {"success": True}
        # Simulate a roll of 5
        self.chaos.chaos_clock = 0
        self.engine._spawn_tension_consequence(result, force_type="HAZARD")
        
        # Check if hazard spawned
        found_hazard = False
        for node in self.engine.interactables.values():
            if node.get("tags") and "disarm" in node["tags"]:
                found_hazard = True
                break
        self.assertTrue(found_hazard)

    def test_interaction_handlers(self):
        """Verify specialized handlers (search, disarm, solve)."""
        # 1. Test Search/Loot
        self.engine.interactables[(5, 5)] = {"type": "Crate", "x": 5, "y": 5, "tags": ["search"]}
        self.engine.active_scene.grid[5][5] = 6 # TILE_LOOT
        res = self.engine.handle_action("search", 5, 5)
        self.assertIn("find something useful", res["log"])
        self.assertNotIn((5, 5), self.engine.interactables)
        
        # 2. Test Disarm
        self.engine.interactables[(6, 6)] = {"type": "Trap", "x": 6, "y": 6, "tags": ["disarm"]}
        self.engine.active_scene.grid[6][6] = 5 # TILE_HAZARD
        res = self.engine.handle_action("disarm", 6, 6)
        self.assertIn("carefully disarm", res["log"])
        self.assertNotIn((6, 6), self.engine.interactables)

        # 3. Test Solve
        self.engine.interactables[(7, 7)] = {"type": "Puzzle", "x": 7, "y": 7, "tags": ["solve"]}
        self.engine.active_scene.grid[7][7] = 6 # TILE_LOOT
        res = self.engine.handle_action("solve", 7, 7)
        self.assertIn("concentrate and solve", res["log"])
        self.assertNotIn((7, 7), self.engine.interactables)

if __name__ == "__main__":
    unittest.main()

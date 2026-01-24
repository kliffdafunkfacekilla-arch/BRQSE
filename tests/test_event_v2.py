import os
import sys
import unittest
import random
from typing import Dict, Any

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brqse_engine.core.game_loop import GameLoopController
from scripts.world_engine import ChaosManager, SceneStack

class TestEventV2(unittest.TestCase):
    def setUp(self):
        self.chaos = ChaosManager()
        self.engine = GameLoopController(self.chaos)
        
    def test_progression_gating(self):
        """Verify that advance_scene is blocked when an event is active."""
        # 1. Force a new scene to trigger an event
        self.engine.advance_scene()
        
        # 2. Check that is_event_resolved is False
        # (Very first room might be resolved if we didn't force one, but advance_scene forces one)
        self.assertFalse(self.engine.is_event_resolved)
        
        # 3. Attempt to move to the exit door (17, 10)
        res = self.engine.handle_action("move", 17, 10)
        self.assertFalse(res["success"])
        self.assertIn("barred", res["reason"])

    def test_scenario_generation(self):
        """Verify that 5xD20 rolls produce a valid scenario."""
        self.engine.advance_scene()
        scenario = self.engine.active_scenario
        self.assertIsNotNone(scenario)
        self.assertIn("narrative", scenario)
        self.assertIn("win_condition", scenario)
        self.assertTrue(len(scenario["setup"]) > 0)

    def test_journaling(self):
        """Verify that events are logged to the journal."""
        self.engine.advance_scene()
        summary = self.engine.journal.get_summary()
        self.assertTrue(len(summary) > 0)
        last_entry = summary[-1]
        self.assertEqual(last_entry["outcome"], "Unresolved")

    def test_manual_resolution(self):
        """Verify that solving a puzzle or talking resolves the gating."""
        self.engine.state = "EXPLORE"
        
        # Force a puzzle scenario manually for testing
        self.engine.active_scenario = {
            "archetype": "Puzzle",
            "win_condition": {"type": "PUZZLE_SOLVED"}
        }
        self.engine.is_event_resolved = False
        
        # Ensure (5,5) and (5,6) are floor
        self.engine.active_scene.grid[5][5] = 1
        self.engine.active_scene.grid[6][5] = 1
        
        # Fake a puzzle object
        self.engine.interactables[(5, 5)] = {"type": "Puzzle", "x": 5, "y": 5, "tags": ["solve"], "is_blocking": True}
        
        # Perform solve action
        solve_res = self.engine.handle_action("solve", 5, 5)
        self.assertTrue(solve_res["success"], f"Solve failed: {solve_res.get('reason')}")
        
        # Verify resolution
        self.assertTrue(self.engine.is_event_resolved)
        self.assertEqual(self.engine.journal.entries[-1].outcome, "Solved")
        
        # Verify unblocking
        # Move to (5, 6)
        res = self.engine.handle_action("move", 5, 6)
        self.assertTrue(res["success"], f"Move failed: {res.get('reason')}")

if __name__ == "__main__":
    unittest.main()

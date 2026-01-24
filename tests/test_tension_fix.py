import os
import sys
import unittest
import random
from typing import Dict, Any

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brqse_engine.core.game_loop import GameLoopController
from scripts.world_engine import ChaosManager

class TestTensionFix(unittest.TestCase):
    def setUp(self):
        self.chaos = ChaosManager()
        self.engine = GameLoopController(self.chaos)
        
    def test_tension_event_trigger(self):
        """Verify that a tension EVENT triggers a scenario and journal entry."""
        # 1. Force tension threshold high
        self.chaos.tension_threshold = 12
        
        # 2. Clear journal to be sure
        self.engine.journal.entries = []
        
        # 3. Take a step
        px, py = self.engine.player_pos
        res = self.engine.handle_action("move", px + 1, py)
        
        # 4. Verify tension hit
        self.assertIn("tension", res)
        # With threshold 12, d12 roll is always <= 12 (EVENT)
        # Note: CHAOS_EVENT might trigger too if roll == chaos_level
        
        # 5. Check Journal
        summary = self.engine.journal.get_summary()
        self.assertTrue(len(summary) > 0, "Journal should have an entry for the tension event.")
        
        # 6. Verify Log contains narrative
        self.assertIn("unfolds", res["log"])
        
        # 7. Check if gating is re-applied if significant
        scenario = self.engine.active_scenario
        if scenario["win_condition"]["type"] in ["ENEMIES_KILLED", "PUZZLE_SOLVED"]:
            self.assertFalse(self.engine.is_event_resolved, "Exit should be blocked by significant tension event.")

if __name__ == "__main__":
    unittest.main()

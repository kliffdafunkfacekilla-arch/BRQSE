
import sys
import os
import unittest
import shutil
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from brqse_engine.core.game_loop import GameLoopController
from scripts.world_engine import ChaosManager

class TestCampaignChain(unittest.TestCase):
    def setUp(self):
        self.chaos = ChaosManager()
        mock_sensory = MagicMock()
        mock_sensory.consult_oracle.return_value = "Mock Oracle Response"
        self.game = GameLoopController(self.chaos, sensory_layer=mock_sensory)
        self.game.logger = MagicMock()
        
        # Mock Narrator to avoid AI calls
        self.game.narrator = MagicMock() 
        self.game.narrator.narrate.return_value = "Mock Narration"

    def test_campaign_flow(self):
        import traceback
        try:
            print("\n=== Testing Linked Map System ===")
            
            # 1. Start Campaign
            print("[1] Starting New Campaign...")
            self.game.start_new_campaign(biome="TestZone")
            
            camp_id = self.game.active_campaign_id
            print(f"    - Campaign ID: {camp_id}")
            self.assertIsNotNone(camp_id)
            
            # Check Files
            save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Saves", "Campaigns", camp_id)
            self.assertTrue(os.path.exists(os.path.join(save_dir, "scene_0.json")), "Scene 0 file should exist")
            self.assertTrue(os.path.exists(os.path.join(save_dir, "meta.json")), "Meta file should exist")
            
            # 2. Check Loaded Scene 0
            print(f"[2] Active Scene: {self.game.active_scene.text}")
            self.assertEqual(self.game.current_scene_index, 0)
            
            # Find Exit Logic
            # We need to find the coordinates of the "Way Forward" object
            exit_pos = None
            for (x, y), obj in self.game.interactables.items():
                if obj.get("type") == "zone_transition" and obj.get("target_scene") == 1:
                    exit_pos = (x, y)
                    print(f"    - Found Exit to Scene 1 at {x},{y}")
                    break
                    
            if not exit_pos:
                print("    - WARNING: No Exit to Scene 1 found. Stack might be too short or linker failed.")
                
            if exit_pos:
                # 3. Travel to Exit
                # Clean exit of enemies for test
                enemy = self.game.combat_engine.get_combatant_at(exit_pos[0], exit_pos[1])
                if enemy:
                    print(f"    - Removing blocking enemy {enemy.name} from Exit...")
                    # self.game.combat_engine.remove_combatant(enemy) # Method not found
                    if enemy in self.game.combat_engine.combatants:
                        self.game.combat_engine.combatants.remove(enemy)
                    self.game.combat_engine.tiles[enemy.y][enemy.x].occupant = None

                print(f"[3] Moving to Exit {exit_pos}...")
                # Teleport player near exit to simulate walk
                self.game.player_pos = (exit_pos[0]-1, exit_pos[1])
                res = self.game._process_move(exit_pos[0], exit_pos[1])
                
                # 4. Verify Transition
                print(f"    - Move Result: {res.get('event')}")
                if res.get("event") != "SCENE_ADVANCED":
                    print(f"    - FAILED: Expected SCENE_ADVANCED, got {res}")
                
                self.assertEqual(res.get("event"), "SCENE_ADVANCED")
                self.assertEqual(self.game.current_scene_index, 1)
                print(f"[4] Arrived in Scene 1: {self.game.active_scene.text}")
                
        except Exception:
            with open("debug_crash.txt", "w") as f:
                f.write(traceback.format_exc())
            print("CRASHED. See debug_crash.txt")
            self.fail("Test crashed")

            
    def tearDown(self):
        # Cleanup Campaign Folder
        if self.game.active_campaign_id:
             save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Saves", "Campaigns", self.game.active_campaign_id)
             if os.path.exists(save_dir):
                 shutil.rmtree(save_dir)
                 print("\n[Cleanup] Removed test campaign folder.")

if __name__ == '__main__':
    # unittest.main()
    print("Manual Run Mode")
    t = TestCampaignChain()
    try:
        t.setUp()
        t.test_campaign_flow()
        t.tearDown()
    except Exception:
        import traceback
        with open("debug_crash.txt", "w") as f:
            f.write(traceback.format_exc())
        print("CRASHED IN SETUP/TEARDOWN. See debug_crash.txt")
        traceback.print_exc()
    print("Manual Run Complete")

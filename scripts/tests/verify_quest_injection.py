
import sys
import os
import unittest
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from brqse_engine.world.story_director import StoryDirector
from scripts.world_engine import SceneStack, ChaosManager
from brqse_engine.world.donjon_generator import DonjonGenerator, Cell

class TestQuestInjection(unittest.TestCase):
    def setUp(self):
        self.chaos = ChaosManager()
        self.stack = SceneStack(self.chaos)
        self.director = StoryDirector(sensory_layer=MagicMock())
        self.logger = MagicMock()

    def test_full_pipeline(self):
        print("\n=== Testing Quest Architect Pipeline ===")
        
        # 1. Generate Quest
        self.stack.generate_quest(biome="TestBiome")
        print(f"[1] Quest Generated: {self.stack.quest_title} ({self.stack.total_steps} Steps)")
        
        starting_stack_len = len(self.stack.stack)
        self.assertTrue(starting_stack_len > 0, "Stack should not be empty")

        # 2. Map Generation (Sizing)
        dim = int(15 + (starting_stack_len * 1.5))
        if dim % 2 == 0: dim += 1
        print(f"[2] Calculated Grid Size: {dim}x{dim}")
        
        dg = DonjonGenerator()
        map_data = dg.generate(width=dim, height=dim)
        rooms = map_data["rooms"]
        print(f"[3] Map Generated with {len(rooms)} Rooms")
        
        self.assertTrue(len(rooms) > 0, "Map should have rooms")

        # 3. Distribute Quest
        self.director.distribute_quest(map_data, self.stack, 1, self.logger)
        print("[4] Quest Distributed")
        
        # 4. Verification
        # Check Stack Consumed
        self.assertEqual(len(self.stack.stack), 0, "Stack should be consumed by distribution")
        
        # Check Rooms have Scenes
        scenes_found = 0
        finale_found = False
        entrance_found = False
        
        for r in rooms.values():
            if "scene_data" in r:
                scenes_found += 1
                scene_text = r["scene_data"].get("text", "")
                role = r.get("role", "")
                
                if "Finale" in role:
                    finale_found = True
                    print(f"  - Goal Room {r['id']}: {scene_text}")
                if "Entrance" in role:
                    entrance_found = True
                    print(f"  - Start Room {r['id']}: {scene_text}")
                    
        print(f"[5] Scenes found in map: {scenes_found}")
        
        self.assertTrue(scenes_found > 0, "Rooms should have scenes injected")
        self.assertTrue(finale_found, "Finale should be placed")
        self.assertTrue(entrance_found, "Entrance should be placed")

if __name__ == '__main__':
    unittest.main()

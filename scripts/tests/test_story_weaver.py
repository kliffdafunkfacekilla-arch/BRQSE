
import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from brqse_engine.world.story_weaver import StoryWeaver

class MockSensoryLayer:
    def consult_oracle(self, system_prompt, user_prompt):
        # Determine if this is a JSON request or a Flavor request
        if "flavor" in system_prompt or "Describe" in user_prompt:
             # Batch Response Mock
             return "[\"Mock Desc 1\", \"Mock Desc 2\", \"Mock Desc 3\", \"Mock Desc 4\", \"Mock Desc 5\"]"
             
        # JSON Request (Weaving)
        print(f"[MockSensory] Weaving Prompt...")
        return """
        Here is your plan:
        ```json
        [
            {"map_index": 0, "room_id": "random", "type": "clue", "name": "AI Clue", "desc": "."},
            {"map_index": 0, "room_id": "random", "type": "trap", "name": "AI Filler Trap", "desc": "."},
            {"map_index": 1, "room_id": "last", "type": "trap", "name": "AI Trap", "desc": "."}
        ]
        ```
        """

class TestStoryWeaver(unittest.TestCase):
    def test_mock_weaving(self):
        print("\n=== Testing Story Weaver (AI Prompt + Filler + Enrichment) ===")
        # Inject Mock Layer
        weaver = StoryWeaver(sensory_layer=MockSensoryLayer())
        
        # Mock Maps
        maps = [
            {"id": "map0", "rooms": {1: {"id": 1, "center": (5,5), "x":1, "y":1, "w":5, "h":5}}},
            {"id": "map1", "rooms": {10: {"id": 10, "center": (10,10), "x":5, "y":5, "w":5, "h":5}}},
            {"id": "map2", "rooms": {99: {"id": 99, "center": (15,15), "x":10, "y":10, "w":5, "h":5}}}
        ]
        
        quest_params = {"title": "Test Quest", "desc": "Find the Mockguffin.", "length": 3}
        
        # 1. Weave
        weaver.weave_campaign(maps, quest_params)
        
        # Verify Filler Trap
        objects0 = maps[0].get("objects", [])
        print("DEBUG: Map 0 Objects:", objects0) # Debug
        found_filler = any(o["name"] == "AI Filler Trap" and "trap" in o["tags"] for o in objects0)
        self.assertTrue(found_filler, "Map 0 should have AI Filler Trap with correct tag")
        
        # 2. Enrich
        weaver.enrich_assets(maps, quest_params)
        
        # Verify Flavor Text
        clue = next(o for o in objects0 if o["name"] == "AI Clue")
        print("DEBUG: Clue Description:", clue["description"]) # Debug
        # Assert one of the batch strings
        self.assertTrue("Mock Desc" in clue["description"], "Should receive batch mock description")
        
        print("Weaving Successful - Filler Placed & Descriptions Enriched.")

if __name__ == '__main__':
    unittest.main()

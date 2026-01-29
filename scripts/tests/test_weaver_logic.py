
import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from brqse_engine.world.story_weaver import StoryWeaver
from brqse_engine.core.sensory_layer import SensoryLayer

def test_weaver():
    print("[TEST] Initializing StoryWeaver...")
    # Mock sensory layer or real? Let's try to mock the response to see if logic holds, 
    # then maybe try real if we can. 
    # For now, let's see if the Weaver handles a Mock response correctly.
    
    class MockSensory:
        def consult_oracle(self, sys, prompt):
            print(f"[MOCK LLM] Prompt received: {prompt[:50]}...")
            return """
            ```json
            [
              {"map_index": 0, "room_id": "random", "type": "clue", "name": "Test Clue", "desc": "A test clue."},
              {"map_index": 0, "room_id": "random", "type": "trap", "name": "Spike Pit", "desc": "Sharp spikes."}
            ]
            ```
            """

    weaver = StoryWeaver(sensory_layer=MockSensory())
    
    # Create dummy map
    dummy_map = {
        "biome": "Dungeon",
        "rooms": {"1": {"id": 1, "x":1, "y":1, "w":5, "h":5, "center": (3,3)}},
        "objects": [{"x": 1, "y": 1, "type": "barrel", "name": "Barrel"}]
    }
    
    print("[TEST] Running Weave...")
    weaver.weave_campaign([dummy_map], {"title": "Test Quest", "length": 1})
    
    print("[TEST] Checking Map Assets...")
    objs = dummy_map.get("objects", [])
    found_clue = False
    for o in objs:
        print(f" - {o['name']} ({o['type']})")
        if o['name'] == "Test Clue": found_clue = True
        
    if found_clue:
        print("[SUCCESS] Weaver successfully injected LLM assets.")
    else:
        print("[FAIL] Weaver failed to inject assets.")

if __name__ == "__main__":
    test_weaver()

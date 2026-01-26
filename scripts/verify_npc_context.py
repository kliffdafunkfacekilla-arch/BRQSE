
import sys
import os
import random
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brqse_engine.core.game_loop import GameLoopController
from brqse_engine.core.event_engine import EventEngine

def test_npc_context():
    print("Testing NPC Context Injection...")
    
    # 1. Setup Mock Sensory Layer
    mock_sensory = MagicMock()
    # Mock QUEST generation
    # Use side_effect with a function to handle infinite calls if needed, or just extend the list
    mock_sensory.generate_narrative.side_effect = [
        # Call 1: Quest Gen
        {"narrative": '{"narrative": "A dark figure looms.", "goal_description": "Find the Lost Amulet", "setup": [{"type": "NPC_SPAWN", "subtype": "Guide"}], "win_condition": {"type": "TALKED_TO_NPC"}}'},
        # Call 2: Social Interaction
        {"narrative": '{"narrative": "I heard you are looking for the Amulet..."}'},
        # Call 3+: Fallback
        {"narrative": '{"narrative": "..."}'},
        {"narrative": '{"narrative": "..."}'}
    ]

    # 2. Setup Logic
    mock_chaos = MagicMock()
    mock_chaos.chaos_clock = 0
    mock_chaos.chaos_level = 1
    mock_chaos.get_atmosphere.return_value = {"descriptor": "calm"}
    
    gl = GameLoopController(mock_chaos, sensory_layer=mock_sensory)
    
    # 3. Trigger Event (Simulate Room Entry)
    print("\n[Step 1] Triggering Event...")
    gl.trigger_event(is_entry=True)
    
    # 4. Find NPC
    npc_loc = None
    for loc, obj in gl.interactables.items():
        if obj["type"] == "Guide":
            npc_loc = loc
            print(f"DEBUG: Found NPC at {loc}")
            print(f"DEBUG: NPC Context stored: {obj.get('dialogue_context')}")
            if obj.get('dialogue_context') == "Find the Lost Amulet":
                print("SUCCESS: Context injected into Entity.")
            else:
                print("FAILURE: Context missing or incorrect on Entity.")
            break
            
    if not npc_loc:
        print("FAILURE: NPC did not spawn.")
        return

    # 5. Talk to NPC
    print("\n[Step 2] Talking to NPC...")
    gl.handle_action("talk", npc_loc[0], npc_loc[1])
    
    # 6. Verify Sensory Call
    print("\n[Step 3] Verifying Sensory Call...")
    calls = mock_sensory.generate_narrative.call_args_list
    last_call = calls[-1]
    kwargs = last_call.kwargs
    
    print(f"Call Kwargs: {kwargs}")
    if kwargs.get("quest_context") == "Find the Lost Amulet":
        print("SUCCESS: quest_context passed to SensoryLayer.")
    else:
         print(f"FAILURE: quest_context not passed correctly. Got: {kwargs.get('quest_context')}")

if __name__ == "__main__":
    test_npc_context()

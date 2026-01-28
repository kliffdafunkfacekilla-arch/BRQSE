
import sys
import os
import json
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brqse_engine.core.event_engine import EventEngine
from brqse_engine.core.game_loop import GameLoopController

def test_ai_event_goal():
    print("Testing AI Event Goal Integration...")
    
    # Mock SensoryLayer
    mock_sensory = MagicMock()
    # Mock the response structure from SensoryLayer
    mock_sensory.generate_narrative.return_value = {
        "narrative": json.dumps({
            "narrative": "A dark figure approaches.",
            "goal_description": "TALK to the figure to learn the truth.",
            "setup": [{"type": "NPC_SPAWN", "subtype": "Figure", "tags": ["talk"]}],
            "win_condition": {"type": "TALKED_TO_NPC"}
        })
    }

    # Initialize EventEngine
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Data")
    engine = EventEngine(data_dir)
    
    # Generate Scenario
    scenario = engine.generate_scenario("DUNGEON", sensory_layer=mock_sensory)
    
    # Verify parsing
    print(f"Scenario Keys: {scenario.keys()}")
    if "goal_description" in scenario:
        print(f"SUCCESS: goal_description found: '{scenario['goal_description']}'")
    else:
        print("FAILURE: goal_description missing from scenario.")
        return

    # Verify GameLoop Integration (Mocking parts for speed)
    print("\nTesting GameLoop Trigger...")
    mock_chaos = MagicMock()
    mock_chaos.chaos_clock = 0
    mock_chaos.chaos_level = 1
    mock_chaos.get_atmosphere.return_value = {"descriptor": "eerie"}
    # Mock scene for game loop
    mock_scene = MagicMock()
    mock_scene.biome = "DUNGEON"
    mock_scene.grid = [[0]*20 for _ in range(20)]
    mock_scene.interactables = []
    
    gl = GameLoopController(mock_chaos, sensory_layer=mock_sensory, game_state=None)
    # Inject mocked scene
    gl.active_scene = mock_scene
    gl.event_engine = engine # Use our engine with the mocked sensory layer
    
    # Trigger Event
    res = gl.trigger_event(is_entry=True)
    
    # Check Result Log
    print(f"GameLoop Result Log: {res['log']}")
    if "GOAL: TALK to the figure" in res['log']:
        print("SUCCESS: Goal displayed in GameLoop log.")
    else:
        print("FAILURE: Goal not found in GameLoop log.")

if __name__ == "__main__":
    test_ai_event_goal()


import sys
import os
import random
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brqse_engine.core.game_loop import GameLoopController
from brqse_engine.core.event_engine import EventEngine

def test_key_mechanism():
    print("Testing Key/Lock Mechanic...")
    
    # 1. Setup Mock
    mock_chaos = MagicMock()
    mock_chaos.chaos_level = 1
    mock_chaos.chaos_clock = 0
    mock_chaos.roll_tension.return_value = "SAFE"
    
    gl = GameLoopController(mock_chaos, sensory_layer=MagicMock())
    gl.active_scene = MagicMock()
    gl.active_scene.grid = [[0 for _ in range(20)] for _ in range(20)] # Mock grid
    gl.player_pos = (5, 5)
    
    # Mock Player
    gl.player_combatant = MagicMock()
    gl.player_combatant.character.skills = []
    gl.player_combatant.character.powers = []
    gl.player_combatant.facing = "N"
    
    # 2. Plant Key and Lock manually
    key_id = "test_key_123"
    
    # Object with Key
    gl.interactables[(6, 5)] = {
        "type": "Chest", "x": 6, "y": 5,
        "tags": ["search"],
        "has_key": key_id,
        "key_name": "Test Key"
    }
    
    # Locked Door
    gl.interactables[(7, 5)] = {
        "type": "Door", "x": 7, "y": 5,
        "tags": ["unlock"],
        "is_locked": True,
        "required_key": key_id,
        "is_blocking": True
    }
    
    # 3. Test: Try to unlock WITHOUT key
    print("\n[Step 1] Initial Unlock Attempt (Should Fail)...")
    res = gl.handle_action("unlock", 7, 5)
    print(f"Result: {res.get('log')}")
    if "key" in res.get("log", "").lower():
        print("SUCCESS: Unlock failed as expected.")
    else:
        print("FAILURE: Unlock succeeded or gave wrong message.")
        
    # 4. Test: Search for Key
    print("\n[Step 2] Searching for Key...")
    res = gl.handle_action("search", 6, 5)
    print(f"Result: {res.get('log')}")
    
    # Verify Inventory
    print(f"Inventory: {gl.inventory}")
    has_key = any(k["id"] == key_id for k in gl.inventory)
    if has_key:
        print("SUCCESS: Key added to inventory.")
    else:
        print("FAILURE: Key NOT found.")
        return

    # 5. Test: Try to unlock WITH key
    print("\n[Step 3] Unlock Attempt with Key...")
    res = gl.handle_action("unlock", 7, 5)
    print(f"Result: {res.get('log')}")
    
    obj = gl.interactables.get((7, 5))
    if not obj["is_locked"]:
        print("SUCCESS: Door unlocked!")
    else:
        print("FAILURE: Door still locked.")

if __name__ == "__main__":
    test_key_mechanism()

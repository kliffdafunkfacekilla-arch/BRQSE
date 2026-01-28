
import sys
import os
import json as json_lib
from unittest.mock import MagicMock

# Add project root to path
# scripts/tests/test_arbiter.py -> scripts/tests -> scripts -> BRQSE
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from brqse_engine.core.arbiter import Arbiter
from brqse_engine.core.oracle import DungeonOracle
from brqse_engine.core.context_manager import ContextManager

# Mock SensoryLayer for Oracle
class MockSensoryLayer:
    def consult_oracle(self, system_prompt, user_input):
        print(f"[Sensory Mock] Received System Prompt Snippet: {system_prompt[-200:]}")
        return "You leap across the chasm, landing gracefully."

# Mock Arbiter's API call
def mock_api_post(url, json=None, timeout=None):
    prompt_sent = json.get("prompt", "")
    print(f"[Arbiter Mock] Received Prompt: {prompt_sent[:100]}...")
    
    # Mock Response Object
    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self.json_data = json_data
            self.status_code = status_code
        def json(self):
            return self.json_data

    # Simulate Logic: If "jump" in input, trigger check
    if "jump" in prompt_sent.lower():
        # The Arbiter implementation expects 'response' field containing the text from LLM
        response_json = {
            "check_needed": True,
            "skill": "Athletics",
            "dc": 15,
            "reason": "Jumping a wide chasm"
        }
        # We wrap the JSON in text for the 'response' field, as LLM outputs text
        return MockResponse({"response": json_lib.dumps(response_json)})
    else:
        return MockResponse({"response": '{"check_needed": false}'})

def test_arbiter_system():
    print("--- Testing Arbiter System ---")
    
    # 1. Setup
    sensory = MockSensoryLayer()
    oracle = DungeonOracle(sensory)
    
    # Monkeypatch requests.post in Arbiter to avoid real API calls
    import requests
    requests.post = mock_api_post
    
    # Mock Context Manager
    oracle.ctx_manager = MagicMock()
    oracle.ctx_manager.build_full_context.return_value = "[Context: You are on a ledge.]"
    
    # Mock Game Loop & Player
    oracle.loop = MagicMock()
    oracle.loop.player_combatant = MagicMock()
    # Mock get_stat_modifier for MIGHT to return +4
    def get_mod(name):
        return 4 if name == "Might" else 0
    oracle.loop.player_combatant.get_stat_modifier = get_mod
    
    # 2. Test Safe Action
    print("\n[Test 1] Safe Action: 'I look around'")
    response = oracle.chat("I look around")
    print(f"Response: {response}")
    if "[SYSTEM EVENT]" not in response:
        print("PASS: No check triggered for safe action.")
    else:
        print("FAIL: Check triggered unexpectedly.")

    # 3. Test Risky Action
    print("\n[Test 2] Risky Action: 'I jump across the chasm'")
    response = oracle.chat("I jump across the chasm")
    print(f"Response: {response}")
    
    if "[SYSTEM EVENT]" in response and "Athletics" in response:
        print("PASS: Skill Check triggered and logged.")
        if "MIGHT +4" in response:
            print("PASS: Stat Bonus (+4) correctly applied.")
        else:
            print("FAIL: Stat Bonus missing from log.")
    else:
        print("FAIL: Skill Check missing.")

if __name__ == "__main__":
    test_arbiter_system()


import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brqse_engine.world.narrator import Narrator
from brqse_engine.core.sensory_layer import SensoryLayer
from brqse_engine.world.campaign_logger import CampaignLogger

class MockLogger:
    def log(self, level, category, text, tags=None):
        print(f"[LOG] {category}: {text}")

def test_narrator():
    print("Initializing Narrator Test...")
    sensory = SensoryLayer(model="qwen2.5:latest")
    logger = MockLogger()
    narrator = Narrator(sensory, logger)
    
    # 1. Test Combat Flavor
    print("\n--- Testing Combat Narration ---")
    combat_result = {
        "success": True, 
        "event": "COMBAT_STARTED", 
        "log": "Combat Started! The Skeletal Warrior engages."
    }
    flavor = narrator.narrate(combat_result, state_context="Ancient Crypt")
    print(f"Original: {combat_result['log']}")
    print(f"Flavored: {flavor}")
    
    if flavor and flavor != combat_result['log']:
        print("SUCCESS: Combat narrated.")
    else:
        print("FAIL: Combat not flavored (or AI failed).")

    # 2. Test Discovery Flavor
    print("\n--- Testing Discovery Narration ---")
    discovery_result = {
        "success": True,
        "event": "DISCOVERY",
        "log": "You found a Rusty Key."
    }
    flavor = narrator.narrate(discovery_result, state_context="Damp Cellar")
    print(f"Original: {discovery_result['log']}")
    print(f"Flavored: {flavor}")

    # 3. Test Boring Action (Should skip)
    print("\n--- Testing Boring Action ---")
    move_result = {
        "success": True,
        "event": "ACTION",
        "log": "Moved to 3, 4."
    }
    flavor = narrator.narrate(move_result)
    if flavor == move_result["log"]:
        print("SUCCESS: Boring action skipped.")
    else:
        print(f"FAIL: Boring action was narrated: {flavor}")

if __name__ == "__main__":
    test_narrator()

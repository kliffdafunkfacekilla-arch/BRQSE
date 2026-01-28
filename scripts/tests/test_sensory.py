
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brqse_engine.core.sensory_layer import SensoryLayer
from scripts.world_engine import ChaosManager

def test_sensory_integration():
    print("=== TESTING AI SENSORY LAYER INTEGRATION ===\n", flush=True)
    
    # 1. Initialize Components
    chaos = ChaosManager()
    chaos.chaos_clock = 7 # High Chaos
    sensory = SensoryLayer()
    
    print(f"Chaos Level: {chaos.chaos_level}")
    print(f"Chaos Clock: {chaos.chaos_clock} (High Tension)")
    
    # 2. Test Scene Description (Module A)
    print("\n--- TEST: SCENE GENERATION (Module A) ---")
    
    scene_context = {
        "biome": "Sump",
        "chaos_level": chaos.chaos_level,
        "chaos_clock": chaos.chaos_clock,
        "atmosphere": "Fog, Smell of Sulfur",
        "features": ["Rotting Bridge", "Acid Pods"],
        "smell": "Rotten Eggs"
    }
    
    response = sensory.generate_narrative(scene_context, "SCENE")
    payload = response["payload"]
    
    print("Input Context:", json.dumps(scene_context, indent=2))
    print("Generated Prompt Payload:", json.dumps(payload, indent=2))
    
    assert payload["chaos_clock"] == 7
    assert payload["event"]["type"] == "SCENE_ENTER"
    assert "Rotting Bridge" in payload["event"]["features"]
    
    # 3. Test Combat Narrator (Module B)
    print("\n--- TEST: COMBAT NARRATION (Module B) ---")
    
    # Mock data from mechanics.py replay_log
    combat_data = {
        "actor_name": "Valerius",
        "target_name": "Black Knight",
        "action": "Attack",
        "weapon": "Maul",
        "armor": "Plate Armor",
        "result": "miss",
        "margin": -2,
        "damage": 0,
        "style": "Glancing"
    }
    
    response = sensory.generate_narrative(scene_context, "COMBAT", combat_data)
    payload = response["payload"]
    
    print("Combat Data:", json.dumps(combat_data, indent=2))
    print("Generated Prompt Payload:", json.dumps(payload, indent=2))
    
    assert payload["event"]["type"] == "COMBAT_ACTION"
    assert payload["event"]["margin"] == -2
    assert payload["event"]["weapon"] == "Maul"
    
    # 4. Test Clash (Module B - Special)
    print("\n--- TEST: CLASH (Module B - Clash) ---")
    clash_data = {
        "actor_name": "Valerius",
        "target_name": "Black Knight",
        "action": "Clash",
        "weapon": "Maul",
        "armor": "Plate Armor",
        "result": "clash",
        "margin": 0,
        "damage": 0
    }
    response = sensory.generate_narrative(scene_context, "COMBAT", clash_data)
    print("Clash Payload:", json.dumps(response["payload"]["event"], indent=2))
    
    # 5. Test Social DM (Module C)
    print("\n--- TEST: SOCIAL ENCOUNTER (Module C) ---")
    social_data = {
        "actor_name": "Bard",
        "target_name": "Guard",
        "method": "Intimidation",
        "defense": "Stoicism",
        "result": "Success"
    }
    response = sensory.generate_narrative(scene_context, "SOCIAL", social_data)
    print("Social Payload:", json.dumps(response["payload"]["event"], indent=2))

    print("\n=== INTEGRATION VERIFIED ===")

if __name__ == "__main__":
    test_sensory_integration()

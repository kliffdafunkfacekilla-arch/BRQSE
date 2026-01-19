import sys
import os
import random

# Ensure project root is in path
sys.path.append(os.getcwd())

# Mock Mechanics (simplified) to avoid importing everything
from brqse_engine.combat.mechanics import CombatEngine, Combatant

def test_ai():
    print("Testing AI Logic...")
    engine = CombatEngine()
    
    # Mock Flower
    flower = Combatant(data={
        "Name": "Flower",
        "Species": "Plant",
        "AI": "Ranged", 
        "Stats": {"Vitality": 18, "Knowledge": 10},
        "Powers": ["Solar Beam", "Entangle", "Spore Cloud"],
        "FP": 30,
        "SP": 30
    })
    # Mock positions
    flower.x, flower.y = 0, 0
    
    # Mock Buggy
    buggy = Combatant(data={"Name": "Buggy", "Stats": {"Might": 18}})
    buggy.x, buggy.y = 3, 0 # Distance 3 (Ideal range)
    
    engine.add_combatant(flower, 0, 0)
    engine.add_combatant(buggy, 3, 0)
    
    print("\n--- Running 20 Turns (Target NOT Controlled) ---")
    solar_count = 0
    entangle_count = 0
    
    for i in range(20):
        # Reset cooldowns/resources if needed (not needed here)
        log = engine.execute_ai_turn(flower)
        
        # Check Log
        found = False
        for line in log:
            if "Solar Beam" in line:
                solar_count += 1
                found = True
            elif "Entangle" in line:
                entangle_count += 1
                found = True
        
        if not found:
            print(f"Turn {i}: No Spell Cast? Log: {log}")

    print(f"\nResults:")
    print(f"Entangle (Control): {entangle_count}")
    print(f"Solar Beam (Damage): {solar_count}")
    
    if solar_count > 0:
        print("\nSUCCESS: Solar Beam is selectable!")
    else:
        print("\nFAILURE: Solar Beam was never selected.")

if __name__ == "__main__":
    test_ai()

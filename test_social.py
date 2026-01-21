import sys
import os
import random

# Ensure we can import from local
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brqse_engine.models.character import Character
from brqse_engine.combat.combatant import Combatant
from brqse_engine.combat.combat_engine import CombatEngine

def main():
    print("=== TEST: Social Combat (Call Out) ===")
    random.seed(42) # Deterministic
    
    # 1. Setup Hero (High Awareness)
    hero_data = {
        "Name": "Detector", 
        "Stats": {"Awareness": 16, "Logic": 12}, 
        "Current_HP": 20
    }
    hero = Character(hero_data)
    c_hero = Combatant(hero, team="Blue")
    
    # 2. Setup Rival (Low Guile)
    rival_data = {
        "Name": "Liar", 
        "Stats": {"Guile": 8, "Intuition": 10}, 
        "Current_HP": 20
    }
    rival = Character(rival_data)
    c_rival = Combatant(rival, team="Red")
    
    engine = CombatEngine()
    engine.add_combatant(c_hero)
    engine.add_combatant(c_rival)
    
    print(f"Hero Awareness Mod: {c_hero.get_stat_mod('Awareness')}")
    print(f"Rival Guile Mod: {c_rival.get_stat_mod('Guile')}")
    print(f"Rival Max Composure: {c_rival.max_composure}")
    
    # 3. Execute Call Out (Awareness vs Guile)
    print("\n--- Executing Call Out ---")
    start_comp = c_rival.current_composure
    success = engine.execute_social_maneuver(c_hero, c_rival, "Call Out")
    
    if success:
        print("PASS: Maneuver Succeeded.")
        if c_rival.current_composure < start_comp:
             dmg = start_comp - c_rival.current_composure
             print(f"PASS: Target took {dmg} Composure damage. Current: {c_rival.current_composure}")
        else:
             print("FAIL: No Composure damage taken?")
    else:
        print("FAIL: Maneuver Failed (or lost roll).")
        
    # Check simple status effect logic
    # Gaslight Effect: "Target becomes Confused"
    # Currently engine logs text but doesn't apply Status object yet unless mapped.
    # We rely on log inspection for now.

if __name__ == "__main__":
    main()

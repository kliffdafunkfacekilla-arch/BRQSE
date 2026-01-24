import sys
import os
sys.path.append(os.getcwd())
from brqse_engine.combat.combat_engine import CombatEngine
from brqse_engine.combat.combatant import Combatant
from brqse_engine.models.character import Character
import random

def test_tactics():
    print("=== TESTING TACTICAL RULES ===")
    engine = CombatEngine()
    
    # Setup Combatants
    char_hero = Character({"Name": "Hero", "Stats": {"Might": 18, "Reflexes": 14}}) # Mod +4, AC 12
    hero = Combatant(char_hero, x=0, y=0, team=1)
    
    char_ally = Character({"Name": "Ally", "Stats": {"Might": 14, "Reflexes": 10}}) 
    ally = Combatant(char_ally, x=1, y=0, team=1) # Adjacent to Hero, will move
    
    char_villain = Character({"Name": "Villain", "Stats": {"Might": 16, "Reflexes": 10}}) # AC 10
    villain = Combatant(char_villain, x=5, y=5, team=2)
    
    engine.add_combatant(hero)
    engine.add_combatant(ally)
    engine.add_combatant(villain)

    # 1. TEST FLANKING (2v1)
    print("\n--- TEST 1: FLANKING (2 Attacks) ---")
    # Move Hero and Ally to be adjacent to Villain (5,5)
    hero.x, hero.y = 4, 5 # Left of Villain
    ally.x, ally.y = 6, 5 # Right of Villain
    # Villain is at 5,5. 
    # Check adjacent:
    ops = engine.get_adjacent_opponents(villain)
    print(f"Villain has {len(ops)} adjacent enemies (Expected 2).")
    
    # Hero attacks Villain
    print("Hero attacking Villain (Should be Flanking):")
    res = engine.execute_attack(hero, villain)
    print(f"Log: {res['log']}")
    print(f"Roll: {res['roll']}, Total: {res['total']} (Base Mod +4 + Flank?)")

    # 2. TEST MOBBING (3v1)
    print("\n--- TEST 2: MOBBING (3 Attacks) ---")
    char_ally2 = Character({"Name": "Ally2", "Stats": {"Might": 10}})
    ally2 = Combatant(char_ally2, x=5, y=4, team=1) # Top of Villain
    engine.add_combatant(ally2)
    
    ops = engine.get_adjacent_opponents(villain)
    print(f"Villain has {len(ops)} adjacent enemies (Expected 3).")
    
    print("Hero attacking Villain (Should be Mobbing - Advantage):")
    # We can't easily see advantage rolls in result dict, but log should say it
    res = engine.execute_attack(hero, villain)
    print(f"Log: {res['log']}")
    
    # 3. TEST RANGED & FRIENDLY FIRE
    print("\n--- TEST 3: FRIENDLY FIRE ---")
    # Reset positions
    hero.x, hero.y = 0, 5 # 5 ft away (Ranged)
    # Ally is at 6,5 (Next to Villain at 5,5)
    # Villain at 5,5
    # Ally2 removed or moved away
    ally2.x, ally2.y = 0, 0 
    
    print(f"Hero at {hero.x},{hero.y}. Villain at {villain.x},{villain.y}. Ally at {ally.x},{ally.y}")
    
    # Hero attacks Villain with Ranged
    # We need a MISS to trigger Friendly Fire. 
    # Villain AC is 10. Hero Mod +4. Needs roll < 6 to miss.
    
    found_ff = False
    for i in range(20):
        print(f"Shot {i+1}:")
        res = engine.execute_attack(hero, villain, is_ranged=True)
        if "FRIENDLY FIRE" in res['log']:
            print(f"!!! SUCCESS: {res['log']}")
            found_ff = True
            break
        else:
            print(f"Result: {res['log']}")
            
    if not found_ff:
        print("Warning: No Friendly Fire triggered in 20 shots (might be luck or high hit rate).")

if __name__ == "__main__":
    test_tactics()

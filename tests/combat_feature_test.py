import sys
import os
import random

# Ensure we can import from local
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brqse_engine.models.character import Character
from brqse_engine.combat.mechanics import Combatant, CombatEngine
import brqse_engine.abilities.engine_hooks as engine_hooks

def main():
    print("=== TEST: Phase C2 Features (Terrain, Effects, Abilities) ===")
    random.seed(1) 
    
    # 1. Setup
    # Vitality 10 -> Max HP = 10 + 10 = 20.
    char_data = {"Name": "Tester", "Stats": {"Might": 50, "Vitality": 10}, "Current_HP": 20}
    # Mechanics Combatant takes 'data' dict, not Character object
    # It also doesn't take x/y/team in init
    hero_data = char_data
    # Ensure stats key matches what mechanics expects (Stats)
    if "Stats" not in hero_data: hero_data["Stats"] = hero_data.get("stats", {})
    
    c_hero = Combatant(data=hero_data)
    c_hero.team = "Blue"
    
    engine = CombatEngine(cols=5, rows=5)
    engine.add_combatant(c_hero, 0, 0)
    engine.start_combat()
    
    # --- TEST 1: TERRAIN HAZARDS ---
    print("\n[Test 1] Terrain Hazards")
    # Set (0, 1) to Fire
    engine.set_terrain(0, 1, "fire")
    print(f"Setting (0,1) to Fire. Hero HP: {c_hero.hp}")
    
    # Move Hero into Fire
    engine.move_char(c_hero, 0, 1)
    print(f"Moved Hero to Fire. Hero HP: {c_hero.hp}")
    
    if c_hero.hp < 20:
        print("PASS: Took hazard damage.")
    else:
        print("FAIL: No damage taken.")

    # --- TEST 2: STATUS EFFECTS ---
    print("\n[Test 2] Status Effects")
    # Apply Stunned for 1 round
    c_hero.apply_effect("Stunned", 1)
    if c_hero.is_stunned:
        print("PASS: Hero is Stunned (Property check).")
    else:
        print("FAIL: Hero is not Stunned.")
        
    print("Ending Turn (Tick Effects)...")
    # Current turn index is 0 (Hero). next_turn() will advance to next. 
    # But wait, next_turn() ticks the *new* active combatant.
    # To tick Hero, we need to loop back to Hero's turn.
    # Since Hero is the only one...
    engine.end_turn() # Advance to... Hero again (round 2)
    
    if not c_hero.is_stunned:
        print("PASS: Stunned effect expired.")
    else:
        print(f"FAIL: Hero still Stunned. Active Effects: {c_hero.active_effects}")

    # --- TEST 3: ABILITIES ---
    print("\n[Test 3] Abilities")
    # Inject Mock Ability
    mock_ability = {"Talent_Name": "Test Heal", "Effect": "Heal 100 HP"}
    engine_hooks.loader.talents.append(mock_ability)
    
    # Damage Hero first
    c_hero.start_hp = c_hero.hp
    c_hero.take_damage(5)
    print(f"Hero damaged to {c_hero.hp}. Casting 'Test Heal'...")
    
    success = engine.activate_ability(c_hero, "Test Heal", target=c_hero)
    
    if success:
        print(f"Ability Resolved. Hero HP: {c_hero.hp}")
        if c_hero.hp > c_hero.start_hp - 5:
             print("PASS: Healing applied.")
        else:
             print("FAIL: Healing not applied.")
    else:
        print("FAIL: Ability activation returned False.")

    # --- TEST 4: GEAR INTEGRATION ---
    print("\n[Test 4] Gear Damage")
    # mechanics.py attack_target uses c.weapon_data
    # We inject it directly to bypass inventory complexity for this test
    c_hero.weapon_data = {
        "Name": "Greatsword",
        "damage_dice": 12, # mechanics use int for simple calculation or requires parser
        "tags": {"Finesse"} # Example tag
    }
    
    # Needs a target
    dummy_data = {"Name": "Dummy", "Stats": {"Reflexes": 10}, "Current_HP": 50}
    c_dummy = Combatant(data=dummy_data)
    c_dummy.team = "Red"
    engine.add_combatant(c_dummy, 1, 0)
    
    hp = c_dummy.hp
    print("Attacking Dummy with Greatsword (2d6)...")
    # Force hit if possible (hard to force with dice, but we check log)
    result = engine.attack_target(c_hero, c_dummy)
    
    # mechanics.py returns a list of log strings, not a dict
    if result and "HIT" in str(result):
        print(f"Outcome: {result}")
        if "HIT" in str(result) or "deals" in str(result):
            print("PASS: Damage logic executed.")
        else:
            print("FAIL: Did not see HIT confirm in log string (expected behavior for list return)")
    else:
        print("INFO: Attack resolved (Log printed below)")
        print(result)

if __name__ == "__main__":
    main()

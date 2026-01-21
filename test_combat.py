import sys
import os
import random

# Ensure we can import from local
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brqse_engine.models.character import Character
from brqse_engine.combat.combatant import Combatant
from brqse_engine.combat.combat_engine import CombatEngine
import brqse_engine.abilities.engine_hooks as engine_hooks

def main():
    print("=== TEST: Phase C2 Features (Terrain, Effects, Abilities) ===")
    random.seed(1) 
    
    # 1. Setup
    # Vitality 10 -> Max HP = 10 + 10 = 20.
    char_data = {"Name": "Tester", "Stats": {"Might": 50, "Vitality": 10}, "Current_HP": 20}
    hero = Character(char_data)
    c_hero = Combatant(hero, x=0, y=0, team="Blue")
    
    engine = CombatEngine(cols=5, rows=5)
    engine.add_combatant(c_hero)
    engine.start_combat()
    
    # --- TEST 1: TERRAIN HAZARDS ---
    print("\n[Test 1] Terrain Hazards")
    # Set (0, 1) to Fire
    engine.set_terrain(0, 1, "fire")
    print(f"Setting (0,1) to Fire. Hero HP: {c_hero.current_hp}")
    
    # Move Hero into Fire
    engine.move_entity(c_hero, 0, 1)
    print(f"Moved Hero to Fire. Hero HP: {c_hero.current_hp}")
    
    if c_hero.current_hp < 20:
        print("PASS: Took hazard damage.")
    else:
        print("FAIL: No damage taken.")

    # --- TEST 2: STATUS EFFECTS ---
    print("\n[Test 2] Status Effects")
    # Apply Stunned for 1 round
    c_hero.add_timed_effect("Stunned", 1)
    if c_hero.is_stunned:
        print("PASS: Hero is Stunned (Property check).")
    else:
        print("FAIL: Hero is not Stunned.")
        
    print("Ending Turn (Tick Effects)...")
    # Current turn index is 0 (Hero). next_turn() will advance to next. 
    # But wait, next_turn() ticks the *new* active combatant.
    # To tick Hero, we need to loop back to Hero's turn.
    # Since Hero is the only one...
    engine.next_turn() # Advance to... Hero again (round 2)
    
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
    c_hero.start_hp = c_hero.current_hp
    c_hero.take_damage(5)
    print(f"Hero damaged to {c_hero.current_hp}. Casting 'Test Heal'...")
    
    success = engine.activate_ability(c_hero, "Test Heal", target=c_hero)
    
    if success:
        print(f"Ability Resolved. Hero HP: {c_hero.current_hp}")
        if c_hero.current_hp > c_hero.start_hp - 5:
             print("PASS: Healing applied.")
        else:
             print("FAIL: Healing not applied.")
    else:
        print("FAIL: Ability activation returned False.")

    # --- TEST 4: GEAR INTEGRATION ---
    print("\n[Test 4] Gear Damage")
    # Equip Hero with Greatsword (2d6)
    greatsword = {
        "Name": "Greatsword",
        "Type": "Weapon",
        "Damage": "2d6",
        "AC_Bonus": 0,
        "Equipped": True
    }
    c_hero.character.inventory.append(type('Item', (object,), {"data": greatsword, "is_equipped": True, "type": "Weapon"})()) # Mock Item
    
    # Needs a target
    dummy_data = {"Name": "Dummy", "Stats": {"Reflexes": 10}, "Current_HP": 50}
    c_dummy = Combatant(Character(dummy_data), x=1, y=0, team="Red")
    engine.add_combatant(c_dummy)
    
    current_hp = c_dummy.current_hp
    print("Attacking Dummy with Greatsword (2d6)...")
    # Force hit if possible (hard to force with dice, but we check log)
    result = engine.execute_attack(c_hero, c_dummy, "Might")
    
    if result["hit"]:
        dmg = result["damage"]
        print(f"Hit! Damage dealt: {dmg}")
        print(f"Log: {result['log']}")
        if "2d6" in result.get("log", ""):
            print("PASS: Used 2d6 damage dice.")
        else:
            print("FAIL: Did not use 2d6 damage dice.")
    else:
        print("Missed (Bad RNG). Unable to verify damage dice this run.")

if __name__ == "__main__":
    main()

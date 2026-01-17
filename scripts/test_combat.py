import os
import sys

# Add the current directory to path so we can import engines
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from char_engine import Character
from combat_engine import resolve_attack, resolve_clash_effect

print("=== ⚔️ MODULE TEST: COMBAT ENGINE ⚔️ ===")

# 1. SETUP DUMMY FIGHTERS
# We manually define stats to ensure we know what SHOULD happen
print("\n[1] Spawning Test Dummies...")
hero = Character("Mammal", "Greatsword", "Plate") 
# Force stats for predictability
hero.derived["HP"] = 20
hero.weapon_name = "Greatsword" # Uses MIGHT

enemy = Character("Reptile", "Spear", "Leather")
enemy.derived["HP"] = 20
enemy.weapon_name = "Spear" # Uses REFLEX or AWARENESS

print(f"    HERO: {hero.species_name} (HP: {hero.current_hp})")
print(f"    FOE:  {enemy.species_name} (HP: {enemy.current_hp})")

# 2. TEST ATTACK
print("\n[2] Testing Attack Roll...")
result = resolve_attack(hero, enemy)
print(f"    Result: {result['outcome']}")
print(f"    Margin: {result['margin']}")
print(f"    Damage: {result['damage']}")
print(f"    Desc:   {result['desc']}")

# 3. TEST CLASH (Force it)
print("\n[3] Testing CLASH Resolution...")
# We fake a clash by calling the function directly
effect_press = resolve_clash_effect("MIGHT", hero, enemy)
print(f"    Option A (PRESS - Might): {effect_press}")

effect_disengage = resolve_clash_effect("REFLEXES", hero, enemy)
print(f"    Option B (DISENGAGE - Reflex): {effect_disengage}")

print("\n=== TEST COMPLETE ===")

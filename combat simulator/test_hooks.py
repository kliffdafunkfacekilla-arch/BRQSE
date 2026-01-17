import sys
import os
import mechanics

# 1. Monkey Patch the Loader so we don't need CSVs
# We need to import the hooks module and modify its 'loader' instance.
from abilities import engine_hooks

# Mock Data
mock_talent_1 = {
    "Talent_Name": "Precision Strike",
    "Effect": "+5 to Hit"
}
mock_talent_2 = {
    "Talent_Name": "Flaming Weapon",
    "Effect": "Deal 1d6 Fire Damage"
}
mock_school_1 = {
    "School": "Pyromancy",
    "Description": "Generic Pyromancy Description"
}
# Inject into loader
engine_hooks.loader.talents = [mock_talent_1, mock_talent_2]
engine_hooks.loader.schools = [mock_school_1]
engine_hooks.loader.species_skills = {}
engine_hooks.loader.skills = []

def run_tests():
    print("=== ABILITY HOOKS STRESS TEST ===")
    
    engine = mechanics.CombatEngine()
    
    # Mock Combatant with Traits support
    p1 = mechanics.Combatant("c:/Users/krazy/Desktop/BRQSE/Saves/Ironclad.json")
    p1.name = "Attacker"
    p1.traits = ["Precision Strike", "Flaming Weapon"]
    
    p2 = mechanics.Combatant("c:/Users/krazy/Desktop/BRQSE/Saves/Ironclad.json")
    p2.name = "Defender"
    p2.hp = 100 # Give plenty of HP
    
    # --- TEST 1: Modifying Attack Rolls ---
    print("\n[TEST 1] Attack Roll Modification (+5 to Hit)")
    # We can't easily see the internal roll, but we can check the LOG or check if margins are high.
    # mechanics.py attack_sequence (now attack_target) doesn't return the raw roll easily, but log contains it.
    
    # Ensure they are adjacent for attack_target range check (default 0,0 is fine)
    res = engine.attack_target(p1, p2)
    
    found_bonus = False
    for line in res:
        if "Effect: +5 to Hit" in line:
            found_bonus = True
            print(f"  PASS: {line}")
            break
            
    if not found_bonus:
        print("  FAIL: Precision Strike did not trigger.")
        print(res)

    # --- TEST 2: Damage Triggers (On Hit) ---
    print("\n[TEST 2] Damage Triggers (Deal 1d6 Fire Damage)")
    # This triggers ON_HIT. We need to ensure we hit.
    # Improve p1 stats to guarantee hit
    p1.stats["Might"] = 20
    
    res = engine.attack_target(p1, p2)
    found_fire = False
    for line in res:
        if "Effect (Fire):" in line:
            found_fire = True
            print(f"  PASS: {line}")
            break
            
    if not found_fire:
        print("  FAIL: Flaming Weapon did not trigger (or missed).")
        # Check if missed
        if any("MISS" in l for l in res):
            print("  (Attack Missed, so verification inconclusive)")

    # --- TEST 3: Breaking It (Missing Context) ---
    print("\n[TEST 3] Attempting Break: Missing Context Keys")
    # Manually calling apply_hooks with bad context
    try:
        bad_ctx = {"attacker": p1} # Missing 'log' and 'target'
        # Flaming Weapon needs 'target' and 'log'. Should crash?
        engine_hooks.apply_hooks(p1, "ON_HIT", bad_ctx)
        print("  PASS (Resilience): Did not crash validly (or effect skipped).")
    except KeyError as e:
        print(f"  FAIL (Crash): Crashed on missing key: {e}")
    except AttributeError as e:
        print(f"  FAIL (Crash): Crashed on Attribute: {e}")
    except Exception as e:
        print(f"  FAIL (Crash): Unexpected crash: {e}")

if __name__ == "__main__":
    run_tests()

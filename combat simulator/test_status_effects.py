"""
Test script for Status Effect Persistence.
Verifies:
1. Effects are applied with durations
2. Effects tick down each turn
3. Effects expire and clear flags
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

import mechanics
from abilities import engine_hooks

def run_tests():
    print("=== STATUS EFFECT PERSISTENCE TEST ===")
    
    engine = mechanics.CombatEngine()
    
    # Load real character or create mock
    p1 = mechanics.Combatant("c:/Users/krazy/Desktop/BRQSE/Saves/Ironclad.json")
    p1.name = "Hero"
    p1.x = 0; p1.y = 0
    
    p2 = mechanics.Combatant("c:/Users/krazy/Desktop/BRQSE/Saves/Ironclad.json")
    p2.name = "Victim"
    p2.x = 1; p2.y = 0
    
    engine.add_combatant(p1, 0, 0)
    engine.add_combatant(p2, 1, 0)
    engine.start_combat()
    
    print("\n[TEST 1] Apply Stun for 2 rounds")
    p2.apply_effect("Stunned", 2)
    print(f"  is_stunned: {p2.is_stunned}")
    print(f"  active_effects: {p2.active_effects}")
    assert p2.is_stunned == True, "FAIL: Stunned flag not set"
    assert len(p2.active_effects) == 1, "FAIL: Effect not tracked"
    print("  PASS")
    
    print("\n[TEST 2] Tick effects (1 turn passes)")
    expired = p2.tick_effects()
    print(f"  Expired: {expired}")
    print(f"  is_stunned: {p2.is_stunned}")
    print(f"  Remaining duration: {p2.active_effects[0]['duration'] if p2.active_effects else 'N/A'}")
    assert p2.is_stunned == True, "FAIL: Stunned cleared too early"
    assert p2.active_effects[0]['duration'] == 1, "FAIL: Duration not decremented"
    print("  PASS")
    
    print("\n[TEST 3] Tick effects (2nd turn - should expire)")
    expired = p2.tick_effects()
    print(f"  Expired: {expired}")
    print(f"  is_stunned: {p2.is_stunned}")
    assert p2.is_stunned == False, "FAIL: Stunned not cleared on expiry"
    assert len(p2.active_effects) == 0, "FAIL: Effect not removed from list"
    print("  PASS")
    
    print("\n[TEST 4] Poison (3 rounds default)")
    p2.apply_effect("Poisoned", 3)
    print(f"  is_poisoned: {p2.is_poisoned}")
    for i in range(3):
        p2.tick_effects()
        print(f"  After tick {i+1}: is_poisoned={p2.is_poisoned}, effects={len(p2.active_effects)}")
    assert p2.is_poisoned == False, "FAIL: Poison didn't clear after 3 ticks"
    print("  PASS")
    
    print("\n=== ALL TESTS PASSED ===")

if __name__ == "__main__":
    run_tests()

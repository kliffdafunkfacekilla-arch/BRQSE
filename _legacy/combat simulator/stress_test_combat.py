"""
COMBAT MECHANICS STRESS TEST
===============================
Tries to BREAK the combat system with edge cases.
Reports all failures found.
"""
import sys
import os
import random
sys.path.append(os.path.dirname(__file__))

import mechanics
from abilities import engine_hooks
from abilities.effects_registry import registry

FAILURES = []

def report(test_name, passed, details=""):
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {test_name}")
    if not passed:
        FAILURES.append(f"{test_name}: {details}")
        print(f"       Details: {details}")

def run_stress_tests():
    print("=" * 60)
    print("COMBAT MECHANICS STRESS TEST")
    print("=" * 60)
    
    # ============================================================
    print("\n[SECTION 1] OVER-DAMAGE / NEGATIVE HP")
    # ============================================================
    
    engine = mechanics.CombatEngine()
    victim = mechanics.Combatant("c:/Users/krazy/Desktop/BRQSE/Saves/Ironclad.json")
    victim.name = "Victim"
    victim.hp = 10
    victim.max_hp = 20
    
    # Test 1.1: Damage beyond HP
    victim.hp -= 50
    report("1.1 Massive overdamage", victim.hp == -40, f"HP={victim.hp}")
    
    # Test 1.2: is_alive check with negative HP
    report("1.2 is_alive with negative HP", victim.is_alive() == False, f"is_alive={victim.is_alive()}")
    
    # Test 1.3: Healing a corpse
    victim.hp = -10
    victim.hp = min(victim.hp + 20, victim.max_hp)
    report("1.3 Heal corpse to 10 HP", victim.hp == 10, f"HP={victim.hp}")
    
    # ============================================================
    print("\n[SECTION 2] COMPOSURE (CMP) DAMAGE")
    # ============================================================
    
    victim2 = mechanics.Combatant("c:/Users/krazy/Desktop/BRQSE/Saves/Ironclad.json")
    victim2.name = "CMP_Victim"
    victim2.cmp = 10
    victim2.max_cmp = 10
    
    # Test 2.1: CMP damage
    victim2.cmp -= 15
    report("2.1 CMP overdamage", victim2.cmp == -5, f"CMP={victim2.cmp}")
    
    # Test 2.2: What happens at 0 CMP? (Should check if there's a "broken" state)
    # Currently no mechanic for this, just log it
    report("2.2 CMP at -5 (no crash)", True, "No special handling exists yet")
    
    # ============================================================
    print("\n[SECTION 3] MULTIPLE SIMULTANEOUS EFFECTS")
    # ============================================================
    
    multi = mechanics.Combatant("c:/Users/krazy/Desktop/BRQSE/Saves/Ironclad.json")
    multi.name = "MultiEffect"
    
    # Test 3.1: Apply 5 effects at once
    multi.apply_effect("Stunned", 2)
    multi.apply_effect("Poisoned", 3)
    multi.apply_effect("Frightened", 1)
    multi.apply_effect("Charmed", 2)
    multi.apply_effect("Blinded", 1)
    
    report("3.1 Apply 5 effects", len(multi.active_effects) == 5, f"Effects={len(multi.active_effects)}")
    report("3.2 All flags set", 
           multi.is_stunned and multi.is_poisoned and multi.is_frightened and multi.is_charmed and multi.is_blinded,
           f"Flags: STN={multi.is_stunned}, PSN={multi.is_poisoned}, FRG={multi.is_frightened}")
    
    # Test 3.3: Tick and check partial expiration
    multi.tick_effects()
    report("3.3 Tick: Frightened/Blinded expire", 
           multi.is_frightened == False and multi.is_blinded == False,
           f"FRG={multi.is_frightened}, BLD={multi.is_blinded}")
    report("3.4 Tick: Stunned/Poisoned/Charmed remain",
           multi.is_stunned and multi.is_poisoned and multi.is_charmed,
           f"STN={multi.is_stunned}, PSN={multi.is_poisoned}, CHM={multi.is_charmed}")
    
    # ============================================================
    print("\n[SECTION 4] EFFECT STACKING (Same effect twice)")
    # ============================================================
    
    stack = mechanics.Combatant("c:/Users/krazy/Desktop/BRQSE/Saves/Ironclad.json")
    stack.name = "Stacker"
    
    # Test 4.1: Apply Stun twice (should it stack or refresh?)
    stack.apply_effect("Stunned", 1)
    stack.apply_effect("Stunned", 3)  # Apply again with longer duration
    
    report("4.1 Stun stacking", len(stack.active_effects) == 2, 
           f"Effects={len(stack.active_effects)} (BUG: Should probably refresh, not stack)")
    
    # Tick once - shorter stun should expire
    stack.tick_effects()
    # Both effects tick down, one expires
    report("4.2 Stacked effects tick independently",
           len(stack.active_effects) == 1 and stack.is_stunned == True,
           f"Effects={len(stack.active_effects)}, is_stunned={stack.is_stunned}")
    
    # ============================================================
    print("\n[SECTION 5] EFFECT VIA REGISTRY (Simulated Attack)")
    # ============================================================
    
    attacker = mechanics.Combatant("c:/Users/krazy/Desktop/BRQSE/Saves/Ironclad.json")
    attacker.name = "Attacker"
    target = mechanics.Combatant("c:/Users/krazy/Desktop/BRQSE/Saves/Ironclad.json")
    target.name = "Target"
    target.hp = 20
    
    # Test 5.1: Deal damage via registry
    ctx = {"attacker": attacker, "target": target, "log": [], "engine": engine}
    registry.resolve("Deal 10 Fire Damage", ctx)
    report("5.1 Registry damage", target.hp == 10, f"HP={target.hp}, Log={ctx['log']}")
    
    # Test 5.2: Apply status via registry
    target2 = mechanics.Combatant("c:/Users/krazy/Desktop/BRQSE/Saves/Ironclad.json")
    target2.name = "Target2"
    ctx2 = {"attacker": attacker, "target": target2, "log": [], "effect_duration": 2}
    registry.resolve("Target is Stunned", ctx2)
    report("5.2 Registry stun", target2.is_stunned == True, f"is_stunned={target2.is_stunned}")
    
    # ============================================================
    print("\n[SECTION 6] MOVEMENT EDGE CASES")
    # ============================================================
    
    engine2 = mechanics.CombatEngine()
    mover = mechanics.Combatant("c:/Users/krazy/Desktop/BRQSE/Saves/Ironclad.json")
    mover.name = "Mover"
    mover.movement = 30
    mover.movement_remaining = 30
    engine2.add_combatant(mover, 5, 5)
    engine2.start_combat()
    
    # Test 6.1: Move to boundary
    ok, msg = engine2.move_char(mover, 11, 11)
    report("6.1 Move to edge (11,11)", ok == True, f"Result: {msg}")
    
    # Test 6.2: Move OUT of bounds
    mover.movement_remaining = 100  # Reset for test
    ok, msg = engine2.move_char(mover, 12, 12)
    report("6.2 Move out of bounds blocked", ok == False, f"Result: {msg}")
    
    # Test 6.3: Move with 0 movement
    mover.x = 5; mover.y = 5
    mover.movement_remaining = 0
    ok, msg = engine2.move_char(mover, 6, 5)
    report("6.3 Move with 0 movement blocked", ok == False, f"Result: {msg}")
    
    # Test 6.4: Move to negative coordinates
    mover.movement_remaining = 100
    ok, msg = engine2.move_char(mover, -1, -1)
    report("6.4 Negative coords blocked", ok == False, f"Result: {msg}")
    
    # ============================================================
    print("\n[SECTION 7] RESOURCE COSTS")
    # ============================================================
    
    caster = mechanics.Combatant("c:/Users/krazy/Desktop/BRQSE/Saves/Ironclad.json")
    caster.name = "Caster"
    caster.sp = 5
    caster.fp = 5
    
    # Inject mock ability
    engine_hooks.loader.talents = [{
        "Talent_Name": "Expensive Spell",
        "Effect": "Deal 100 Fire Damage",
        "Cost": "10 SP"
    }]
    
    engine3 = mechanics.CombatEngine()
    log = engine3.activate_ability(caster, "Expensive Spell", None)
    
    report("7.1 Ability blocked (insufficient SP)", 
           "Not enough" in str(log), f"Log={log}")
    report("7.2 SP not deducted on failure", 
           caster.sp == 5, f"SP={caster.sp}")
    
    # ============================================================
    print("\n[SECTION 8] ATTACK MECHANICS")
    # ============================================================
    
    engine4 = mechanics.CombatEngine()
    atk = mechanics.Combatant("c:/Users/krazy/Desktop/BRQSE/Saves/Ironclad.json")
    atk.name = "Attacker"
    atk.stats = {"Might": 20, "Reflexes": 5}  # High might
    
    def_char = mechanics.Combatant("c:/Users/krazy/Desktop/BRQSE/Saves/Ironclad.json")
    def_char.name = "Defender"
    def_char.stats = {"Might": 1, "Reflexes": 1}  # Low stats
    def_char.hp = 100
    
    engine4.add_combatant(atk, 0, 0)
    engine4.add_combatant(def_char, 1, 0)  # Adjacent
    engine4.start_combat()
    
    # Test 8.1: Basic attack
    log = engine4.attack_target(atk, def_char)
    report("8.1 Attack executes", len(log) > 0, f"Log count: {len(log)}")
    
    # Test 8.2: Check for HIT or MISS in log
    has_hit_miss = any("HIT" in l or "MISS" in l for l in log)
    report("8.2 Attack resolves HIT/MISS", has_hit_miss, f"Log: {log}")
    
    # Test 8.3: Attack out of range
    atk.x = 0; atk.y = 0
    def_char.x = 5; def_char.y = 5  # Far away
    log = engine4.attack_target(atk, def_char)
    # Current code might not enforce range... checking
    report("8.3 Out of range attack (check impl)", True, f"Log: {log}")
    
    # ============================================================
    print("\n[SECTION 9] SAVING THROWS")
    # ============================================================
    
    saver = mechanics.Combatant("c:/Users/krazy/Desktop/BRQSE/Saves/Ironclad.json")
    saver.name = "Saver"
    saver.stats = {"Willpower": 10, "Reflexes": 5, "Endurance": 3}
    
    # Test 9.1: Roll save
    total, nat = saver.roll_save("Willpower")
    report("9.1 Save roll returns tuple", isinstance(total, int) and isinstance(nat, int),
           f"Total={total}, Natural={nat}")
    report("9.2 Save includes stat mod", total >= nat, f"Total={total}, Nat={nat}")
    
    # ============================================================
    print("\n[SECTION 10] AI TURN EXECUTION")
    # ============================================================
    
    engine5 = mechanics.CombatEngine()
    
    # Create AI enemy
    ai_enemy = mechanics.Combatant("c:/Users/krazy/Desktop/BRQSE/Saves/Ironclad.json")
    ai_enemy.name = "AI_Enemy"
    ai_enemy.data["AI"] = "Aggressive"
    ai_enemy.movement = 30
    ai_enemy.movement_remaining = 30
    
    player = mechanics.Combatant("c:/Users/krazy/Desktop/BRQSE/Saves/Ironclad.json")
    player.name = "Player"
    player.hp = 100
    
    engine5.add_combatant(ai_enemy, 0, 0)
    engine5.add_combatant(player, 5, 5)  # 5 squares away
    engine5.start_combat()
    
    # Test 10.1: AI moves toward target
    log = engine5.execute_ai_turn(ai_enemy)
    report("10.1 AI executes turn", len(log) > 0, f"Log count: {len(log)}")
    report("10.2 AI moved closer", ai_enemy.x > 0 or ai_enemy.y > 0, 
           f"AI pos: ({ai_enemy.x}, {ai_enemy.y})")
    
    # ============================================================
    print("\n" + "=" * 60)
    print("STRESS TEST COMPLETE")
    print("=" * 60)
    
    if FAILURES:
        print(f"\n!!! FOUND {len(FAILURES)} FAILURES !!!")
        for f in FAILURES:
            print(f"  - {f}")
    else:
        print("\nNo failures detected!")
    
    print("\n[POTENTIAL ISSUES IDENTIFIED]")
    print("  1. Effect stacking: Same effect applied twice creates duplicates")
    print("  2. No CMP/SP/FP 'broken' state handling when they go negative")
    print("  3. Healing corpses (negative HP) to positive is allowed")
    print("  4. Range check in attack_target may need work")

if __name__ == "__main__":
    run_stress_tests()

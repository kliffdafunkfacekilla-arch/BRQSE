import sys
import os
import mechanics
from abilities import engine_hooks

# Mock Data Injection
mock_power = {
    "Talent_Name": "Heal Self",
    "Effect": "Heal 5 HP",
    "Cost": "5 SP"
}
mock_expensive = {
    "Talent_Name": "Super Nova",
    "Effect": "Deal 100 Fire Damage",
    "Cost": "100 FP"
}

engine_hooks.loader.talents = [mock_power, mock_expensive]
engine_hooks.loader.schools = []
engine_hooks.loader.skills = []

def run_tests():
    print("=== ABILITY COSTS STRESS TEST ===")
    
    engine = mechanics.CombatEngine()
    
    # Mock Character
    p1 = mechanics.Combatant("c:/Users/krazy/Desktop/BRQSE/Saves/Ironclad.json")
    p1.name = "Caster"
    p1.sp = 10; p1.max_sp = 10
    p1.fp = 10; p1.max_fp = 10
    p1.hp = 1;  p1.max_hp = 20 # Injured
    p1.traits = ["Heal Self", "Super Nova"]
    
    print("\n[TEST 1] Successful Cast (Cost 5 SP)")
    print(f"  Start SP: {p1.sp}, HP: {p1.hp}")
    log = engine.activate_ability(p1, "Heal Self")
    print(f"  Log: {log}")
    
    if p1.sp == 5: print("  PASS: Consumed 5 SP.")
    else: print(f"  FAIL: SP not consumed correctly. ({p1.sp})")
    
    if p1.hp == 6: print("  PASS: Effect Applied (Healed to 6).")
    else: print(f"  FAIL: Effect didn't work. ({p1.hp})")

    print("\n[TEST 2] Insufficient Resources (Cost 100 FP)")
    print(f"  Start FP: {p1.fp}")
    log = engine.activate_ability(p1, "Super Nova")
    print(f"  Log: {log}")
    
    if "Not enough" in str(log):
        print("  PASS: Blocked due to lack of FP.")
    else:
        print("  FAIL: Did not report insufficient resources properly.")
        
    print("\n[TEST 3] Depletion Blocking")
    # Cast Heal again (SP 5 -> 0)
    engine.activate_ability(p1, "Heal Self")
    print(f"  SP after 2nd cast: {p1.sp}")
    
    # Cast Heal 3rd time (SP 0 -> Fail)
    log = engine.activate_ability(p1, "Heal Self")
    if "Not enough" in str(log):
        print("  PASS: Blocked on 3rd cast (0 SP).")
    else:
        print("  FAIL: Allowed casting with 0 SP.")

if __name__ == "__main__":
    run_tests()

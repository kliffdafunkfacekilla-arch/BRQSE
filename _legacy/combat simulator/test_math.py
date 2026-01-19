import sys
import os
import random

# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import mechanics

def test_combat_math():
    print("=== TESTING COMBAT MATH ===")
    
    # 1. Setup Engine
    engine = mechanics.CombatEngine()
    
    # 2. Mock Fighters with specific stats
    class MockFighter:
        def __init__(self, name, might, reflexes):
            self.name = name
            self.hp = 10
            self.stats = {"Might": might, "Reflexes": reflexes}
            self.skills = ["Weapon", "Dodge"] # Give them rank 1 in relevant skills
            
            self.cmp = 10
            self.derived = {"Speed": 10}
            self.initiative = 0 # manually set later if needed
            
        def get_stat(self, name): return self.stats.get(name, 0)
        def get_skill_rank(self, name): return 1
        def is_alive(self): return self.hp > 0
        
    attacker = MockFighter("Hero", 5, 2)  # Might 5
    defender = MockFighter("Villain", 3, 4) # Reflex 4
    
    # 3. Test Attack Math
    # Attacker: d20 + Might(5) + Skill(1) = d20 + 6
    # Defender: d20 + Reflex(4) + Skill(1) = d20 + 5
    # Margin = (d20+6) - (d20+5)
    
    print("\n[TEST 1] Attack Resolution")
    print(f"Attacker Stats: Might 5, Skill 1 (Total +6)")
    print(f"Defender Stats: Reflex 4, Skill 1 (Total +5)")
    
    # Force Random Seed for predictability? No, let's run a few times and check bounds.
    for i in range(3):
        res = engine.attack_sequence(attacker, defender)
        print(f"  Roll {i+1}: {res[-1]}")
        # Parse log for verification? 
        # Log format: "ATK: X (...) vs DEF: Y (...)"
        
    # 4. Test Damage Math
    # Damage = 1d6 + Might(5) -> Range 6-11
    print("\n[TEST 2] Damage Check")
    min_dmg = 99
    max_dmg = 0
    for _ in range(20):
        dmg = engine.calc_damage(attacker, 5)
        min_dmg = min(min_dmg, dmg)
        max_dmg = max(max_dmg, dmg)
    
    print(f"  Damage Range Observed: {min_dmg}-{max_dmg}")
    if min_dmg >= 6 and max_dmg <= 11:
        print("  PASS: Damage within expected range (1d6 + 5)")
    else:
        print("  FAIL: Damage Calculation Wrong")

    # 5. Test Clash Trigger
    print("\n[TEST 3] Clash Trigger")
    # We can't easily force a tie with random rolls without mocking random.randint
    # But we can verify specific inputs manually calling attack_sequence logic abstractly?
    # Actually, let's just inspect the code logic visually we did that.
    # Let's try to mock the engine's internal random to force a tie.
    
    original_randint = random.randint
    def mock_randint(a, b): return 10 # Always roll 10
    random.randint = mock_randint
    
    res = engine.attack_sequence(attacker, defender)
    random.randint = original_randint # Restore
    
    # With rolls initialized to 10:
    # Atk: 10 + 6 = 16
    # Def: 10 + 5 = 15
    # Margin = 1
    # Expect HIT
    if "HIT" in str(res): print(f"  PASS: 16 vs 15 resulted in HIT. {res}")
    else: print(f"  FAIL: Expected HIT. {res}")
    
    # Now force TIE
    attacker.stats["Might"] = 4 # Reduce Atk by 1 -> Total +5
    # Atk: 10 + 5 = 15 vs Def 15
    
    random.randint = mock_randint
    res = engine.attack_sequence(attacker, defender)
    random.randint = original_randint
    
    if "CLASH START" in str(res): print(f"  PASS: 15 vs 15 triggered CLASH. {res}")
    else: print(f"  FAIL: Expected Clash. {res}")

if __name__ == "__main__":
    test_combat_math()

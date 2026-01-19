import sys
import os
import mechanics

def run_tests():
    print("=== TACTICAL ARENA STRESS TEST ===")
    
    # Setup
    engine = mechanics.CombatEngine()
    
    # Mock Fighters
    class MockFighter:
        def __init__(self, name, speed):
            self.name = name
            self.derived = {"Speed": speed}
            self.hp = 20; self.max_hp = 20
            self.inventory = [] 
            self.weapon_db = {}
            self.x = 0; self.y = 0
            self.stats = {"Might": 5, "Reflexes": 1} # Default high might
            self.skills = []
            self.species = "Human" # Hook support
            self.traits = []
            self.powers = []
            self.movement = speed # Fix logic mirroring Combatant
            self.movement_remaining = speed
            
        def roll_initiative(self): self.initiative = 10; return 10
        def is_alive(self): return self.hp > 0
        def get_stat(self, s): return self.stats.get(s, 0)
        def get_skill_rank(self, s): return 0
        
    p1 = MockFighter("Hero", 20) # Speed 20 (4 squares)
    p2 = MockFighter("Villain", 20)
    
    engine.add_combatant(p1, 5, 5) # Center
    engine.add_combatant(p2, 6, 5) # Adjacent Right
    
    print("\n[TEST 1] Movement Constraints (Speed 20, 5ft/sq = 4 squares)")
    # Valid Move (3 squares)
    ok, msg = engine.move_char(p1, 2, 5)
    if ok: print("  PASS: Moved 3 squares.")
    else: print(f"  FAIL: Should have moved. {msg}")
    
    # Invalid Move (5 squares away from 2,5 -> 7,5)
    # 2,5 to 7,5 is delta 5 = 25ft. Speed 20.
    ok, msg = engine.move_char(p1, 7, 5)
    if not ok: print(f"  PASS: Blocked excess move. {msg}")
    else: print("  FAIL: Allowed move beyond speed!")

    print("\n[TEST 2] Collision")
    # P2 is at 6,5. P1 try to move there.
    ok, msg = engine.move_char(p1, 6, 5)
    if not ok and "Blocked" in msg: print("  PASS: Collision detected.")
    else: print(f"  FAIL: Moved into occupied square! {msg}")

    print("\n[TEST 3] Attack Range")
    # Move P1 far away (0,0) and P2 at (6,5)
    p1.x, p1.y = 0, 0
    res = engine.attack_target(p1, p2)
    if "out of range" in res[0]: print("  PASS: Melee range enforced.")
    else: print(f"  FAIL: Attacked form across map! {res}")
    
    # Move Adjacent (5,5 and 6,5)
    p1.x, p1.y = 5, 5
    res = engine.attack_target(p1, p2)
    if "attacks" in res[0]: print("  PASS: Adjacent attack allowed.")
    else: print(f"  FAIL: Adjacent attack blocked. {res}")

    print("\n[TEST 4] Clash Push Physics")
    # Setup Clash manually
    engine.clash_participants = (p1, p2)
    engine.clash_stat = "Might" # Should Push Back 1 & Follow 1
    
    # P1 (5,5) vs P2 (6,5)
    # P1 Wins. P2 should be pushed to (7,5). P1 follows to (6,5).
    # NOTE: mechanics.py random outcome logic makes "Winner" random.
    # We need to force P1 win or logic check result.
    
    # Force stats to ensure high roll for P1
    p1.stats["Might"] = 100
    p2.stats["Might"] = 0
    
    log = engine.resolve_clash("PRESS")
    print(f"  Log: {log[-1]}")
    
    print(f"  P1 Pos: {p1.x},{p1.y} (Expected 6,5)")
    print(f"  P2 Pos: {p2.x},{p2.y} (Expected 7,5)")
    
    if p1.x == 6 and p2.x == 7: print("  PASS: Push & Follow physics worked.")
    else: print("  FAIL: Physics calculation wrong.")
    
    print("\n[TEST 5] Breaking Boundaries (The 'Break It' Test)")
    # Logic doesn't check Grid Size (only distance).
    # Can I move to -50, -50 if I have speed?
    p1.derived["Speed"] = 1000
    ok, msg = engine.move_char(p1, -10, -10)
    if not ok and "Out of Bounds" in msg:
        print("  PASS: System blocked void walking.")
    else:
        print(f"  FAIL: Still allowed void walking! {msg}")

    print("\n[TEST 6] Movement Budget Depletion")
    # Reset P1 at 0,0 with 20 ft speed (4 squares)
    p1.x, p1.y = 0, 0
    p1.movement = 20
    p1.movement_remaining = 20
    
    # Move 1: 0,0 -> 2,0 (10ft cost)
    ok, msg = engine.move_char(p1, 2, 0)
    print(f"  Move 1: {msg}")
    
    # Move 2: 2,0 -> 3,0 (5ft cost, Total 15)
    ok, msg = engine.move_char(p1, 3, 0)
    print(f"  Move 2: {msg}")
    
    # Move 3: 3,0 -> 5,0 (10ft cost. Total 25. Should FAIL)
    ok, msg = engine.move_char(p1, 5, 0)
    if not ok and "Not enough movement" in msg:
        print("  PASS: Movement budget exhausted correctly.")
    else:
        print(f"  FAIL: Allowed move without budget! {msg}")

if __name__ == "__main__":
    run_tests()


"""
ENEMY AI STRESS TEST
Tries to break the AI in every way possible.
"""

import sys
import os
import random
import json
import traceback

# Add paths
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "combat simulator"))

from AI.enemy_ai import EnemyAI, Behavior

# Mock Combatant for testing
class MockCombatant:
    def __init__(self, name, x=0, y=0):
        self.name = name
        self.x = x
        self.y = y
        self.stats = {
            "Might": random.randint(8, 16),
            "Reflexes": random.randint(8, 16),
            "Endurance": random.randint(8, 16),
            "Vitality": random.randint(8, 16),
            "Finesse": random.randint(8, 16),
            "Knowledge": random.randint(8, 16),
        }
        self.derived = {"HP": 20, "Speed": 30}
        self.max_hp = 20
        self.hp = 20
        self.max_cmp = 10
        self.cmp = 10
        self.sp = 10
        self.fp = 10
        self.movement = 30
        self.movement_remaining = 30
        self.inventory = []
        self.powers = ["Fireball", "Heal"] if random.random() > 0.5 else []
        self.skills = []
        self.traits = []
        self.data = {}
        
        # Status flags
        self.is_prone = False
        self.is_stunned = False
        self.is_poisoned = False
        
    def is_alive(self):
        return self.hp > 0
        
    def get_stat(self, stat_name):
        return self.stats.get(stat_name, 10)

# Mock Engine for testing
class MockEngine:
    def __init__(self):
        self.combatants = []
        self.clash_active = False
        self.clash_participants = (None, None)
        self.clash_stat = None
        self.attack_count = 0
        self.ability_count = 0
        self.move_count = 0
        self.clash_count = 0
        
    def add_combatant(self, c, x, y):
        c.x = x
        c.y = y
        self.combatants.append(c)
        
    def move_char(self, char, tx, ty):
        self.move_count += 1
        if not (0 <= tx < 12 and 0 <= ty < 12):
            return False, "Out of Bounds!"
        # Check collision
        for c in self.combatants:
            if c != char and c.x == tx and c.y == ty and c.is_alive():
                return False, "Blocked!"
        char.x = tx
        char.y = ty
        char.movement_remaining -= 5
        return True, f"Moved to {tx},{ty}"
        
    def attack_target(self, attacker, target):
        self.attack_count += 1
        log = [f"{attacker.name} attacks {target.name}!"]
        
        # Simulate attack
        atk_roll = random.randint(1, 20) + attacker.get_stat("Might")
        def_roll = random.randint(1, 20) + target.get_stat("Reflexes")
        
        margin = atk_roll - def_roll
        
        if margin == 0:
            self.clash_active = True
            self.clash_participants = (attacker, target)
            self.clash_stat = "Might"
            log.append("CLASH START")
            self.clash_count += 1
        elif margin > 0:
            dmg = random.randint(1, 6) + 2
            target.hp -= dmg
            log.append(f"HIT! Dmg: {dmg}. {target.name} HP: {target.hp}")
        else:
            log.append("MISS!")
            
        return log
        
    def activate_ability(self, char, ability_name, target=None):
        self.ability_count += 1
        log = [f"{char.name} uses {ability_name}!"]
        if target:
            target.hp -= random.randint(1, 4)
            log.append(f"Effect applied to {target.name}")
        return log
        
    def resolve_clash(self, choice):
        self.clash_active = False
        p1, p2 = self.clash_participants
        log = [f"CLASH RESOLVED using {choice}"]
        # Random winner
        winner = random.choice([p1, p2])
        log.append(f"{winner.name} WINS!")
        self.clash_participants = (None, None)
        return log

# =====================
# TEST FUNCTIONS
# =====================

def test_basic_100_iterations():
    """Run AI 100 times with random configs"""
    print("\n=== TEST: 100 Basic Iterations ===")
    errors = []
    
    for i in range(100):
        try:
            engine = MockEngine()
            player = MockCombatant("Player", 0, 0)
            enemy = MockCombatant(f"Enemy_{i}", random.randint(1, 10), random.randint(1, 10))
            engine.add_combatant(player, 0, 0)
            engine.add_combatant(enemy, enemy.x, enemy.y)
            
            ai = EnemyAI(engine)
            behavior = random.choice([Behavior.AGGRESSIVE, Behavior.RANGED, Behavior.CAMPER, 
                                      Behavior.FLEEING, Behavior.CASTER, Behavior.SPELLBLADE])
            log = ai.take_turn(enemy, behavior)
            
        except Exception as e:
            errors.append(f"Iteration {i}: {e}\n{traceback.format_exc()}")
    
    print(f"  Completed: 100 iterations")
    print(f"  Errors: {len(errors)}")
    if errors:
        for err in errors[:3]:
            print(f"    {err[:100]}...")
    return len(errors) == 0

def test_multi_enemy_combat():
    """Spawn 10 enemies at once"""
    print("\n=== TEST: 10 Enemies Simultaneously ===")
    errors = []
    
    try:
        engine = MockEngine()
        player = MockCombatant("Player", 5, 5)
        engine.add_combatant(player, 5, 5)
        
        enemies = []
        for i in range(10):
            e = MockCombatant(f"Goblin_{i}", random.randint(0, 11), random.randint(0, 11))
            engine.add_combatant(e, e.x, e.y)
            enemies.append(e)
        
        ai = EnemyAI(engine)
        
        # Run 5 rounds
        for round_num in range(5):
            for enemy in enemies:
                if enemy.is_alive():
                    try:
                        log = ai.take_turn(enemy)
                    except Exception as e:
                        errors.append(f"Round {round_num}, {enemy.name}: {e}")
                        
    except Exception as e:
        errors.append(f"Setup error: {e}")
    
    print(f"  Rounds completed: 5")
    print(f"  AI calls: {10 * 5}")
    print(f"  Errors: {len(errors)}")
    return len(errors) == 0

def test_enemy_vs_enemy():
    """Enemies fighting each other (no player)"""
    print("\n=== TEST: Enemy vs Enemy (No Player) ===")
    errors = []
    
    try:
        engine = MockEngine()
        
        # Only enemies
        e1 = MockCombatant("Red_Goblin", 2, 2)
        e2 = MockCombatant("Blue_Goblin", 8, 8)
        engine.add_combatant(e1, 2, 2)
        engine.add_combatant(e2, 8, 8)
        
        ai = EnemyAI(engine)
        
        # 10 rounds of fighting
        for _ in range(10):
            if e1.is_alive():
                log = ai.take_turn(e1, Behavior.AGGRESSIVE)
            if e2.is_alive():
                log = ai.take_turn(e2, Behavior.AGGRESSIVE)
                
        print(f"  Red_Goblin HP: {e1.hp}/{e1.max_hp}")
        print(f"  Blue_Goblin HP: {e2.hp}/{e2.max_hp}")
        
    except Exception as e:
        errors.append(str(e))
        traceback.print_exc()
    
    return len(errors) == 0

def test_clash_spam():
    """Force many clashes"""
    print("\n=== TEST: Clash Spam (50 clashes) ===")
    errors = []
    
    engine = MockEngine()
    e1 = MockCombatant("Fighter1", 1, 1)
    e2 = MockCombatant("Fighter2", 2, 1)
    engine.add_combatant(e1, 1, 1)
    engine.add_combatant(e2, 2, 1)
    
    ai = EnemyAI(engine)
    
    for _ in range(50):
        try:
            # Force clash by setting flag
            engine.clash_active = True
            engine.clash_participants = (e1, e2)
            engine.clash_stat = random.choice(["Might", "Reflexes", "Finesse"])
            
            # AI should detect and handle
            log = ai._handle_clash(e1, [])
            
        except Exception as e:
            errors.append(str(e))
    
    print(f"  Clashes resolved: 50")
    print(f"  Errors: {len(errors)}")
    return len(errors) == 0

def test_dead_target():
    """AI with dead targets"""
    print("\n=== TEST: Dead Targets ===")
    errors = []
    
    try:
        engine = MockEngine()
        player = MockCombatant("DeadPlayer", 5, 5)
        player.hp = 0  # Already dead
        
        enemy = MockCombatant("Confused_Goblin", 1, 1)
        engine.add_combatant(player, 5, 5)
        engine.add_combatant(enemy, 1, 1)
        
        ai = EnemyAI(engine)
        log = ai.take_turn(enemy, Behavior.AGGRESSIVE)
        
        # Should handle gracefully
        print(f"  Log: {log}")
        
    except Exception as e:
        errors.append(str(e))
        traceback.print_exc()
    
    return len(errors) == 0

def test_no_targets():
    """AI with no valid targets"""
    print("\n=== TEST: No Targets ===")
    errors = []
    
    try:
        engine = MockEngine()
        enemy = MockCombatant("Lonely_Goblin", 5, 5)
        engine.add_combatant(enemy, 5, 5)
        
        ai = EnemyAI(engine)
        log = ai.take_turn(enemy, Behavior.AGGRESSIVE)
        
        print(f"  Log: {log}")
        
    except Exception as e:
        errors.append(str(e))
        traceback.print_exc()
    
    return len(errors) == 0

def test_all_behaviors_all_positions():
    """Test every behavior from every grid position"""
    print("\n=== TEST: All Behaviors x All Positions ===")
    errors = []
    behaviors = [Behavior.AGGRESSIVE, Behavior.RANGED, Behavior.CAMPER, 
                 Behavior.FLEEING, Behavior.CASTER, Behavior.SPELLBLADE]
    
    count = 0
    for beh in behaviors:
        for x in range(0, 12, 3):
            for y in range(0, 12, 3):
                try:
                    engine = MockEngine()
                    player = MockCombatant("Target", 6, 6)
                    enemy = MockCombatant("Tester", x, y)
                    engine.add_combatant(player, 6, 6)
                    engine.add_combatant(enemy, x, y)
                    
                    ai = EnemyAI(engine)
                    log = ai.take_turn(enemy, beh)
                    count += 1
                    
                except Exception as e:
                    errors.append(f"{beh} at ({x},{y}): {e}")
    
    print(f"  Combinations tested: {count}")
    print(f"  Errors: {len(errors)}")
    return len(errors) == 0

def test_resource_exhaustion():
    """AI with 0 resources"""
    print("\n=== TEST: Resource Exhaustion ===")
    errors = []
    
    try:
        engine = MockEngine()
        player = MockCombatant("Player", 5, 5)
        
        poor_mage = MockCombatant("Broke_Mage", 1, 1)
        poor_mage.sp = 0
        poor_mage.fp = 0
        poor_mage.cmp = 0
        poor_mage.movement_remaining = 0
        poor_mage.powers = ["Fireball", "Lightning"]
        
        engine.add_combatant(player, 5, 5)
        engine.add_combatant(poor_mage, 1, 1)
        
        ai = EnemyAI(engine)
        log = ai.take_turn(poor_mage, Behavior.CASTER)
        
        print(f"  Log: {log}")
        
    except Exception as e:
        errors.append(str(e))
        traceback.print_exc()
    
    return len(errors) == 0

def test_extreme_positions():
    """AI at edge/corner positions"""
    print("\n=== TEST: Extreme Positions ===")
    errors = []
    
    positions = [(0,0), (11,0), (0,11), (11,11), (5,0), (0,5), (11,5), (5,11)]
    
    for pos in positions:
        try:
            engine = MockEngine()
            player = MockCombatant("Player", 5, 5)
            enemy = MockCombatant("Edge_Slime", pos[0], pos[1])
            engine.add_combatant(player, 5, 5)
            engine.add_combatant(enemy, pos[0], pos[1])
            
            ai = EnemyAI(engine)
            log = ai.take_turn(enemy, Behavior.AGGRESSIVE)
            
        except Exception as e:
            errors.append(f"Position {pos}: {e}")
    
    print(f"  Positions tested: {len(positions)}")
    print(f"  Errors: {len(errors)}")
    return len(errors) == 0

# =====================
# MAIN
# =====================

if __name__ == "__main__":
    print("=" * 60)
    print("ENEMY AI STRESS TEST")
    print("=" * 60)
    
    results = {}
    
    results["100 Iterations"] = test_basic_100_iterations()
    results["Multi Enemy"] = test_multi_enemy_combat()
    results["Enemy vs Enemy"] = test_enemy_vs_enemy()
    results["Clash Spam"] = test_clash_spam()
    results["Dead Targets"] = test_dead_target()
    results["No Targets"] = test_no_targets()
    results["All Behaviors"] = test_all_behaviors_all_positions()
    results["Resource Empty"] = test_resource_exhaustion()
    results["Extreme Positions"] = test_extreme_positions()
    
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    for test, result in results.items():
        status = "PASS" if result else "FAIL"
        if result: passed += 1
        else: failed += 1
        print(f"  [{status}] {test}")
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n*** ALL TESTS PASSED! AI is robust. ***")
    else:
        print("\n*** SOME TESTS FAILED - See above for details ***")

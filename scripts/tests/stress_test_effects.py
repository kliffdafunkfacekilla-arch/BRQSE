
"""
ENEMY AI + EFFECTS STRESS TEST
Tests AI with status effects and timed effects.
"""

import sys
import os
import random
import traceback

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "combat simulator"))

from AI.enemy_ai import EnemyAI, Behavior

# Mock Combatant with full effect support
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
            "Logic": random.randint(8, 16),
            "Awareness": random.randint(8, 16),
            "Intuition": random.randint(8, 16),
            "Charm": random.randint(8, 16),
            "Willpower": random.randint(8, 16),
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
        
        # All status flags
        self.is_prone = False
        self.is_grappled = False
        self.is_blinded = False
        self.is_restrained = False
        self.is_stunned = False
        self.is_paralyzed = False
        self.is_poisoned = False
        self.is_frightened = False
        self.is_charmed = False
        self.is_deafened = False
        self.is_invisible = False
        self.is_confused = False
        self.is_berserk = False
        self.is_sanctuary = False
        self.taunted_by = None
        
        # Duration-based effects
        self.active_effects = []
        
    def is_alive(self):
        return self.hp > 0
        
    def get_stat(self, stat_name):
        return self.stats.get(stat_name, 10)
    
    def apply_effect(self, effect_name, duration=1, on_expire=None):
        self.active_effects.append({
            "name": effect_name,
            "duration": duration,
            "on_expire": on_expire or f"is_{effect_name.lower()}"
        })
        flag = f"is_{effect_name.lower()}"
        if hasattr(self, flag):
            setattr(self, flag, True)

    def tick_effects(self):
        expired = []
        remaining = []
        
        for eff in self.active_effects:
            if eff["duration"] == -1:
                remaining.append(eff)
                continue
                
            eff["duration"] -= 1
            if eff["duration"] <= 0:
                flag = eff.get("on_expire")
                if flag and hasattr(self, flag):
                    setattr(self, flag, False)
                expired.append(eff["name"])
            else:
                remaining.append(eff)
        
        self.active_effects = remaining
        return expired

# Mock Engine
class MockEngine:
    def __init__(self):
        self.combatants = []
        self.clash_active = False
        self.clash_participants = (None, None)
        self.clash_stat = None
        
    def add_combatant(self, c, x, y):
        c.x = x
        c.y = y
        self.combatants.append(c)
        
    def move_char(self, char, tx, ty):
        if not (0 <= tx < 12 and 0 <= ty < 12):
            return False, "Out of Bounds!"
        for c in self.combatants:
            if c != char and c.x == tx and c.y == ty and c.is_alive():
                return False, "Blocked!"
        char.x = tx
        char.y = ty
        char.movement_remaining -= 5
        return True, f"Moved to {tx},{ty}"
        
    def attack_target(self, attacker, target):
        log = [f"{attacker.name} attacks {target.name}!"]
        
        # Check attacker status
        if attacker.is_stunned:
            log.append("But is STUNNED! Attack fails.")
            return log
        if attacker.is_paralyzed:
            log.append("But is PARALYZED! Cannot act.")
            return log
        if attacker.is_frightened and target == attacker.taunted_by:
            log.append("FRIGHTENED! Disadvantage on attack.")
        if attacker.is_blinded:
            log.append("BLINDED! Disadvantage on attack.")
            
        # Check target status
        if target.is_sanctuary:
            log.append(f"{target.name} is under SANCTUARY! Attack deflected.")
            return log
            
        atk_roll = random.randint(1, 20) + attacker.get_stat("Might")
        def_roll = random.randint(1, 20) + target.get_stat("Reflexes")
        
        # Disadvantage from effects
        if attacker.is_blinded or attacker.is_frightened:
            atk_roll = min(atk_roll, random.randint(1, 20) + attacker.get_stat("Might"))
            
        # Advantage against prone/restrained
        if target.is_prone or target.is_restrained:
            atk_roll = max(atk_roll, random.randint(1, 20) + attacker.get_stat("Might"))
            log.append(f"Advantage vs {target.name} (Prone/Restrained)")
        
        margin = atk_roll - def_roll
        
        if margin == 0:
            self.clash_active = True
            self.clash_participants = (attacker, target)
            self.clash_stat = "Might"
            log.append("CLASH START")
        elif margin > 0:
            dmg = random.randint(1, 6) + 2
            
            # Poison tick
            if attacker.is_poisoned:
                attacker.hp -= 1
                log.append("Poison ticks! 1 dmg to self.")
                
            target.hp -= dmg
            log.append(f"HIT! Dmg: {dmg}. {target.name} HP: {target.hp}")
        else:
            log.append("MISS!")
            
        return log
        
    def activate_ability(self, char, ability_name, target=None):
        log = [f"{char.name} uses {ability_name}!"]
        
        if char.is_stunned or char.is_paralyzed:
            log.append("Cannot act - incapacitated!")
            return log
            
        if target:
            target.hp -= random.randint(1, 4)
            log.append(f"Effect applied to {target.name}")
        return log
        
    def resolve_clash(self, choice):
        self.clash_active = False
        p1, p2 = self.clash_participants
        log = [f"CLASH RESOLVED using {choice}"]
        winner = random.choice([p1, p2])
        log.append(f"{winner.name} WINS!")
        self.clash_participants = (None, None)
        return log

# =====================
# EFFECT TESTS
# =====================

def test_stunned_enemy():
    """AI with stunned status"""
    print("\n=== TEST: Stunned Enemy ===")
    errors = []
    
    try:
        engine = MockEngine()
        player = MockCombatant("Player", 5, 5)
        
        stunned_goblin = MockCombatant("Stunned_Goblin", 4, 5)
        stunned_goblin.is_stunned = True
        stunned_goblin.apply_effect("Stunned", duration=2)
        
        engine.add_combatant(player, 5, 5)
        engine.add_combatant(stunned_goblin, 4, 5)
        
        ai = EnemyAI(engine)
        
        # Turn 1 - Stunned
        log1 = ai.take_turn(stunned_goblin, Behavior.AGGRESSIVE)
        print(f"  Turn 1 (Stunned): {log1}")
        
        # Tick effect
        expired = stunned_goblin.tick_effects()
        print(f"  Effects expired: {expired}")
        
        # Turn 2 - Still stunned
        log2 = ai.take_turn(stunned_goblin, Behavior.AGGRESSIVE)
        print(f"  Turn 2: {log2}")
        
        # Tick again
        expired = stunned_goblin.tick_effects()
        print(f"  Effects expired: {expired}")
        
        # Turn 3 - Should be free
        log3 = ai.take_turn(stunned_goblin, Behavior.AGGRESSIVE)
        print(f"  Turn 3 (Free): {log3}")
        
    except Exception as e:
        errors.append(str(e))
        traceback.print_exc()
    
    return len(errors) == 0

def test_all_status_effects():
    """Apply every status effect"""
    print("\n=== TEST: All Status Effects ===")
    errors = []
    
    effects = ["prone", "grappled", "blinded", "restrained", "stunned", 
               "paralyzed", "poisoned", "frightened", "charmed", "deafened",
               "invisible", "confused", "berserk", "sanctuary"]
    
    for effect in effects:
        try:
            engine = MockEngine()
            player = MockCombatant("Player", 5, 5)
            enemy = MockCombatant(f"{effect.title()}_Enemy", 4, 5)
            
            # Apply effect
            flag = f"is_{effect}"
            if hasattr(enemy, flag):
                setattr(enemy, flag, True)
            enemy.apply_effect(effect.title(), duration=1)
            
            engine.add_combatant(player, 5, 5)
            engine.add_combatant(enemy, 4, 5)
            
            ai = EnemyAI(engine)
            log = ai.take_turn(enemy, Behavior.AGGRESSIVE)
            
            # Tick and clear
            expired = enemy.tick_effects()
            
        except Exception as e:
            errors.append(f"{effect}: {e}")
    
    print(f"  Effects tested: {len(effects)}")
    print(f"  Errors: {len(errors)}")
    if errors:
        for e in errors:
            print(f"    - {e}")
    return len(errors) == 0

def test_multi_effect_stacking():
    """Multiple effects on one character"""
    print("\n=== TEST: Multi-Effect Stacking ===")
    errors = []
    
    try:
        engine = MockEngine()
        player = MockCombatant("Player", 5, 5)
        
        cursed = MockCombatant("Cursed_Warrior", 4, 5)
        cursed.is_poisoned = True
        cursed.is_blinded = True
        cursed.is_frightened = True
        cursed.apply_effect("Poisoned", duration=3)
        cursed.apply_effect("Blinded", duration=2)
        cursed.apply_effect("Frightened", duration=1)
        
        engine.add_combatant(player, 5, 5)
        engine.add_combatant(cursed, 4, 5)
        
        ai = EnemyAI(engine)
        
        print(f"  Active effects: {len(cursed.active_effects)}")
        
        for turn in range(4):
            log = ai.take_turn(cursed, Behavior.AGGRESSIVE)
            expired = cursed.tick_effects()
            print(f"  Turn {turn+1}: {len(cursed.active_effects)} effects, Expired: {expired}")
            
            # Check HP (poison should tick)
            # Note: Our mock doesn't auto-tick poison damage, but real engine does
            
    except Exception as e:
        errors.append(str(e))
        traceback.print_exc()
    
    return len(errors) == 0

def test_permanent_effects():
    """Effects with duration -1 (permanent)"""
    print("\n=== TEST: Permanent Effects ===")
    errors = []
    
    try:
        engine = MockEngine()
        player = MockCombatant("Player", 5, 5)
        
        cursed = MockCombatant("Cursed_Forever", 4, 5)
        cursed.is_charmed = True
        cursed.apply_effect("Charmed", duration=-1)  # Permanent
        
        engine.add_combatant(player, 5, 5)
        engine.add_combatant(cursed, 4, 5)
        
        ai = EnemyAI(engine)
        
        for turn in range(5):
            log = ai.take_turn(cursed, Behavior.AGGRESSIVE)
            expired = cursed.tick_effects()
            
        # Should still have the effect
        print(f"  After 5 turns, effects: {len(cursed.active_effects)}")
        print(f"  is_charmed: {cursed.is_charmed}")
        
        if len(cursed.active_effects) != 1 or not cursed.is_charmed:
            errors.append("Permanent effect was cleared!")
            
    except Exception as e:
        errors.append(str(e))
        traceback.print_exc()
    
    return len(errors) == 0

def test_effect_interaction_combat():
    """Full combat with effects"""
    print("\n=== TEST: Full Combat with Effects ===")
    errors = []
    
    try:
        engine = MockEngine()
        
        # Fighter vs Mage
        fighter = MockCombatant("Fighter", 2, 2)
        mage = MockCombatant("Mage", 8, 8)
        mage.powers = ["Fireball", "Sleep", "Fear"]
        
        engine.add_combatant(fighter, 2, 2)
        engine.add_combatant(mage, 8, 8)
        
        ai = EnemyAI(engine)
        
        # Simulate 10 rounds
        for round_num in range(10):
            if not fighter.is_alive() or not mage.is_alive():
                break
                
            # Random effects
            if random.random() < 0.3:
                fighter.is_poisoned = True
                fighter.apply_effect("Poisoned", 2)
            if random.random() < 0.2:
                mage.is_frightened = True
                mage.apply_effect("Frightened", 1)
                
            # AI turns
            if fighter.is_alive():
                log1 = ai.take_turn(fighter, Behavior.AGGRESSIVE)
                fighter.tick_effects()
                
            if mage.is_alive():
                log2 = ai.take_turn(mage, Behavior.CASTER)
                mage.tick_effects()
                
        print(f"  Combat ended at round {round_num + 1}")
        print(f"  Fighter HP: {fighter.hp}/{fighter.max_hp}")
        print(f"  Mage HP: {mage.hp}/{mage.max_hp}")
        
    except Exception as e:
        errors.append(str(e))
        traceback.print_exc()
    
    return len(errors) == 0

def test_taunt_mechanic():
    """Taunt forcing target"""
    print("\n=== TEST: Taunt Mechanic ===")
    errors = []
    
    try:
        engine = MockEngine()
        
        tank = MockCombatant("Tank", 3, 3)
        enemy = MockCombatant("Taunted_Enemy", 5, 5)
        squishy = MockCombatant("Squishy_Mage", 7, 7)
        
        # Enemy is taunted by Tank
        enemy.taunted_by = tank
        
        engine.add_combatant(tank, 3, 3)
        engine.add_combatant(enemy, 5, 5)
        engine.add_combatant(squishy, 7, 7)
        
        ai = EnemyAI(engine)
        
        # AI should target Tank (closest hostile is still found normally, 
        # but taunted_by could be used for more advanced AI)
        log = ai.take_turn(enemy, Behavior.AGGRESSIVE)
        print(f"  Log: {log}")
        
    except Exception as e:
        errors.append(str(e))
        traceback.print_exc()
    
    return len(errors) == 0

def test_100_with_random_effects():
    """100 iterations with random effects"""
    print("\n=== TEST: 100 Iterations with Random Effects ===")
    errors = []
    effect_names = ["Poisoned", "Blinded", "Stunned", "Frightened", "Charmed", "Prone"]
    
    for i in range(100):
        try:
            engine = MockEngine()
            player = MockCombatant("Player", 5, 5)
            enemy = MockCombatant(f"Enemy_{i}", random.randint(0, 11), random.randint(0, 11))
            
            # Random effects on both
            for _ in range(random.randint(0, 3)):
                eff = random.choice(effect_names)
                target = random.choice([player, enemy])
                flag = f"is_{eff.lower()}"
                if hasattr(target, flag):
                    setattr(target, flag, True)
                target.apply_effect(eff, random.randint(1, 3))
            
            engine.add_combatant(player, 5, 5)
            engine.add_combatant(enemy, enemy.x, enemy.y)
            
            ai = EnemyAI(engine)
            behavior = random.choice([Behavior.AGGRESSIVE, Behavior.RANGED, Behavior.CASTER])
            
            for _ in range(random.randint(1, 5)):
                if enemy.is_alive() and player.is_alive():
                    log = ai.take_turn(enemy, behavior)
                    enemy.tick_effects()
                    player.tick_effects()
                    
        except Exception as e:
            errors.append(f"Iteration {i}: {e}")
    
    print(f"  Completed: 100 iterations")
    print(f"  Errors: {len(errors)}")
    if errors:
        for e in errors[:3]:
            print(f"    - {e[:80]}...")
    return len(errors) == 0

# =====================
# MAIN
# =====================

if __name__ == "__main__":
    print("=" * 60)
    print("ENEMY AI + EFFECTS STRESS TEST")
    print("=" * 60)
    
    results = {}
    
    results["Stunned Enemy"] = test_stunned_enemy()
    results["All Status Effects"] = test_all_status_effects()
    results["Multi-Effect Stacking"] = test_multi_effect_stacking()
    results["Permanent Effects"] = test_permanent_effects()
    results["Full Combat w/ Effects"] = test_effect_interaction_combat()
    results["Taunt Mechanic"] = test_taunt_mechanic()
    results["100 Random Effects"] = test_100_with_random_effects()
    
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
        print("\n*** ALL EFFECT TESTS PASSED! ***")
    else:
        print("\n*** SOME TESTS FAILED ***")

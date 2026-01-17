"""
Test School of Flux effects
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from abilities.effects_registry import registry

# Mock Combatant
class MockTarget:
    def __init__(self, name):
        self.name = name
        self.hp = 50
        self.stats = {"Might": 12, "Reflexes": 10}
        self.inventory = ["Sword", "Shield"]
        self.movement = 30
        self.is_grappled = False
        self.is_restrained = False
        self.is_prone = False
        self.is_poisoned = False
        self.active_effects = []
        
    def is_alive(self):
        return self.hp > 0
        
    def apply_effect(self, name, duration, on_expire=None):
        self.active_effects.append({"name": name, "duration": duration})

class MockEngine:
    def __init__(self):
        self.combatants = []
        
    def add(self, c, x, y):
        c.x = x
        c.y = y
        self.combatants.append(c)

print("=" * 50)
print("SCHOOL OF FLUX EFFECT TESTS")
print("=" * 50)

# Test each Flux effect
flux_effects = [
    ("Ethereal", "Become Ethereal and immune to physical damage"),
    ("Phase", "Allow ally to phase through walls"),
    ("Walk through solid wall", "Phase walk through obstacles"),
    ("Amorphous", "Become Amorphous and immune to crits"),
    ("Displacement", "You appear 5ft from your real position"),
    ("Disintegrate", "Disintegrate the target completely"),
    ("Damage over Time", "Apply bleeding DoT for 3 rounds"),
    ("Cut off a limb", "Sever the target's limb"),
    ("Compress space to a point", "Pull enemies toward caster"),
    ("Escape grapple", "Escape bindings and restraints"),
    ("Find path", "Magically find path to location"),
    ("Force drop held item", "Disarm the target"),
    ("Grab weapon thrown at you", "Snatch projectile from air"),
    ("Steal equipped item", "Steal an item from target"),
    ("Switch items instantly", "Swap items with target"),
    ("Ignore Armor", "Attack ignores armor rating"),
    ("Precision hit to knock down", "Knock target prone"),
    ("Reduce melee damage", "Halve incoming melee damage"),
    ("Open mechanism", "Pick lock or unlock door"),
    ("Clean poison from liquid", "Purify poison"),
    ("Un-mix potion", "Separate compound"),
]

passed = 0
failed = 0

for effect_name, effect_desc in flux_effects:
    try:
        attacker = MockTarget("Caster")
        target = MockTarget("Enemy")
        engine = MockEngine()
        engine.add(attacker, 5, 5)
        engine.add(target, 6, 5)
        
        ctx = {
            "attacker": attacker,
            "target": target,
            "engine": engine,
            "log": [],
            "incoming_damage": 10
        }
        
        handled = registry.resolve(effect_desc, ctx)
        
        if handled:
            print(f"[PASS] {effect_name}")
            if ctx["log"]:
                print(f"       Log: {ctx['log'][0][:60]}...")
            passed += 1
        else:
            print(f"[FAIL] {effect_name} - Not handled")
            failed += 1
            
    except Exception as e:
        print(f"[ERROR] {effect_name} - {e}")
        failed += 1

print("\n" + "=" * 50)
print(f"RESULTS: {passed} passed, {failed} failed")
print("=" * 50)

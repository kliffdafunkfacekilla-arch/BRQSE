"""
Test School of Vita effects
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
        self.max_hp = 100
        self.stats = {"Might": 12, "Reflexes": 10, "Endurance": 14}
        self.active_effects = []
        self.is_bleeding = True
        self.is_diseased = True
        self.is_poisoned = True
        self.is_alive_flag = True
        self.inventory = []
        
    def is_alive(self):
        return self.is_alive_flag
        
    def apply_effect(self, name, duration, on_expire=None):
        self.active_effects.append({"name": name, "duration": duration})

class MockCommoner(MockTarget):
    def __init__(self, name):
        super().__init__(name)
        self.hp = 10

class MockEngine:
    def __init__(self):
        self.combatants = []
        self.log = [] # Fallback log if not in ctx

print("=" * 50)
print("SCHOOL OF VITA EFFECT TESTS")
print("=" * 50)

# Test each Vita effect
vita_effects = [
    ("Regeneration", "Heal HP every turn"),
    ("Minor Heal", "Heal minor wounds"),
    ("Full Heal", "Full recovery"),
    ("Stop Bleeding", "Stop Bleeding"),
    ("Cure Disease", "Cure Disease"),
    ("Cure Poison", "Cure Poison"),
    ("Lifesteal", "Lifesteal"),
    ("Life Bond", "Share HP"),
    ("Auto-Life", "Auto-Life on death"),
    ("Resurrect", "Resurrect target"),
    ("Consume Ally", "Eat minion to heal"),
    ("Inflict Disease", "Inflict Disease"),
    ("Necrotic Damage", "Necrotic damage"),
    ("Stat Drain", "Drain Stat"),
    ("Massive DoT", "Massive Rapid DoT"),
    ("Contagion", "Spreading infection"),
    ("Creature Bane", "Kill creature type"),
    ("Enlarge", "Enlarge self"),
    ("Grow Wings", "Grow Wings"),
    ("Natural Armor", "Natural Armor"),
    ("Swarm Form", "Turn into bugs"),
    ("Clone", "Grow spare body"),
    ("Animate Plant", "Animate Plant"),
    ("Create Life", "Create new Lifeform"),
    ("Detect Life", "Detect Life"),
    ("Vines", "Vines restrict movement"),
]

passed = 0
failed = 0

for effect_name, effect_desc in vita_effects:
    try:
        attacker = MockTarget("Healer")
        target = MockTarget("Patient")
        minion = MockCommoner("Minion")
        
        # Setup specific conditions
        if effect_name == "Resurrect":
            target.is_alive_flag = False
            target.hp = 0
            
        ctx = {
            "attacker": attacker,
            "target": target,
            "engine": MockEngine(),
            "log": [],
            "incoming_damage": 20 # For lifesteal test
        }
        
        if effect_name == "Consume Ally":
            ctx["target"] = minion # Eat the minion
        
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
        import traceback
        traceback.print_exc()
        failed += 1

print("\n" + "=" * 50)
print(f"RESULTS: {passed} passed, {failed} failed")
print("=" * 50)

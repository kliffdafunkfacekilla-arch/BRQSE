"""
Test School of Lux effects
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
        self.species = []
        self.active_effects = []
        self.is_blinded = False
        self.is_invisible = False
        self.can_see_invisible = False
        self.has_darkvision = False
        self.is_hidden = False
        self.is_ethereal = False
        
    def is_alive(self):
        return self.hp > 0
        
    def apply_effect(self, name, duration, on_expire=None):
        self.active_effects.append({"name": name, "duration": duration})

class MockUndead(MockTarget):
    def __init__(self, name):
        super().__init__(name)
        self.species = ["Undead"]

class MockEngine:
    def __init__(self):
        self.combatants = []
        self.log = [] 

print("=" * 50)
print("SCHOOL OF LUX EFFECT TESTS")
print("=" * 50)

# Test each Lux effect
lux_effects = [
    ("Laser Damage", "Laser Beam Damage"),
    ("Nova", "Massive Light Damage"),
    ("Split Beam", "Split Beam attack"),
    ("Burn Undead", "Burn Undead"),
    ("Flashbang", "Explosion of Light"),
    ("Heat Metal", "Heat Metal"),
    ("See Invisible", "See Invisible"),
    ("X-Ray", "See Through Walls"),
    ("Darkvision", "See in Darkness"),
    ("GPS", "Know Location"),
    ("Postcognition", "Postcognition"),
    ("Scry", "Remote Viewing"),
    ("Bonus Perception", "Bonus Perception"),
    ("Blindness", "Blind foe"),
    ("Perm Blindness", "Permanent Blindness"),
    ("Dazzle", "Dazzle target"),
    ("Block Sight", "Block Sight Line"),
    ("Turn Invisible", "Turn Invisible"),
    ("Disguise", "Alter Self"),
    ("Camouflage", "Blend with surroundings"),
    ("Illusion", "Create Illusion"),
    ("Major Image", "Major Image"),
    ("Hidden Reality", "Hidden from Reality"),
]

passed = 0
failed = 0

for effect_name, effect_desc in lux_effects:
    try:
        attacker = MockTarget("Caster")
        target = MockTarget("Target")
        undead = MockUndead("Skeleton")
        
        ctx = {
            "attacker": attacker,
            "target": target,
            "engine": MockEngine(),
            "log": [],
            "incoming_damage": 10
        }
        
        if effect_name == "Burn Undead":
            ctx["target"] = undead
        
        handled = registry.resolve(effect_desc, ctx)
        
        if handled:
            print(f"[PASS] {effect_name}")
            if ctx["log"]:
                print(f"       Log: {ctx['log'][0][:60]}...")
            
            # Additional checks
            if effect_name == "Burn Undead" and ctx["incoming_damage"] != 20:
                print(f"       [WARN] Damage not doubled! Got {ctx['incoming_damage']}")
            
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

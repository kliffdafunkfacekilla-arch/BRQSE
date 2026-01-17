"""
Test Species effects
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
        self.active_effects = []
        self.is_blinded = False
        self.is_restrained = False
        self.is_grappled = False
        self.is_prone = False
        self.is_immovable = False
        self.cannot_be_flanked = False
        self.has_swim_speed = False
        self.has_fly_speed = False
        self.has_burrow_speed = False
        self.can_breathe_water = False
        
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
print("SPECIES EFFECT TESTS")
print("=" * 50)

# Test each Species effect
species_effects = [
    ("Swim Speed", "Propel: Gain Swim Speed"),
    ("Fly Speed", "Fragile Speed: Gain Fly Speed"),
    ("Burrow Speed", "Earth Glide"),
    ("Climb Speed", "Climber"),
    ("Bio-Sense", "Bio-Sense active"),
    ("Thermal Sight", "Thermal Sight"),
    ("Omni-Vision", "Cannot be Flanked"),
    ("Hearing", "Eavesdrop"),
    ("Anchor", "Anchor: Cannot be moved"),
    ("Slippery", "Slippery skin"),
    ("Withdraw", "Withdraw into shell"),
    ("Web Shot", "Web Shot"),
    ("Spore Cloud", "Release spores"),
    ("Tail Sweep", "Tail Sweep"),
    ("Gust", "Gust of wind"),
    ("Solar Beam", "Solar Beam"),
    ("Lockjaw", "Lockjaw"),
    ("Goodberry", "Create Goodberry"),
    ("Mimicry", "Mimicry"),
    ("Water Breathing", "Breathe underwater"),
    ("Cone Attack", "Cone Attack (15ft)"),
    ("Auto Grapple", "Grapple on hit"),
]

passed = 0
failed = 0

for effect_name, effect_desc in species_effects:
    try:
        attacker = MockTarget("Creature")
        target = MockTarget("Hunter")
        
        ctx = {
            "attacker": attacker,
            "target": target,
            "engine": MockEngine(),
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
        import traceback
        traceback.print_exc()
        failed += 1

print("\n" + "=" * 50)
print(f"RESULTS: {passed} passed, {failed} failed")
print("=" * 50)

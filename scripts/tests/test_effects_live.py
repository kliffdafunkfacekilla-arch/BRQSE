
import sys
import os
import unittest
import importlib.util

# Add root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

# Import EffectRegistry
# Since it uses relative imports internally, we need to load it properly or ensure sys.path allows it.
# Simple way: from brqse_engine.abilities.effects_registry import registry
from brqse_engine.abilities.effects_registry import registry

class MockCombatant:
    def __init__(self, name, hp=20):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.status = {}
        self.active_effects = []
        self.effects_log = [] # Track applied effects here for testing

        # Basic flags
        self.is_stunned = False
        self.is_poisoned = False
        self.is_prone = False
        
    def take_damage(self, amount):
        self.hp -= amount
        return self.hp <= 0
        
    def apply_effect(self, name, duration):
        print(f"DEBUG: Applying {name} for {duration}")
        self.effects_log.append((name, duration))
        if name == "Stunned": self.is_stunned = True
        if name == "Poisoned": self.is_poisoned = True
        if name == "Prone": self.is_prone = True
        
    def remove_effect(self, name):
        pass # Stub

class TestEffectsLive(unittest.TestCase):
    def setUp(self):
        self.attacker = MockCombatant("Attacker", 20)
        self.target = MockCombatant("Target", 20)
        self.ctx = {
            "attacker": self.attacker,
            "target": self.target,
            "log": []
        }

    def test_damage_regex(self):
        # Case 1: Simple Deal Damage
        registry.resolve("Deal 5 Fire Damage", self.ctx)
        self.assertEqual(self.target.hp, 15)
        self.assertTrue(any("5 Fire damage" in l for l in self.ctx["log"]))
        
        # Case 2: Dice Damage (Simulate)
        # "Deal 1d1 Fire Damage" -> 1 dmg
        self.ctx["log"] = []
        registry.resolve("Deal 1d1 Cold Damage", self.ctx)
        self.assertEqual(self.target.hp, 14)
        
    def test_healing_regex(self):
        self.target.hp = 10
        registry.resolve("Heal 5 HP", self.ctx)
        self.assertEqual(self.target.hp, 15)
        
    def test_status_regex(self):
        registry.resolve("Stun target", self.ctx)
        self.assertTrue(self.target.is_stunned)
        
        registry.resolve("Poison target", self.ctx)
        self.assertTrue(self.target.is_poisoned)
        
    def test_movement_regex(self):
        # Push
        registry.resolve("Push 10ft", self.ctx)
        self.assertTrue(any("Pushed 10ft" in l for l in self.ctx["log"]))
        
        # Teleport
        registry.resolve("Teleport 30ft", self.ctx)
        self.assertTrue(any("Teleports 30ft" in l for l in self.ctx["log"]))

    def test_complex_description(self):
        # "Deal 5 Fire Damage and Stun target" -> Should trigger both?
        # Current registry implementation: break after first match?
        # Let's check the code: "handled = True ... # break" is commented out in effects_registry.py
        # So it should handle multiple.
        
        self.target.hp = 20
        self.target.is_stunned = False
        
        # We need to call resolve twice or have a description that matches multiple patterns individually?
        # Actually, registry loops over patterns. If one string matches multiple patterns, they all fire.
        # "Deal 5 Damage Stun" 
        # Pattern 1 match: "Deal 5 Damage"
        # Pattern 2 match: "Stun"
        
        desc = "Deal 5 Fire Damage. Stun target."
        registry.resolve(desc, self.ctx)
        
        self.assertEqual(self.target.hp, 15)
        self.assertTrue(self.target.is_stunned)

if __name__ == '__main__':
    unittest.main()

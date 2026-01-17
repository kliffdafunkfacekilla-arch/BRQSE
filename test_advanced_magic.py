import sys
import os
import unittest
from unittest.mock import MagicMock

# Add path to scripts
sys.path.append(os.path.join(os.path.dirname(__file__), "combat simulator"))
sys.path.append(os.path.join(os.path.dirname(__file__), "."))

try:
    from mechanics import CombatEngine, Combatant
    from abilities.effects_registry import EffectRegistry, EffectRegistry
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

class TestAdvancedMagic(unittest.TestCase):
    def setUp(self):
        self.engine = CombatEngine()
        self.registry = EffectRegistry()
        
        # Create Dummy Combatant
        self.c1 = Combatant(filepath=None, data={
            "Name": "Caster",
            "Species": "Human",
            "Stats": {"Might": 10, "Reflexes": 10},
            "Derived": {"HP": 20, "Speed": 30},
            "Skills": [], "Traits": [], "Powers": []
        })
        self.c1.x, self.c1.y = 5, 5
        self.engine.add_combatant(self.c1, 5, 5)

    def test_create_wall(self):
        print("\n--- Testing Wall Creation ---")
        try:
            # Simulate "Create Wall" effect
            ctx = {"engine": self.engine, "attacker": self.c1, "log": []}
            self.registry.resolve("Create wall", ctx)
            
            wall_loc = (6, 5)
            if wall_loc not in self.engine.walls:
                print(f"FAILURE: Wall not found at {wall_loc}. Walls: {self.engine.walls}")
                self.fail("Wall creation failed")
            print(f"Wall created successfully at {wall_loc}")
            
            # Test Collision
            print("Testing Movement Collision...")
            success, msg = self.engine.move_char(self.c1, 6, 5)
            if success: 
                print(f"FAILURE: Movement was not blocked!")
                self.fail("Movement not blocked by wall")
            print(f"Collision validated: {msg}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.fail(f"Exception in test_create_wall: {e}")

    def test_summoning(self):
        print("\n--- Testing Summoning ---")
        try:
            ctx = {"engine": self.engine, "attacker": self.c1, "log": []}
            initial_count = len(self.engine.combatants)
            
            # Cast Summon
            self.registry.resolve("summon Wolf", ctx)
            
            new_count = len(self.engine.combatants)
            if new_count <= initial_count:
                print(f"FAILURE: Count did not increase. Logic dump: {ctx.get('log')}")
                print(f"Combatants: {self.engine.combatants}")
                self.fail("Summoning failed to add combatant")
            
            minion = self.engine.combatants[-1]
            print(f"Summoned Entity: {minion.name} at ({minion.x}, {minion.y})")
            
            # Check proximity
            if abs(minion.x - self.c1.x) > 1 or abs(minion.y - self.c1.y) > 1:
                print(f"FAILURE: Minion spawned too far: {minion.x},{minion.y} vs {self.c1.x},{self.c1.y}")
            
            # Check Turn Order
            if minion not in self.engine.turn_order:
                print("FAILURE: Minion not in turn order")
                self.fail("Minion missing from turn order")
            print("Summoning verified!")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.fail(f"Exception in test_summoning: {e}")

    def test_species_abilities(self):
        print("\n--- Testing Species Abilities ---")
        try:
            # Setup: Caster at 5,5. Enemy at 6,5 (Adjacent)
            c2 = Combatant(filepath=None, data={
                "Name": "TargetDummy", "Species": "Goblin",
                "Stats": {"Might": 10}, "Derived": {"HP": 10, "Speed": 30}
            })
            self.engine.add_combatant(c2, 6, 5)
            
            # Test 1: Spore Cloud (AoE Poison)
            print("Testing Spore Cloud...")
            ctx = {"engine": self.engine, "attacker": self.c1, "log": []}
            self.registry.resolve("Release spores", ctx)
            
            if c2.is_poisoned:
                print("SUCCESS: Target poisoned by Spore Cloud.")
            else:
                print("FAILURE: Target NOT poisoned.")
                self.fail("Spore Cloud failed to poison adjacent target")

            # Test 2: Gust (Push)
            print("Testing Gust (Push)...")
            ctx = {"engine": self.engine, "attacker": self.c1, "target": c2, "log": []}
            # Gust pushes 2 squares. From 6,5 -> 8,5
            self.registry.resolve("Gust", ctx)
            
            if c2.x == 8 and c2.y == 5:
                print(f"SUCCESS: Target pushed to {c2.x},{c2.y}")
            else:
                print(f"FAILURE: Target at {c2.x},{c2.y}, expected 8,5")
                self.fail("Gust failed to push target")
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.fail(f"Exception in test_species_abilities: {e}")

if __name__ == '__main__':
    unittest.main()


import sys
import os
import unittest
from unittest.mock import MagicMock

# Add path to scripts
sys.path.append(os.path.join(os.path.dirname(__file__), "combat simulator"))
sys.path.append(os.path.join(os.path.dirname(__file__), "."))

try:
    from mechanics import CombatEngine, Combatant
    # Mock AIDecisionEngine is not needed if we want to test real logic, 
    # but we need to ensure the import works in mechanics.
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

class TestAILogic(unittest.TestCase):
    def setUp(self):
        self.engine = CombatEngine()
        
    def test_caster_priority_heal(self):
        print("\n--- Testing AI: Caster Heal Priority ---")
        # 1. Setup Caster (AI)
        caster = Combatant(filepath=None, data={
            "Name": "ClericBot", "Species": "Human",
            "Stats": {"Might": 10}, "Derived": {"HP": 20},
            "AI": "Caster",
            "Powers": ["Heal"] # Helper tag for our simple AI engine
        })
        caster.team = "Empire"
        self.engine.add_combatant(caster, 5, 5)
        
        # 2. Setup Injured Ally
        ally = Combatant(filepath=None, data={
             "Name": "DyingSoldier", "Species": "Human",
             "Stats": {"Might": 10}, "Derived": {"HP": 20}
        })
        ally.hp = 2 # Critical!
        ally.team = "Empire"
        self.engine.add_combatant(ally, 5, 6) # Adjacent
        
        # 3. Setup Enemy (Distraction)
        enemy = Combatant(filepath=None, data={
            "Name": "TargetDummy", "Species": "Goblin",
            "Stats": {"Might": 10}, "Derived": {"HP": 10}
        })
        enemy.team = "Rebels"
        self.engine.add_combatant(enemy, 5, 8) 
        
        # 4. Run AI Turn
        log = self.engine.execute_ai_turn(caster)
        print("AI Log:", log)
        
        # 5. Verify Heal was cast
        # Check logs for "Cast [Heal]"
        has_healed = any("Cast [Heal]" in l for l in log)
        self.assertTrue(has_healed, "AI should have chosen to Heal ally")
        
    def test_caster_aoe_cluster(self):
        print("\n--- Testing AI: Caster AoE Priority ---")
        caster = Combatant(filepath=None, data={
            "Name": "MageBot", "Species": "Human",
            "Stats": {"Might": 10}, "Derived": {"HP": 20},
            "AI": "Caster",
            "Powers": ["Spore Cloud"] # Tag
        })
        caster.team = "Empire"
        self.engine.add_combatant(caster, 0, 0)
        
        # Create Cluster of Enemies
        for i in range(3):
            e = Combatant(filepath=None, data={"Name": f"Goblin{i}", "Stats": {}, "Derived": {"HP":10}})
            e.team = "Rebels"
            self.engine.add_combatant(e, 5, 5+i) # (5,5), (5,6), (5,7) -> Clustered
            
        # Run AI Turn
        log = self.engine.execute_ai_turn(caster)
        print("AI Log:", log)
        
        # Verify Spore Cloud logic (Pattern "Release spores" in log)
        # Note: The AI Engine calls registry.resolve("Release spores")
        # Registry logs "Spore Cloud released!..."
        # But execute_ai_turn returns a log list. 
        # The AI Engine extends its log with the call log? 
        # Wait, registry.resolve takes a 'ctx' with 'log'. 
        # ai_engine passes `log` list to ctx. So it should be there.
        
        # The registry handle for spore cloud logs: "Spore Cloud released! (Poison AOE)"
        # Or "poisoned by Spore Cloud!"
        
        has_aoe = any("Spore Cloud" in l for l in log)
        self.assertTrue(has_aoe, "AI should have cast Spore Cloud on cluster")

if __name__ == '__main__':
    unittest.main()

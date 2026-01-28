
import unittest
from unittest.mock import MagicMock
import sys
import os

# Adjust path to find engine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from brqse_engine.combat.mechanics import CombatEngine, Combatant

class TestCombatMath(unittest.TestCase):
    def setUp(self):
        self.engine = CombatEngine()
        self.attacker = Combatant(data={"Name": "Attacker", "Stats": {"Might": 10, "Reflexes": 10}, "Skills": {"Sword": 2}})
        self.defender = Combatant(data={"Name": "Defender", "Stats": {"Reflexes": 10}, "Skills": {"Heavy Armor": 1}})
        
        # Inject mock inventory to control "Get Weapon Skill" logic if needed
        # For now, we assume simple property access or mock if mechanics uses helpers
        self.attacker.get_skill_rank = MagicMock(return_value=2) # Skill Rank 2
        self.defender.get_skill_rank = MagicMock(return_value=1) # Skill Rank 1
        
    def test_margins(self):
        # We Mock random.randint to control rolls
        # Execution Order: Damage -> Attacker -> Checker
        # Structure: [Dmg, Atk1, Atk2, Def1, Def2]
        
        # Scenario 1: TIE (Clash)
        # Atk Mod = +2 (Skill 2). Def Mod = 0.
        # Dmg: 5
        # Atk: 10 -> 12.
        # Def: 12 -> 12.
        # Margin: 0 -> Clash
        with unittest.mock.patch('random.randint', side_effect=[5, 10, 10, 12, 12]):
            log = self.engine.attack_target(self.attacker, self.defender)
            if not self.engine.clash_active:
                # Debug output if fails
                pass 
            self.assertTrue(self.engine.clash_active)
            self.assertIn("CLASH TRIGGERED", str(log))

    def test_graze(self):
        # Scenario: Graze (+1 to +4 Margin)
        # Atk Mod = +2. Def Mod = 0.
        # Dmg: 5
        # Atk: 12 -> 14.
        # Def: 10 -> 10.
        # Margin: 4 -> Graze
        self.defender.cmp = 10
        with unittest.mock.patch('random.randint', side_effect=[5, 12, 1, 10, 1]):
            log = self.engine.attack_target(self.attacker, self.defender)
            self.assertTrue("GRAZE" in str(log))
            self.assertEqual(self.defender.cmp, 8) # 10 - 2

    def test_crit(self):
        # Scenario: Crit (+11 Margin)
        # Atk Mod = +2 (Base) + 2 (Might 14) = +4. Def Mod = 0.
        # Dmg: 5
        # Atk: 20 -> 24.
        # Def: 13 -> 13.
        # Margin: 11 -> Crit
        self.attacker.stats["Might"] = 14 # Mod +2
        self.defender.stats["Reflexes"] = 10 # Mod +0
        
        with unittest.mock.patch('random.randint', side_effect=[5, 20, 1, 13, 1]): 
             with unittest.mock.patch('random.choice', return_value="Broken Arm"):
                 log = self.engine.attack_target(self.attacker, self.defender)
                 self.assertTrue("CRITICAL HIT" in str(log))
                 self.assertTrue("Broken Arm" in str(log))

    def test_whiff(self):
        # Scenario: Whiff (-6 to -10 Margin)
        # Atk Mod = +2. Def Mod = 0.
        # Dmg: 5
        # Atk: 4 -> 6.
        # Def: 12 -> 12.
        # Margin: -6 -> Whiff
        with unittest.mock.patch('random.randint', side_effect=[5, 4, 1, 12, 1]):
            log = self.engine.attack_target(self.attacker, self.defender)
            self.assertTrue("WHIFF" in str(log))
            self.assertTrue(self.attacker.is_staggered)

    def test_tactics_flanking(self):
        # Verify Flanking (Rear Attack) gives Advantage
        # Advantage = Roll 2 dice, take highest.
        # Mock: [Dmg=5, Die1=2, Die2=18, Def=10, Def2=10]
        # Without Adv: Roll is 2. With Adv: Roll is 18.
        # We Mock 'is_behind' to True.
        
        self.engine.is_behind = MagicMock(return_value=True)
        
        # Atk Mod +2. Def Mod 0.
        # Roll: max(2, 18) = 18 + 2 = 20.
        # Def: 10 + 0 = 10.
        # Hit Score 20 vs 10. Margin 10 -> HIT.
        # If Logic works, result is HIT. If fails (uses 2), result is WHIFF (4 vs 10).
        
        with unittest.mock.patch('random.randint', side_effect=[5, 2, 18, 10, 10]):
            log = self.engine.attack_target(self.attacker, self.defender)
            self.assertTrue("Rear Attack" in str(log))
            self.assertTrue("HIT" in str(log))
            self.assertFalse("WHIFF" in str(log))

    def test_stat_math(self):
        # Verify Stat Mod formula: (Score - 10) // 2
        self.attacker.stats["Might"] = 12
        self.assertEqual(self.attacker.get_stat_modifier("Might"), 1)
        self.attacker.stats["Might"] = 14
        self.assertEqual(self.attacker.get_stat_modifier("Might"), 2)
        self.attacker.stats["Might"] = 9
        self.assertEqual(self.attacker.get_stat_modifier("Might"), -1)

if __name__ == '__main__':
    unittest.main()

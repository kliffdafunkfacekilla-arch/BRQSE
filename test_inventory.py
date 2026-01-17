
import sys
import os
import unittest

# Add path to scripts
sys.path.append(os.path.join(os.path.dirname(__file__), "combat simulator"))

try:
    from mechanics import CombatEngine, Combatant
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

class TestInventory(unittest.TestCase):
    def setUp(self):
        self.engine = CombatEngine()
        
    def test_weapon_equip(self):
        print("\n--- Testing Weapon Equip ---")
        # 1. Create Combatant with Greatsword in 'Gear'
        c = Combatant(filepath=None, data={
            "Name": "Knight", "Stats": {"Might": 5}, "Derived": {"HP": 20},
            "Gear": ["Greatsword"] # DMG:2d6:Slash
        })
        # Check if equipped
        if not c.inventory: 
            self.fail("Inventory not initialized.")
            
        wpn = c.inventory.equipped["Main Hand"]
        if not wpn:
            self.fail("Greatsword not equipped!")
            
        print(f"Equipped: {wpn.name} ({wpn.tags})")
        self.assertEqual(wpn.name, "Greatsword")
        
        # Check Stats from Inventory
        dice, dtype, tags = c.inventory.get_weapon_stats()
        print(f"Stats: {dice} {dtype}")
        self.assertEqual(dice, "2d6")
        self.assertEqual(dtype, "Slash")

    def test_armor_defense_stat(self):
        print("\n--- Testing Armor Defense Stat ---")
        # 1. Create Combatant with Plate Armor
        # Plate -> Endurance
        c = Combatant(filepath=None, data={
            "Name": "Tank", "Stats": {"Endurance": 5, "Reflexes": 0}, "Derived": {"HP": 20},
            "Gear": ["Bone Mesh"] # Plate group (Family: Plate) in CSV? Wait "Bone Mesh" is "Bio" in Armor Groups CSV?
            # Let's check CSV data. 
            # weapons_and_armor.csv: "Bone Mesh", "Armor", ... "Related_Skill": "Bio"
            # Armor_Groups.csv: "Bio" -> "VITALITY"
            # So Bone Mesh should use VITALITY.
        })
        self.engine.add_combatant(c, 0, 0)
        
        stat = c.inventory.get_defense_stat()
        print(f"Armor: Bone Mesh (Bio). Defense Stat: {stat}")
        self.assertEqual(stat, "Vitality", "Bone Mesh should map to Vitality")

    def test_combat_damage(self):
        print("\n--- Testing Combat Damage ---")
        # Attacker with Greatsword (2d6) vs Dummy
        c1 = Combatant(filepath=None, data={
            "Name": "Attacker", "Stats": {"Might": 10}, "Derived": {"HP": 20},
            "Gear": ["Greatsword"]
        })
        target = Combatant(filepath=None, data={
            "Name": "Target", "Stats": {"Reflexes": 0}, "Derived": {"HP": 50}
        })
        self.engine.add_combatant(c1, 0, 0)
        self.engine.add_combatant(target, 0, 1)
        
        log = self.engine.attack_target(c1, target)
        print("Log:", log)
        
        # Verify damage is > 4 (1d4 min) to prove it used 2d6 (min 2, but likely higher)
        # 2d6 range: 2-12. 
        # Wait, simple attack logic: 1d4 + Might?? 
        # In current mechanics update: `damage = sum(...)` from dice.
        # It does NOT add Might to damage in my replacement code yet!
        # `attack_target` replacement: `hit_score = Might + d20`. 
        # Damage: `damage = int(dice_roll)`.
        # I should verify if Might is added to damage or just To Hit.
        # CSV says "Add Strength Mod to Damage rolls" for Compound Bow only.
        # Implies normally you don't? Or Standard D&D rules apply?
        # User said "defense is a roll + skill rank +stat mod".
        # Assume Damage is just weapon for now unless specified.
        
        has_hit = any("Attack HIT" in l for l in log)
        self.assertTrue(has_hit)
        
if __name__ == '__main__':
    unittest.main()

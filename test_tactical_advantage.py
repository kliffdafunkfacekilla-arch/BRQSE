
import sys
import os
import random

# Mocking necessary components
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from brqse_engine.combat.combat_engine import CombatEngine
from brqse_engine.combat.combatant import Combatant

class MockItem:
    def __init__(self, name, family):
        self.name = name
        self.family = family

class MockInventory:
    def __init__(self, weapon_family="Simple", armor_family="Light"):
        self.equipped = {
            "Main Hand": MockItem("Test Weapon", weapon_family),
            "Armor": MockItem("Test Armor", armor_family)
        }

class MockCharacter:
    def __init__(self, name, weapon_family="Simple", armor_type="Light"):
        self.name = name
        self.species = "Human"
        self.sprite = "human_p"
        self.current_hp = 30
        self.max_hp = 30
        self.base_movement = 30
        self.armor_type = armor_type # Explicit for Combatant.get_defense_info
        self.inventory = MockInventory(weapon_family, armor_type)
        self.stats = {
            "Might": 14,
            "Reflexes": 16,
            "Endurance": 18,
            "Willpower": 12,
            "Knowledge": 10,
            "Vitality": 14,
            "Intuition": 10
        }
        self.skills = {
            "Light": 2,
            "Heavy": 3,
            "Medium": 1,
            "Great": 4,
            "Small": 2,
            "Simple": 1
        }
    def get_stat(self, stat_name):
        return self.stats.get(stat_name, 10)

def test_combat_symmetry():
    engine = CombatEngine(20, 20)
    
    # 1. Setup Attacker - Great Weapon
    char_atk = MockCharacter("Great Attacker", weapon_family="Great")
    p1 = Combatant(char_atk)
    p1.x, p1.y = 5, 5
    p1.team = "Player"
    
    # 2. Setup Defender - Heavy Armor
    char_def_heavy = MockCharacter("Heavy Defender", armor_type="Heavy")
    p2 = Combatant(char_def_heavy)
    p2.x, p2.y = 5, 6
    p2.team = "Enemy"
    
    engine.add_combatant(p1)
    engine.add_combatant(p2)
    
    print("--- Testing Combat Symmetry (Great Atk vs Heavy Def) ---")
    # Attacker: Might (14 -> Mod 2) + Great Skill (4) = +6 bonus
    # Defender: Endurance (18 -> Mod 4) + Heavy Skill (3) = +7 bonus
    engine.execute_attack(p1, p2, stat="Might")
    
    print("\n--- Log Output ---")
    for event in engine.events:
        if event["type"] == "info":
            print(f"LOG: {event['description']}")
        elif event["type"] == "attack":
            print(f"ATTACK: {event['actor']} -> {event['target']} | Result: {event['result']}")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    test_combat_symmetry()

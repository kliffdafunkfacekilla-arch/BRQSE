"""Test script for Injury/Death Mechanics (Phase K)"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brqse_engine.models.character import Character
from brqse_engine.combat.combatant import Combatant
from brqse_engine.combat.combat_engine import CombatEngine

def main():
    print("=== TEST: Injury System ===")
    
    # 1. Setup Character with stats
    char_data = {
        "Name": "Wounded Warrior",
        "Stats": {
            "Might": 12,
            "Vitality": 14,
            "Reflexes": 10,
            "Willpower": 10,
            "Logic": 10,
            "Awareness": 10
        }
    }
    char = Character(char_data)
    
    # Check derived stats
    print(f"Max Condition: {char.max_condition} (Expected: 12+14+10 = 36)")
    print(f"Max Composure: {char.max_composure} (Expected: 10+10+10 = 30)")
    print(f"Death Clock: {char.death_clock} (Expected: 14 = Vitality)")
    
    assert char.max_condition == 36, "FAIL: Condition calculation wrong"
    assert char.max_composure == 30, "FAIL: Composure calculation wrong"
    assert char.death_clock == 14, "FAIL: Death clock calculation wrong"
    print("PASS: Derived stats correct.")
    
    # 2. Test Bloodied threshold
    char.current_condition = 18  # 50%
    assert char.is_bloodied == True, "FAIL: Should be Bloodied at 50%"
    print("PASS: Bloodied threshold works.")
    
    # 3. Test Critical State
    combatant = Combatant(char, team="Blue")
    combatant.current_hp = 5
    combatant.take_damage(5)  # Should trigger critical
    
    assert combatant.is_dying == True, "FAIL: Should be dying at 0 HP"
    assert combatant.has_condition("Prone"), "FAIL: Should be Prone when Dying"
    assert combatant.has_condition("Dying"), "FAIL: Should have Dying condition"
    print("PASS: Critical state triggers correctly.")
    
    # 4. Test Death Clock
    died = combatant.tick_death_clock(5)
    print(f"Death Clock after tick: {combatant.death_clock}")
    assert combatant.death_clock == 9, "FAIL: Clock should be 14-5=9"
    assert died == False, "FAIL: Should not be dead yet"
    print("PASS: Death clock ticks correctly.")
    
    # 5. Test Trauma Roll
    engine = CombatEngine()
    engine.add_combatant(combatant)
    
    injury = engine.roll_trauma(combatant, "Physical")
    print(f"Rolled Trauma: {injury}")
    assert injury is not None, "FAIL: Should have rolled a trauma"
    assert len(combatant.injuries) > 0, "FAIL: Injury should be added"
    print(f"PASS: Trauma system works. Injury: {combatant.injuries}")
    
    print("\n=== ALL TESTS PASSED ===")

if __name__ == "__main__":
    main()

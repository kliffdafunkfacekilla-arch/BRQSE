"""Comprehensive Integration Test for All Data Files"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brqse_engine.abilities.data_loader import DataLoader
from brqse_engine.models.character import Character
from brqse_engine.combat.combatant import Combatant
from brqse_engine.combat.combat_engine import CombatEngine

def test_dataloader():
    """Test all DataLoader tables are populated."""
    print("=== DataLoader Tests ===")
    dl = DataLoader()
    
    tests = [
        ("Talents", len(dl.talents) > 0),
        ("Schools", len(dl.schools) > 0),
        ("Skills", len(dl.skills) > 0),
        ("Power Tiers", len(dl.power_tiers) > 0),
        ("Power Shapes", len(dl.power_shapes) > 0),
        ("Weapon Mastery", len(dl.weapon_mastery) > 0),
        ("Armor Mastery", len(dl.armor_mastery) > 0),
        ("Tool Mastery", len(dl.tool_mastery) > 0),
        ("Universal Traits", len(dl.universal_traits) > 0),
        ("General Skill Unlocks", len(dl.general_skill_unlocks) > 0),
        ("Generic Species Traits", len(dl.generic_species_traits) > 0),
    ]
    
    for name, passed in tests:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
    
    return all(t[1] for t in tests)

def test_mastery_combat():
    """Test mastery effects apply in combat."""
    print("\n=== Mastery Combat Tests ===")
    
    # Create a Master-tier character with Great skill (has Advantage effects)
    attacker_data = {
        "Name": "Master Fighter",
        "Skill_Ranks": {"Great": 9},  # Master tier - Great has Executioner (Advantage on Prone)
        "Stats": {"Might": 14, "Vitality": 12, "Reflexes": 10},
        "Skills": ["Great Weapons"]
    }
    
    # Create a bloodied + prone target
    target_data = {
        "Name": "Wounded Enemy",
        "Stats": {"Might": 10, "Vitality": 10, "Reflexes": 10}
    }
    
    attacker = Combatant(Character(attacker_data))
    target = Combatant(Character(target_data))
    
    # Set positions
    attacker.x, attacker.y, attacker.team = 5, 5, "blue"
    target.x, target.y, target.team = 6, 5, "red"
    
    # Make target bloodied AND prone
    target.character.current_condition = target.character.max_condition // 4
    target.add_condition("Prone")  # Needed for Executioner mastery
    
    # Equip a Great weapon so mastery applies
    from brqse_engine.models.item import Item
    great_sword = Item({"Name": "Greatsword", "Type": "Weapon", "Skill": "Great", "Damage": "2d6"})
    great_sword.is_equipped = True
    attacker.character.inventory.append(great_sword)
    
    engine = CombatEngine(20, 20)
    engine.add_combatant(attacker)
    engine.add_combatant(target)
    
    # Test modifiers
    adv, dis, logs = engine._get_attack_modifiers(attacker, target, False)
    
    tests = [
        ("Target is bloodied", target.is_bloodied),
        ("Target is prone", target.has_condition("Prone")),
        ("Mastery lookup works", len(attacker.character.get_active_mastery_unlocks("Great")) == 3),
        ("Mastery grants advantage", adv == True and any("Executioner" in l or "Prone" in l for l in logs)),
    ]
    
    for name, passed in tests:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
    
    print(f"  Logs: {logs}")
    return all(t[1] for t in tests)

def test_progression():
    """Test progression system."""
    print("\n=== Progression Tests ===")
    
    char = Character({
        "Name": "Leveling Hero",
        "Level": 10,
        "Stats": {"Might": 12, "Vitality": 12, "Reflexes": 12, "Willpower": 10, "Logic": 10, "Awareness": 10}
    })
    
    tests = [
        ("Level set", char.level == 10),
        ("Tier calculated", char.tier in ["Veteran", "Elite", "Master"]),
        ("Max Stamina > 0", char.max_stamina > 0),
        ("Max Focus > 0", char.max_focus > 0),
        ("Magic Tier > 0", char.max_magic_tier > 0),
    ]
    
    for name, passed in tests:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
    
    print(f"  Level {char.level} | Tier: {char.tier} | Magic Tier: {char.max_magic_tier}")
    return all(t[1] for t in tests)

def test_injury_system():
    """Test injury and death mechanics."""
    print("\n=== Injury System Tests ===")
    
    char = Character({
        "Name": "Test Subject",
        "Stats": {"Might": 12, "Vitality": 12, "Reflexes": 12, "Willpower": 10, "Logic": 10, "Awareness": 10}
    })
    
    tests = [
        ("Max Condition > 0", char.max_condition > 0),
        ("Max Composure > 0", char.max_composure > 0),
        ("Death Clock = Vitality", char.death_clock == char.stats.get("Vitality", 10)),
        ("Not dying initially", char.is_dying == False),
    ]
    
    for name, passed in tests:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
    
    return all(t[1] for t in tests)

def test_trauma_loading():
    """Test trauma table loading."""
    print("\n=== Trauma System Tests ===")
    
    engine = CombatEngine(20, 20)
    
    tests = [
        ("Trauma table loaded", len(engine.traumas.get("Physical", [])) > 0 or len(engine.traumas.get("Mental", [])) > 0),
        ("Has physical traumas", len(engine.traumas.get("Physical", [])) > 0),
        ("Has mental traumas", len(engine.traumas.get("Mental", [])) > 0),
    ]
    
    for name, passed in tests:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
    
    return all(t[1] for t in tests)

def main():
    print("=" * 50)
    print("COMPREHENSIVE DATA FILE INTEGRATION TEST")
    print("=" * 50)
    
    results = [
        test_dataloader(),
        test_mastery_combat(),
        test_progression(),
        test_injury_system(),
        test_trauma_loading(),
    ]
    
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"RESULTS: {passed}/{total} test suites passed")
    
    if all(results):
        print("ALL DATA FILES PROPERLY INTEGRATED!")
    else:
        print("Some tests failed - review output above.")

if __name__ == "__main__":
    main()

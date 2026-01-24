"""Test script for Progression System"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brqse_engine.models.character import Character

def main():
    print("=== TEST: Progression System ===")
    
    # 1. Test Level 1 Character
    char_data = {
        "Name": "Newbie",
        "Level": 1,
        "Stats": {
            "Endurance": 12, "Finesse": 10, "Fortitude": 10,  # Stamina base
            "Knowledge": 10, "Charm": 12, "Intuition": 10    # Focus base
        }
    }
    char = Character(char_data)
    
    print(f"Level: {char.level}")
    print(f"Tier: {char.tier}")
    print(f"Max Stamina: {char.max_stamina} (Expected: 32 base + 0 bonus = 32)")
    print(f"Max Focus: {char.max_focus} (Expected: 32 base + 0 bonus = 32)")
    print(f"Max Magic Tier: {char.max_magic_tier} (Expected: 1)")
    
    assert char.level == 1, "FAIL: Level should be 1"
    assert char.tier == "Novice", "FAIL: Tier should be Novice"
    assert char.max_magic_tier == 1, "FAIL: Magic tier should be 1"
    print("PASS: Level 1 stats correct.\n")
    
    # 2. Test Level 10 Character
    char10_data = {
        "Name": "Master",
        "Level": 10,
        "Stats": {"Endurance": 12, "Finesse": 10, "Fortitude": 10, "Knowledge": 10, "Charm": 12, "Intuition": 10}
    }
    char10 = Character(char10_data)
    
    print(f"Level 10 Tier: {char10.tier}")
    print(f"Level 10 Max Stamina: {char10.max_stamina}")
    print(f"Level 10 Max Focus: {char10.max_focus}")
    print(f"Level 10 Magic Tier: {char10.max_magic_tier}")
    
    assert char10.tier == "Master", f"FAIL: Tier should be Master, got {char10.tier}"
    assert char10.max_magic_tier == 5, f"FAIL: Magic tier should be 5, got {char10.max_magic_tier}"
    # Stamina: 32 base + (2+2+4+4+10) = 32 + 22 = 54
    # Focus: 32 base + (2+2+4+4+10) = 32 + 22 = 54
    print("PASS: Level 10 stats correct.\n")
    
    # 3. Test XP Gain and Level Up
    char.xp = 0
    leveled = char.gain_xp(350)  # Should level up to 2 (need 300)
    
    print(f"After 350 XP: Level {char.level}, XP {char.xp}")
    assert char.level == 2, f"FAIL: Should be level 2, got {char.level}"
    assert leveled == True, "FAIL: Should have leveled up"
    print("PASS: Level up works.\n")
    
    # 4. Test Level 20 Character (God Tier)
    char20_data = {"Name": "God", "Level": 20, "Stats": {}}
    char20 = Character(char20_data)
    
    print(f"Level 20 Tier: {char20.tier}")
    print(f"Level 20 Magic Tier: {char20.max_magic_tier}")
    
    assert char20.tier == "God", f"FAIL: Tier should be God"
    assert char20.max_magic_tier == 10, f"FAIL: Magic tier should be 10"
    print("PASS: Level 20 stats correct.\n")
    
    print("=== ALL PROGRESSION TESTS PASSED ===")

if __name__ == "__main__":
    main()

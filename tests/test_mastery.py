"""Test script for Mastery System Integration"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brqse_engine.models.character import Character

def main():
    print("=== TEST: Mastery System ===")
    
    # Test character with high skill rank
    char = Character({
        "Name": "Master Swordsman",
        "Skill_Ranks": {"Great": 9},  # Master tier
        "Stats": {"Might": 14, "Vitality": 12, "Reflexes": 10}
    })
    
    print(f"Character: {char.name}")
    print(f"Skill Rank (Great): {char.get_skill_rank('Great')}")
    print(f"Mastery Tier: {char.get_mastery_tier('Great')}")
    
    unlocks = char.get_active_mastery_unlocks("Great")
    print(f"Number of Unlocks: {len(unlocks)}")
    
    for u in unlocks:
        print(f"  - {u.get('name')}: {u.get('effect')}")
    
    # Test tier thresholds
    print("\n--- Tier Thresholds ---")
    for rank in [0, 3, 6, 9, 12]:
        char2 = Character({"Name": "Test", "Skill_Ranks": {"Small": rank}})
        print(f"  Rank {rank}: {char2.get_mastery_tier('Small')}")
    
    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    main()

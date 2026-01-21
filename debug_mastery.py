"""Debug mastery lookup"""
from brqse_engine.models.character import Character

char = Character({
    "Name": "Master Fighter",
    "Skill_Ranks": {"Fist": 9},
    "Stats": {"Might": 14, "Vitality": 12, "Reflexes": 10}
})

print(f"Skill Rank (Fist): {char.get_skill_rank('Fist')}")
print(f"Mastery Tier: {char.get_mastery_tier('Fist')}")
unlocks = char.get_active_mastery_unlocks("Fist")
print(f"Unlocks count: {len(unlocks)}")
for u in unlocks:
    print(f"  - {u}")

# Check weapon
weapon = char.get_equipped_weapon()
print(f"\nWeapon: {weapon}")
print(f"Weapon Skill: {weapon.get('Skill', 'NONE')}")

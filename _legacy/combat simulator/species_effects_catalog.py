"""
Species Skill Effect Analysis
==============================
Extracted unique effect patterns from all 6 species skill CSVs.
These need handlers in effects_registry.py.
"""

CATEGORIZED_EFFECTS = {
    # --- MOVEMENT MODIFIERS ---
    "movement": [
        "melee reach increases by +5 feet",
        "You gain a Swim Speed equal to your Walk Speed",
        "You gain a Climb Speed equal to your Walk Speed", 
        "You gain a Burrow speed of 15ft",
        "Fly speed increases by +10ft",
        "Move through trees/rafters at full speed",
        "You can squeeze through gaps as small as 1 inch",
        "You can walk on vertical surfaces and ceilings",
        "Jump up to 30ft horizontally or 15ft vertically",
        "You cannot be moved against your will",
    ],
    
    # --- ATTACK BONUSES ---
    "attack_bonus": [
        "next attack deals +1d6 damage",  # Gore
        "Attack deals extra Bleed damage",  # Tear Flesh
        "Critical Hit on 19 or 20",  # Spot Weakness
        "attacks ignore Half-Cover and Three-Quarters Cover",  # Focus
        "deal extra damage equal to your Level",  # Ambush
        "Attack ignores Armor Class bonus from shields",  # Pierce Armor
        "deal automatically Bludgeoning damage",  # Crush (grapple)
    ],
    
    # --- DEFENSE / RESISTANCE ---
    "defense": [
        "reduce the damage taken by 1d6 + Might",  # Parry
        "Gain +5 AC",  # Withdraw
        "gain +2 AC",  # Parry/Deflect
        "Resistance to Fire damage",  # Dampen
        "Resistance to Cold damage",  # Insulated
        "Resistance to Acid damage",  # Waxy Shell
        "immune to Critical Hits",  # Bulwark
        "base Armor Class is 13 + Dexterity",  # Heavy Chitin
        "base Armor Class is 14 + Dexterity",  # Hardwood
        "reduce damage from Bludgeoning attack by half",  # Shrug It Off
    ],
    
    # --- STATUS EFFECTS (Applied to Target) ---
    "apply_status": [
        "target Prone",  # knockdown
        "target is Blinded",  # Mud Slinger
        "target is Poisoned",  # Envenom
        "target is Frightened",  # Warning Shake
        "target is Charmed",  # Hypnotic Gaze
        "target is Restrained",  # Entangle
        "target is Paralyzed",  # Neurotoxin
        "target is Stunned",  # Unnerving
        "target is Deafened",  # Bellow
        "target takes Bleed damage",  # Shred
    ],
    
    # --- GRAPPLE EFFECTS ---
    "grapple": [
        "automatically Grappled",  # Snap Trap
        "Advantage on checks to maintain a Grapple",  # Latch
        "Disadvantage on checks to escape your Grapple",  # Lockjaw
        "Grappled target takes damage",  # Gut Rake
        "creatures that Grapple you take damage",  # Barbed/Spike Armor
    ],
    
    # --- AREA OF EFFECT ---
    "aoe": [
        "15ft cone",  # Leaf Storm, Bellow, Quill Shot
        "10ft cone",  # Quill Shot
        "5ft cloud",  # Musk Spray, Spore Cloud
        "30ft radius",  # Regal Roar (buff allies)
        "10ft radius",  # Pheromone Rally
    ],
    
    # --- PASSIVE / SENSORY ---
    "passive": [
        "You can see in Dim Light as if it were Bright Light",  # Night Vision
        "Detect invisible or hidden creatures",  # Sonar, Thermal Sight
        "Detect poison/magic within 60ft",  # Taste the Air
        "Tremorsense within 30ft",  # Antennae
        "You cannot be Flanked",  # Omni-Vision
        "You cannot be Surprised",  # Vigilant
        "Advantage on Stealth checks",  # Various camo
    ],
    
    # --- HEALING / UTILITY ---
    "utility": [
        "regain Hit Points",  # Photosynth, Scavenge
        "restore 1d4 HP",  # Goodberry
        "Temporary HP equal to your Proficiency Bonus",  # Rally
        "remove the Frightened condition",  # Resonance
    ],
}

# Effect patterns that NEED HANDLERS (prioritized)
MISSING_HANDLERS = [
    # High Priority - Common Combat Effects
    ("Bleed", r"Bleed.*?(\d+d?\d*)?", "Apply bleed DoT"),
    ("Prone", r"knocked? Prone|falls? Prone", "Knock target prone"),
    ("Push", r"pushed back (\d+)ft|shove", "Push target away"),
    ("ExtraReach", r"reach increases by.*?(\d+)", "Extend melee reach"),
    ("SwimSpeed", r"Swim Speed equal", "Grant swim speed"),
    ("ClimbSpeed", r"Climb Speed equal", "Grant climb speed"),
    ("BurrowSpeed", r"Burrow speed", "Grant burrow speed"),
    
    # Medium Priority - Status/Combat
    ("GrappleBonus", r"Advantage on.*?Grapple", "Bonus to grapples"),
    ("ReflexAttack", r"When.*?enters.*?attack", "Trigger attack on approach"),
    ("CritRange", r"Critical Hit on.*?19|19-20", "Expand crit range"),
    ("IgnoreCover", r"ignore.*?Cover", "Ignore cover bonuses"),
    ("Intimidate", r"Intimidation check", "Apply fear from skill"),
    ("Disarm", r"Disarm|drop.*?weapon", "Force weapon drop"),
    
    # Lower Priority - Utility
    ("NightVision", r"see in Dim Light", "Passive darkvision"),
    ("Tremorsense", r"Tremorsense|detect.*?moving creature", "Detect by vibration"),
    ("WallWalk", r"walk on.*?walls|ceilings", "Spider climb"),
    ("Camouflage", r"turn Invisible|Stealth.*?Advantage", "Stealth boost"),
]

print("Species Skill Effect Categories:")
for cat, effects in CATEGORIZED_EFFECTS.items():
    print(f"\n{cat.upper()}: {len(effects)} patterns")
    for e in effects[:3]:
        print(f"  - {e[:50]}...")

print(f"\n\nMISSING HANDLERS NEEDED: {len(MISSING_HANDLERS)}")

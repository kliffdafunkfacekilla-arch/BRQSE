import csv
import json
import os

DATA_DIR = r"C:\Users\krazy\Desktop\BRQSE\Data"
OUTPUT_DIR = r"C:\Users\krazy\Desktop\BRQSE\Web_ui\public\data"
TOKENS_DIR = r"C:\Users\krazy\Desktop\BRQSE\Web_ui\public\tokens"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Mappings for consistent IDs
WEAPON_SKILL_MAP = {
    "Large Weapons": "The Breakers",
    "The Ballistics": "The Draw",
    "Small Weapons": "The Blades",
    "The Thrown": "The Thrown",
    "Fist Weapons": "The Fist",
    "The Simple Shot": "The Simple Shot",
    "Medium Weapons": "The Long Blade",
    "The Blast": "The Blast",
    "Reach Weapons": "The Polearms",
    "The Long Shot": "The Long Shot",
    "Exotic Weapons": "Melee Exotics",
    "Ranged Exotics": "Ranged Exotics"
}

ARMOR_SKILL_MAP = {
    "Plate": "Plate",
    "Bio": "Bio",
    "Light ": "Leather",  # Note space in CSV
    "Robes": "Robes",
    "Mail": "Mail",
    "Rigs": "Rigs"
}

def read_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"File not found: {path} - Skipping")
        return []
    
    encodings = ['utf-8-sig', 'utf-8', 'cp1252', 'latin1']
    for enc in encodings:
        try:
            with open(path, 'r', encoding=enc) as f:
                reader = csv.DictReader(f)
                return list(reader)
        except UnicodeDecodeError:
            continue
    print(f"Could not decode {filename}")
    return []

def generate_backgrounds():
    backgrounds = []

    # 1. ORIGIN (Social)
    social_off = read_csv("Social_Off.csv")
    social_def = read_csv("Social_Def.csv")
    
    origin_step = {
        "id": "Origin",
        "title": "Step 8: Origin",
        "description": "Where do you come from? (Choose a Social Skill)",
        "options": []
    }
    
    for row in social_off:
        # Check keys
        skill = row.get("The Weapon") or row.get("Skill Name")
        desc = row.get("Description (The Action)")
        if skill:
            origin_step["options"].append({
                "name": skill,
                "category": "Social Offense",
                "narrative": desc,
                "grants": ["Social Offense", skill]
            })
            
    for row in social_def:
        skill = row.get("The Armor") or row.get("Skill Name")
        desc = row.get("Description (The Reaction)")
        if skill:
            origin_step["options"].append({
                "name": skill,
                "category": "Social Defense",
                "narrative": desc,
                "grants": ["Social Defense", skill]
            })
            
    backgrounds.append(origin_step)

    # 2. CHILDHOOD (Tool/Utility)
    skills = read_csv("Skills.csv")
    childhood_step = {
        "id": "Childhood",
        "title": "Step 9: Childhood",
        "description": "What did you learn growing up? (Choose a Tool or Utility Skill)",
        "options": []
    }
    
    # Filter Skills.csv for Tool/Utility
    # Headers: Attribute, Type, Skill_Name, Description
    for row in skills:
        stype = row.get("Type", "").strip()
        if stype in ["Tool", "Utility"]:
            name = row.get("Skill_Name", "").strip()
            desc = row.get("Description", "").strip()
            childhood_step["options"].append({
                "name": name,
                "category": stype,
                "narrative": desc,
                "grants": [stype, name]
            })
    
    backgrounds.append(childhood_step)

    # 3. COMING OF AGE (Melee Weapons)
    weps = read_csv("Weapon_Groups.csv")
    age_step = {
        "id": "Coming of Age",
        "title": "Step 10: Coming of Age",
        "description": "You learned to fight. (Choose a Melee Weapon Skill)",
        "options": []
    }
    
    # 5. CATALYST (Ranged Weapons)
    cat_step = {
        "id": "Catalyst",
        "title": "Step 12: Catalyst",
        "description": "Something changed you. (Choose a Ranged Weapon Skill)",
        "options": []
    }

    for row in weps:
        # Family Name, Type, ...
        fam = row.get("Family Name", "").strip()
        wtype = row.get("Type", "").strip() # Melee or Ranged
        
        # Map to Canonical Name
        canonical = WEAPON_SKILL_MAP.get(fam, fam)
        
        desc = row.get("Trait", "") + ". " + row.get("Why this Stat?", "")
        
        opt = {
            "name": canonical,
            "category": "Weapon Skill",
            "narrative": desc,
            "grants": ["Weapon Skill", canonical]
        }
        
        if wtype == "Melee":
            age_step["options"].append(opt)
        elif wtype == "Ranged":
            cat_step["options"].append(opt)
            
    backgrounds.append(age_step)

    # 4. TRAINING (Armor)
    # Insert Training before Catalyst
    armor = read_csv("Armor_Groups.csv")
    train_step = {
        "id": "Training",
        "title": "Step 11: Training",
        "description": "You learned to survive. (Choose an Armor Skill)",
        "options": []
    }
    
    for row in armor:
        fam = row.get("Family Name", "").strip()
        canonical = ARMOR_SKILL_MAP.get(fam, fam)
        desc = row.get("Trait", "") + ". " + row.get("Why this Stat?", "")
        
        train_step["options"].append({
            "name": canonical,
            "category": "Armor Skill",
            "narrative": desc,
            "grants": ["Armor Skill", canonical]
        })
        
    backgrounds.append(train_step)
    backgrounds.append(cat_step) # Catalyst is last

    with open(os.path.join(OUTPUT_DIR, "Backgrounds.json"), 'w') as f:
        json.dump(backgrounds, f, indent=2)
    print("Generated Backgrounds.json")

def generate_spells():
    raw = read_csv("Schools of Power.csv")
    spells = []
    
    for row in raw:
        try:
            tier = int(row.get("Tier", "99"))
        except:
            tier = 99
            
        if tier == 1:
            spells.append(row)
            
    with open(os.path.join(OUTPUT_DIR, "Spells.json"), 'w') as f:
        json.dump(spells, f, indent=2)
    print(f"Generated Spells.json ({len(spells)} spells)")

def generate_gear():
    # Load Weapons and Armor
    raw = read_csv("weapons_and_armor.csv")
    gear = []
    
    for row in raw:
        # Clean up keys if needed
        # Just pass through mostly, ensuring Related_Skill is clean
        rel = row.get("Related_Skill", "").strip()
        if rel:
            row["Related_Skill"] = rel
            gear.append(row)
            
    with open(os.path.join(OUTPUT_DIR, "Gear.json"), 'w') as f:
        json.dump(gear, f, indent=2)
    print(f"Generated Gear.json ({len(gear)} items)")

def generate_tokens():
    tokens = []
    if os.path.exists(TOKENS_DIR):
        for f in os.listdir(TOKENS_DIR):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                tokens.append(f)
    
    with open(os.path.join(OUTPUT_DIR, "Tokens.json"), 'w') as f:
        json.dump(tokens, f, indent=2)
    print(f"Generated Tokens.json ({len(tokens)} images)")

if __name__ == "__main__":
    generate_backgrounds()
    generate_spells()
    generate_gear()
    generate_tokens()

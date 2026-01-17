import os
import sys
import random
import json

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../Data")
TEMP_DIR = os.path.join(BASE_DIR, "../Saves/temp")

# Ensure temp dir
if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)

# --- DATA LOADER (Simplified from charcreate.py) ---
def load_csv(path):
    import csv
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return list(csv.DictReader(f))
    except: return []

class EnemySpawner:
    def __init__(self):
        self.species_stats = {}
        self.evolutions = {}
        self.skills = []
        self.talents = []
        self.tool_types = []
        self.weapon_groups = []
        self.load_data()
        
    def load_data(self):
        # Species Base Stats
        for sp in ["Mammal", "Avian", "Reptile", "Aquatic", "Insect", "Plant"]:
            rows = load_csv(os.path.join(DATA_DIR, f"{sp}.csv"))
            if rows:
                # First row is base stats usually for the species.
                self.species_stats[sp] = rows[0] if rows else {}
                # Evolution rows
                self.evolutions[sp] = rows
                
        # Skills
        self.skills = load_csv(os.path.join(DATA_DIR, "Skills.csv"))
        
        # Talents
        self.talents = load_csv(os.path.join(DATA_DIR, "Talents.csv"))
        
        # Tool Types
        self.tool_types = load_csv(os.path.join(DATA_DIR, "Tool_types.csv"))
        
        # Weapon Groups
        self.weapon_groups = load_csv(os.path.join(DATA_DIR, "Weapon_Groups.csv"))

    def generate(self, ai_template="Aggressive"):
        """
        Generate a random enemy combatant and save to temp JSON.
        Returns the path to the generated file.
        """
        name = f"Enemy_{random.randint(100, 999)}"
        
        # 1. Species
        species_list = list(self.species_stats.keys())
        if not species_list: species_list = ["Mammal"]
        species = random.choice(species_list)
        
        # Base Stats (from evolution rows)
        stats = {"Might": 10, "Reflexes": 10, "Vitality": 10, "Knowledge": 5, "Willpower": 5}
        base_row = self.species_stats.get(species, {})
        for k in stats:
            if k in base_row:
                try: stats[k] = int(base_row[k])
                except: pass
        
        # 2. Derive
        hp = 10 + stats.get("Vitality", 0) * 2
        speed = 20 + stats.get("Reflexes", 0)
        sp = 10
        fp = 10
        cmp = 10
        
        # 3. Traits (pick 1-2 from Talents)
        traits = []
        if self.talents:
            picks = random.sample(self.talents, min(2, len(self.talents)))
            traits = [p.get("Talent_Name") for p in picks if p.get("Talent_Name")]
        
        # 4. Inventory (random weapon)
        inventory = []
        if self.weapon_groups:
            wpn = random.choice(self.weapon_groups).get("Family Name", "Sword")
            inventory.append(wpn)
        
        # 5. AI Template
        # This is a simple string stored in the data; the Engine will interpret it.
        ai = ai_template
        
        # Build Data
        data = {
            "Name": name,
            "Species": species,
            "Stats": stats,
            "Derived": {"HP": hp, "Speed": speed, "SP": sp, "FP": fp, "CMP": cmp},
            "Traits": traits,
            "Powers": [],
            "Skills": ["Guard"],
            "Inventory": inventory,
            "AI": ai
        }
        
        # Save
        filepath = os.path.join(TEMP_DIR, f"{name}.json")
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
            
        return filepath

# Singleton
spawner = EnemySpawner()

# --- AI TEMPLATES DEFINITIONS ---
AI_TEMPLATES = {
    "Aggressive": "Charge and attack every turn.",
    "Defensive": "Defend until attacked, then retaliate.",
    "Ranged": "Stay at max distance and use ranged attacks.",
    "Support": "Buff allies, avoid direct combat.",
    "Berserker": "Attack randomly, ignoring tactics.",
}

def get_ai_templates():
    return list(AI_TEMPLATES.keys())

if __name__ == "__main__":
    print("Generating test enemy...")
    path = spawner.generate("Aggressive")
    print(f"Saved to: {path}")

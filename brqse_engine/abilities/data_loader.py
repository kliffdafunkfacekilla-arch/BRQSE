import csv
import os

class DataLoader:
    def __init__(self, data_dir=None):
        if data_dir:
            self.data_dir = data_dir
        else:
            # Default to ../../Data relative to this file (brqse_engine/abilities/data_loader.py)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.data_dir = os.path.join(base_dir, "../../Data")
        
        self.talents = []
        self.schools = []
        self.skills = []
        self.species_skills = {}
        self.power_tiers = {}  # Tier -> {Damage_Dice, Healing_Dice, Resource_Cost, etc.}
        self.power_shapes = {}  # Tier -> {Shape_Name, Range_Area, Cost_Modifier}
        
        self.reload_all()

    def _load_csv(self, filename):
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path):
            print(f"[DataLoader] Warning: File not found {path}")
            return []
        
        data = []
        encodings = ['utf-8-sig', 'cp1252', 'latin-1']
        for encoding in encodings:
            try:
                with open(path, 'r', encoding=encoding) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Clean keys/values
                        clean_row = {k.strip(): v.strip() for k, v in row.items() if k}
                        data.append(clean_row)
                break # Success
            except UnicodeDecodeError:
                continue # Try next encoding
            except Exception as e:
                print(f"[DataLoader] Error loading {filename} with {encoding}: {e}")
                break
            
        return data

    def reload_all(self):
        self.talents = self._load_csv("Talents.csv")
        self.schools = self._load_csv("Schools of Power.csv")
        self.skills = self._load_csv("Skills.csv")
        
        # Load Species Skills
        species_list = ["Aquatic", "Avian", "Insect", "Mammal", "Plant", "Reptile"]
        for sp in species_list:
            self.species_skills[sp] = self._load_csv(f"{sp}_Skills.csv")
        
        # Load Power Tiers (damage/cost scaling)
        power_data = self._load_csv("Power_Power.csv")
        for row in power_data:
            try:
                tier = int(row.get("Tier", 0))
                self.power_tiers[tier] = {
                    "damage_dice": row.get("Damage_Dice", "1d6"),
                    "healing_dice": row.get("Healing_Dice", "1d6"),
                    "resource_cost": int(row.get("Resource_Cost", tier)),
                    "duration": row.get("Duration", "1 Round"),
                    "force": row.get("Force_Magnitude", "5 ft")
                }
            except:
                pass
        
        # Load Power Shapes (range/targeting)
        shape_data = self._load_csv("Power_Shapes.csv")
        for row in shape_data:
            try:
                tier = int(row.get("Tier", 0))
                self.power_shapes[tier] = {
                    "name": row.get("Shape_Name", "Touch"),
                    "range": row.get("Range_Area", "Melee / Self"),
                    "cost_mod": int(row.get("Cost_Modifier", 0))
                }
            except:
                pass

    def get_tier_damage(self, tier):
        """Get damage dice for a given tier. Returns dice string like '2d6'."""
        if tier in self.power_tiers:
            return self.power_tiers[tier]["damage_dice"]
        # Default fallback
        return f"{max(1, tier // 2)}d6"
    
    def get_tier_cost(self, tier):
        """Get resource cost for a given tier."""
        if tier in self.power_tiers:
            return self.power_tiers[tier]["resource_cost"]
        return tier
    
    def get_shape_range(self, tier):
        """Get shape range for a given tier."""
        if tier in self.power_shapes:
            return self.power_shapes[tier]["range"]
        return "Melee / Self"

    def get_all_effects(self):
        """Returns a list of all unique effect descriptions/strings found in the data."""
        effects = set()
        
        for t in self.talents:
            if "Effect" in t: effects.add(f"Talent: {t.get('Talent_Name')} -> {t['Effect']}")
            if "Effect_Logic" in t: effects.add(f"Talent_Logic: {t.get('Talent_Name')} -> {t['Effect_Logic']}")

        for s in self.schools:
            if "Description" in s: effects.add(f"School: {s.get('School')} -> {s['Description']}")

        for s in self.skills:
            if "Description" in s: effects.add(f"Skill: {s.get('Skill Name')} -> {s['Description']}")

        for sp, skill_list in self.species_skills.items():
            for s in skill_list:
                desc = s.get("Effect Description") or s.get("Effect")
                name = s.get("Skill Name") or s.get("Skill")
                if desc: effects.add(f"Species_{sp}: {name} -> {desc}")
                
        return sorted(list(effects))

if __name__ == "__main__":
    dl = DataLoader()
    print(f"Loaded {len(dl.talents)} Talents")
    print(f"Loaded {len(dl.schools)} Schools")
    print(f"Loaded {len(dl.skills)} Skills")
    print(f"Loaded {len(dl.power_tiers)} Power Tiers")
    print(f"Loaded {len(dl.power_shapes)} Power Shapes")
    
    print("\n--- Power Tier Scaling ---")
    for tier in range(1, 6):
        print(f"Tier {tier}: {dl.get_tier_damage(tier)} damage, {dl.get_tier_cost(tier)} cost")

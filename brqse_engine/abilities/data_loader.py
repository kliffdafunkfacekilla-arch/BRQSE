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
        
        # Mastery Tables (Skill Name -> {Tier -> Unlock})
        self.weapon_mastery = {}
        self.armor_mastery = {}
        self.tool_mastery = {}
        
        # Traits Tables
        self.universal_traits = []  # List of {Tier, Skill_Name, Effect}
        self.general_skill_unlocks = {}  # Category -> [Rank -> Unlock]
        self.generic_species_traits = {}  # Species -> [Tier -> Trait]
        
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
                        # Clean keys/values and normalize spaces to underscores
                        clean_row = {k.strip().replace(" ", "_"): v.strip() for k, v in row.items() if k}
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
        
        # Load Mastery Tables
        self._load_mastery("Weapon_Mastery.csv", self.weapon_mastery)
        self._load_mastery("Armor_Mastery.csv", self.armor_mastery)
        self._load_mastery("Tool_Mastery.csv", self.tool_mastery)
        
        # Load Universal Traits
        self.universal_traits = self._load_csv("Universal_Traits.csv")
        
        # Load General Skill Unlocks (Category -> Rank -> Unlock)
        for row in self._load_csv("General_Skill_Unlocks.csv"):
            cat = row.get("Category", "")
            rank = row.get("Rank", "")
            if cat not in self.general_skill_unlocks:
                self.general_skill_unlocks[cat] = {}
            self.general_skill_unlocks[cat][rank] = {
                "name": row.get("Name", ""),
                "effect": row.get("Effect", "")
            }
        
        # Load Generic Species Traits (Species -> Tier -> Trait)
        for row in self._load_csv("Generic_Species_Traits.csv"):
            species = row.get("Species", "")
            tier = row.get("Tier", "1")
            if species not in self.generic_species_traits:
                self.generic_species_traits[species] = {}
            self.generic_species_traits[species][tier] = {
                "name": row.get("Skill_Name", ""),
                "effect": row.get("Effect", "")
            }

    def _load_mastery(self, filename, target_dict):
        """Load a mastery CSV into skill_name -> tier -> unlock dict."""
        for row in self._load_csv(filename):
            skill = row.get("Skill_Name", "")
            tier = row.get("Tier", "Novice")
            if skill not in target_dict:
                target_dict[skill] = {}
            target_dict[skill][tier] = {
                "name": row.get("Unlock_Name", ""),
                "effect": row.get("Effect", ""),
                "attribute": row.get("Attribute", "")
            }

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
            if "Description" in s: effects.add(f"Skill: {s.get('Skill_Name')} -> {s['Description']}")

        for sp, skill_list in self.species_skills.items():
            for s in skill_list:
                desc = s.get("Effect Description") or s.get("Effect")
                name = s.get("Skill_Name") or s.get("Skill")
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

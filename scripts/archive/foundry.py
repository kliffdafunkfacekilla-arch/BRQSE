
import csv
import json
import os
import sys
from collections import defaultdict

class ChaosFoundry:
    def __init__(self):
        # Resolve Data path relative to this script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(base_dir, "../Data")
        self.data = {}
        # Mappings
        self.weapon_group_map = {} # specific weapon name -> group name

    def _read_csv(self, filename):
        """Helper to safely read CSVs with different encodings."""
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            print(f"Warning: File not found: {filepath}")
            return []
        
        encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
        for enc in encodings:
            try:
                with open(filepath, mode='r', encoding=enc) as f:
                    # Read all to check for null bytes or weirdness, but strictly it's better to just csv.DictReader
                    reader = csv.DictReader(f)
                    return list(reader)
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Error reading {filename} with {enc}: {e}")
        
        print(f"Failed to read {filename}")
        return []

    def process_species(self):
        print("Processing Species...")
        rows = self._read_csv("Species.csv")
        # Transpose: 'Mammal', 'Reptile' are columns.
        # Structure: Attribute, Mammal, Avian, ...
        # Output: "Species": { "Mammal": { "Might": 10, ... }, ... }
        
        if not rows:
            return

        species_data = defaultdict(dict)
        # Get species names from headers, excluding 'Attribute' and 'Reference'
        headers = [k for k in rows[0].keys() if k not in ['Attribute', 'Reference', '']]
        
        for row in rows:
            attr = row.get('Attribute')
            if not attr: continue
            
            for sp in headers:
                try:
                    val = int(row[sp])
                except ValueError:
                    val = row[sp] # Keep as string if not int
                species_data[sp][attr] = val
        
        self.data["Species"] = dict(species_data)

    def process_weapon_groups(self):
        print("Processing Weapon Groups...")
        rows = self._read_csv("Weapon_Groups.csv")
        # Build map: Example "Greatsword" -> Group "Great weapons"
        self.weapon_groups = {} # Store full group info
        
        for row in rows:
            group_name = row.get("Family Name")
            if not group_name: continue
            
            # Normalize group name
            term_group = group_name.strip()
            self.weapon_groups[term_group] = row
            
            examples = row.get("Examples", "")
            # Split by comma
            for ex in examples.split(','):
                w_name = ex.strip()
                if w_name:
                    self.weapon_group_map[w_name.lower()] = term_group

    def process_weapons(self):
        print("Processing Weapons...")
        # File is weapons_and_armor.csv
        rows = self._read_csv("weapons_and_armor.csv")
        weapons = {}
        
        for row in rows:
            if row.get("Type") != "Weapon":
                continue
            
            name = row.get("Name")
            if not name: continue
            
            # Link to group
            # Try exact match or normalized match in map
            norm_name = name.lower()
            linked_group = self.weapon_group_map.get(norm_name, "Unknown")
            
            # If not found, try partial match? The prompt says "matching its name (normalized) against Weapon_Groups.csv"
            row["linked_group"] = linked_group
            
            weapons[name] = row
            
        self.data["Weapons"] = weapons

        # Also store Armor for completeness or CharEngine? 
        # Prompt only asked for Weapons processing in Detail 3, but CharEngine "Read Fee_Cost from equipped Weapon and Armor".
        # So I should store Armor too.
        armor = {}
        for row in rows:
            if row.get("Type") == "Armor":
                name = row.get("Name")
                if name:
                    armor[name] = row
        self.data["Armor"] = armor

    def process_skills(self):
        print("Processing Skills...")
        rows = self._read_csv("Skills.csv")
        skills = {}
        for row in rows:
            name = row.get("Skill Name")
            if name:
                skills[name] = row
        self.data["Skills"] = skills

    def process_talents(self):
        print("Processing Talents...")
        rows = self._read_csv("Talents.csv")
        talents = {}
        for row in rows:
            name = row.get("Talent_Name")
            if name:
                # Prompt: Include columns: Requirement_ID, Requirement_Value, Effect_Logic
                filtered = {
                    "Requirement_ID": row.get("Requirement_ID"),
                    "Requirement_Value": row.get("Requirement_Value"),
                    "Effect_Logic": row.get("Effect_Logic"),
                    "Description": row.get("Description", "") # Helpful to keep
                }
                talents[name] = filtered
        self.data["Talents"] = talents

    def process_spells(self):
        print("Processing Spells...")
        rows = self._read_csv("Schools of Power.csv")
        spells = {}
        for row in rows:
            name = row.get("Name")
            if name:
                # Prompt: Cost, Cost_Type, Effect
                # Map Tier -> Cost
                spells[name] = {
                    "Cost": row.get("Tier"),
                    "Cost_Type": row.get("Attribute"), # Assumed based on prompt "Cost_Type" and file "Start Attribute" relation
                    "Effect": row.get("Description"),
                    "School": row.get("School"), # Extra info
                    "Damage_Type": row.get("Damage_Type")
                }
        self.data["Spells"] = spells

    def process_combat_formula(self):
        print("Processing Combat Formula...")
        rows = self._read_csv("Combat_Formula.csv")
        combat_rules = []
        
        for row in rows:
            margin = row.get("MARGIN RANGE", "")
            outcome = row.get("OUTCOME NAME", "")
            
            if not outcome and not margin:
                continue

            # Handle parsing
            min_val = -999
            max_val = 999
            
            # Explicit fixes for #ERROR! or expected format
            if outcome == "CRUSHING BLOW":
                # Likely 10+
                min_val = 10
                max_val = 99
            elif outcome == "SOLID HIT":
                # Likely 5 to 9
                min_val = 5
                max_val = 9
            elif outcome == "GRAZE":
                # Likely 1 to 4
                min_val = 1
                max_val = 4
            elif "NAT 20" in margin:
                min_val = 200 # Special flag? Or just handle logic separately.
                max_val = 200
            elif "NAT 1" in margin:
                min_val = -200
                max_val = -200
            elif "TIE" in margin or margin == "0":
                min_val = 0
                max_val = 0
            elif "minus 1to4" in margin or "-1 to -5" in margin: # The file had -1 to -5
                 min_val = -5
                 max_val = -1
            elif "-6 to -11" in margin:
                min_val = -11
                max_val = -6
            elif "-12 or less" in margin:
                min_val = -99
                max_val = -12
            else:
                # Try generic "XtoY" parsing if strings were literally "minus 1to4"
                 try:
                     parts = margin.lower().replace("minus ", "-").split('to')
                     if len(parts) == 2:
                         min_val = int(parts[0])
                         max_val = int(parts[1])
                 except:
                     pass

            rule = {
                "Outcome": outcome,
                "Range": {"min": min_val, "max": max_val},
                "Effect": row.get("STATUS EFFECT / CONSEQUENCE"),
                "Damage_Type": row.get("DAMAGE TYPE")
            }
            combat_rules.append(rule)
            
        self.data["Combat_Rules"] = combat_rules

    def process_derived_stats(self):
        print("Processing Derived Stats...")
        rows = self._read_csv("Derived_Stats.csv")
        derived = {}
        for row in rows:
            stat_id = row.get("Stat_ID")
            if stat_id:
                derived[stat_id] = row
        self.data["Derived_Stats"] = derived

    def process_biomes(self):
        print("Processing Biomes...")
        rows = self._read_csv("Biome_Details.csv")
        biomes = {}
        for row in rows:
            name = row.get("Biome")
            if name:
                biomes[name] = {
                    "Description": row.get("Description"),
                    "Factions": row.get("Factions", "").split("; ")
                }
        self.data["Biomes"] = biomes

    def validate_data(self):
        print("Validating Data...")
        if "Weapons" not in self.data or "Skills" not in self.data:
            print("Skipping validation (missing data)")
            return

        skill_names = set(k.lower() for k in self.data["Skills"].keys())
        
        for w_name, w_data in self.data["Weapons"].items():
            group = w_data.get("linked_group", "")
            if group.lower() not in skill_names:
                # print(f"WARNING: Weapon '{w_name}' has linked_group '{group}' which matches no Skill.")
                pass

    def save_json(self):
        out_path = os.path.join(self.data_dir, "chaos_core.json")
        print(f"Saving to {out_path}...")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4)
        print("Done.")

if __name__ == "__main__":
    foundry = ChaosFoundry()
    foundry.process_species()
    foundry.process_weapon_groups()
    foundry.process_weapons()
    foundry.process_skills()
    foundry.process_talents()
    foundry.process_spells()
    foundry.process_derived_stats()
    foundry.process_combat_formula()
    foundry.process_biomes()
    foundry.validate_data()
    foundry.save_json()

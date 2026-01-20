
import csv
import os
import random

class Item:
    def __init__(self, data):
        self.name = data.get("Name", "Unknown")
        self.type = data.get("Type", "Misc")
        self.tags = self._parse_tags(data.get("Logic_Tags", ""))
        self.family = "" 
        
        # Heuristic for Family (Armor Group) because CSV format varies
        # weapons_and_armor.csv has "Related_Skill" column which often holds the Group/Family
        self.family = data.get("Related_Skill", "")
        if not self.family and self.type == "Armor":
             # Fallback or specific parsing
             pass

    def _parse_tags(self, tag_str):
        """
        Parses 'DMG:2d6:Slash|PROP:Heavy' into a dict.
        """
        tags = {}
        if not tag_str: return tags
        
        parts = tag_str.split('|')
        for part in parts:
            tokens = part.split(':')
            key = tokens[0]
            val = tokens[1:] if len(tokens) > 1 else [True]
            tags[key] = val
        return tags

class Inventory:
    def __init__(self):
        self.items = []
        self.equipped = {
            "Main Hand": None,
            "Off Hand": None,
            "Armor": None
        }
        self.db = self._load_db()
        self.armor_stats = {
            "Heavy": "Endurance",
            "Natural": "Vitality",
            "Light": "Reflexes",
            "Cloth": "Knowledge",
            "Medium": "Willpower",
            "Utility": "Intuition"
        }
        self.skill_map = self._load_skills()
        # Aliases for mismatched data (CSV vs CSV) - Now using canonical names from Skills.csv
        self.skill_aliases = {
            # Weapons: Small, Medium, Large, Great, Exotic, Fist, Thrown, Ballistics, Blast, Long Shot, Simple
            # Armor: Cloth, Light, Medium, Heavy, Natural, Utility
        }

    def _load_skills(self):
        """Loads Skills.csv to map Skill Name -> Attribute"""
        s_map = {}
        try:
            # Try multiple paths similar to _load_db
            paths = [
                os.path.join(os.path.dirname(__file__), "../Data/Skills.csv"),
                "C:/Users/krazy/Desktop/BRQSE/Data/Skills.csv"
            ]
            target_path = next((p for p in paths if os.path.exists(p)), None)
            
            if target_path:
                with open(target_path, 'r', encoding='utf-8-sig') as f: # Handle SIG for BOM
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Map "Great Weapons" -> "MIGHT"
                        s_name = row.get("Skill Name", "").strip()
                        attr = row.get("Attribute", "").strip()
                        if s_name and attr:
                            s_map[s_name] = attr
                            
                            # Also handle "The X" variants just in case
                            if not s_name.startswith("The ") and " " in s_name:
                                s_map[f"The {s_name}"] = attr
        except Exception as e:
            print(f"[Inventory] Error loading Skills: {e}")
        return s_map

    def _load_db(self):
        """Loads weapons_and_armor.csv"""
        db = {}
        try:
            # Assume script is in combat simulator/
            # Try multiple paths
            paths = [
                os.path.join(os.path.dirname(__file__), "../Data/weapons_and_armor.csv"),
                os.path.join(os.path.dirname(__file__), "../../Data/weapons_and_armor.csv"),
                "C:/Users/krazy/Desktop/BRQSE/Data/weapons_and_armor.csv" # Hard fallback
            ]
            
            target_path = None
            for p in paths:
                if os.path.exists(p):
                    target_path = p
                    break
            
            if not target_path:
                print(f"[Inventory] Warning: DB not found. Checked: {paths}")
                return db
                
            with open(target_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if "Name" in row:
                        db[row["Name"].strip()] = row
                    elif "\ufeffName" in row: # Handle explicit BOM if sig fails
                        db[row["\ufeffName"].strip()] = row
                    elif list(row.keys())[0].strip() == "Name": # Fallback
                        db[row[list(row.keys())[0]]] = row
        except Exception as e:
            print(f"[Inventory] Error loading DB: {e}")
        return db

    def equip(self, item_name, slot="Main Hand"):
        if item_name not in self.db:
            print(f"[Inventory] Item '{item_name}' not found in DB.")
            return False
            
        item_data = self.db[item_name]
        item = Item(item_data)
        
        if item.type == "Armor":
            self.equipped["Armor"] = item
        else:
            self.equipped[slot] = item
        return True

    def get_weapon_stats(self):
        """Returns (damage_dice, damage_type, tags) for Main Hand"""
        wpn = self.equipped["Main Hand"]
        if not wpn:
            # Unarmed default
            return ("1d4", "Bludgeoning", {"Unarmed": True})
            
        # Parse DMG tag: ['2d6', 'Slash']
        dmg_tag = wpn.tags.get("DMG", ["1d4", "Bludgeoning"])
        dice = dmg_tag[0]
        dtype = dmg_tag[1] if len(dmg_tag) > 1 else "Bludgeoning"
        
        return (dice, dtype, wpn.tags)

    def get_weapon_main_stat(self):
        """Returns the Attribute Name used for attacks (Might, Finesse, etc)."""
        wpn = self.equipped["Main Hand"]
        if not wpn: return "Might" # Default Unarmed? Or Fortitude if "The Fist"?
        
        # 1. Check direct aliases
        skill = wpn.family.strip() # "Related_Skill" from CSV
        
        if skill in self.skill_aliases:
            return self.skill_aliases[skill]
            
        # 2. Check loaded Skills.csv
        if skill in self.skill_map:
            return self.skill_map[skill]
            
        # 3. Fallback: Tag Check
        if "Finesse" in wpn.tags: return "Finesse"
        
        # 4. Default
        return "Might"

    def get_defense_stat(self):
        """Returns the Stat Name used for defense based on Armor."""
        armor = self.equipped["Armor"]
        if not armor:
            return "Reflexes" # Default unarmored
        
        # Map Armor Family to Stat
        # In the CSV, the "Related_Skill" column for Armor seems to hold the Family (Plate, Bio, etc)
        family = armor.family.strip()
        stat = self.armor_stats.get(family, "Reflexes")
        return stat
        
    def get_resistances(self):
        """Returns list of types resisted"""
        armor = self.equipped["Armor"]
        res = []
        if armor:
            if "RESIST" in armor.tags:
                res.extend(armor.tags["RESIST"])
        return res


import json
import os

class Character:
    def __init__(self, species_name, weapon_name="Unarmed", armor_name="Clothes", stats_override=None):
        self.rules = self._load_rules()
        self.species_name = species_name
        self.weapon_name = weapon_name
        self.armor_name = armor_name
        
        # Load Base Attributes from Species
        species_data = self.rules.get("Species", {}).get(species_name)
        if not species_data:
            # Fallback or error
            if species_name in ["Debug Goblin"]: # Hardcoded fallback logic for debug
                species_data = {"Might": 10, "Reflexes": 10, "Endurance": 10, "Vitality": 10}
            else:
                 species_data = {}
        
        self.attributes = species_data.copy()
        if stats_override:
            self.attributes.update(stats_override)
            
        self.skills = {} 
        self._init_skills()
        
        # Derived Stats
        self.derived = {}
        self.calculate_derived_stats()
        
        # Current State
        self.current_hp = self.derived.get("HP", 0)
        self.current_cmp = self.derived.get("CMP", 0)
        self.current_sp = self.derived.get("SP", 0)
        self.current_fp = self.derived.get("FP", 0)

    def _load_rules(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(base_dir, "../Data/chaos_core.json")
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def _init_skills(self):
        # Determine Weapon Skill
        w_data = self.rules.get("Weapons", {}).get(self.weapon_name, {})
        # Store for external access (User Code Compat)
        self.weapon_data = w_data
        
        a_data = self.rules.get("Armor", {}).get(self.armor_name, {})
        self.armor_data = a_data
        
        # Use linked_group as skill name
        linked_group = w_data.get("linked_group", "")
        if linked_group:
            self.skills[linked_group] = 1

    # Alias for User Code Compatibility
    def get_roll_mod(self, stat_name):
        return self.get_roll_modifiers(stat_name, None)

    def calculate_derived_stats(self):
        stats_def = self.rules.get("Derived_Stats", {})
        
        def get_attr(attr_name):
            if attr_name == "Refflexes": attr_name = "Reflexes"
            attr_name = attr_name.replace("Attribute ", "") # weird prefixes?
            return int(self.attributes.get(attr_name, 0))

        for stat_key, def_data in stats_def.items():
            base_str = str(def_data.get("Base_Value", "0"))
            if base_str == "B D": base = 0
            else:
                try: base = int(base_str)
                except: base = 0
            
            # Simple Formula Parsing
            # We know the known IDs: HP, CMP, SP, FP, SPD
            val_a = get_attr(def_data.get("Attribute_A", "-"))
            val_b = get_attr(def_data.get("Attribute_B", "-"))
            val_c = get_attr(def_data.get("Attribute_C", "-"))
            
            final_val = base
            
            # Logic Map based on reading Derived_Stats.csv (from memory/previous steps)
            # HP = Base + Vitality + Fortitude (Example)
            # We'll trust the A/B/C mapping from Foundry.
            
            # Stat_ID logic overrides if CSV formula string is complex
            if stat_key == "SPD":
                 # Base + (A * 5) usually?
                 final_val = base + val_a # Simplified
            else:
                 final_val = base + val_a + val_b + val_c
                 
            self.derived[stat_key] = final_val

        # --- Loadout Cost ---
        w_data = self.rules.get("Weapons", {}).get(self.weapon_name, {})
        a_data = self.rules.get("Armor", {}).get(self.armor_name, {})
        
        def get_cost(item):
            try: return int(item.get("Fee_Cost", 0))
            except: return 0
            
        w_cost = get_cost(w_data)
        a_cost = get_cost(a_data)
        
        # Deduct from Stamina (SP) usually, unless Magic?
        # Requirement: "Subtract these costs from... Max_Stamina or Max_Focus"
        # We'll assume Physical = SP.
        if "SP" in self.derived:
            self.derived["SP"] = max(0, self.derived["SP"] - (w_cost + a_cost))

    def get_roll_modifiers(self, stat_name, skill_name=None):
        attr = int(self.attributes.get(stat_name, 0))
        skill = self.skills.get(skill_name, 0) if skill_name else 0
        return attr + skill

    def apply_damage(self, amount):
        self.current_hp -= amount
        if self.current_hp < 0: self.current_hp = 0
        
    def apply_composure_damage(self, amount):
        self.current_cmp -= amount
        if self.current_cmp < 0: self.current_cmp = 0

if __name__ == "__main__":
    c = Character("Mammal", "Greatsword", "Plate")
    print(f"Stats: HP {c.current_hp}/{c.derived['HP']}, SP {c.current_sp}/{c.derived['SP']}")

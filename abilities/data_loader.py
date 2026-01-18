import csv
import os

class DataLoader:
    def __init__(self, data_dir=None):
        if data_dir:
            self.data_dir = data_dir
        else:
            # Default to ../Data relative to this file
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.data_dir = os.path.join(base_dir, "../Data")
        
        self.talents = []
        self.schools = []
        self.skills = []
        self.species_skills = {}
        
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
        
        # Load Species Skills (Assuming generic naming convention from Species.csv if needed, 
        # but for now we can just load the known ones or scan directory)
        # Based on file list: Aquatic, Avian, Insect, Mammal, Plant, Reptile
        species_list = ["Aquatic", "Avian", "Insect", "Mammal", "Plant", "Reptile"]
        for sp in species_list:
            self.species_skills[sp] = self._load_csv(f"{sp}_Skills.csv")

    def get_all_effects(self):
        """
        Returns a list of all unique effect descriptions/strings found in the data.
        Useful for building the registry.
        """
        effects = set()
        
        # 1. Talents
        for t in self.talents:
            if "Effect" in t: effects.add(f"Talent: {t.get('Talent_Name')} -> {t['Effect']}")
            if "Effect_Logic" in t: effects.add(f"Talent_Logic: {t.get('Talent_Name')} -> {t['Effect_Logic']}")

        # 2. Schools
        for s in self.schools:
            if "Description" in s: effects.add(f"School: {s.get('School')} -> {s['Description']}")

        # 3. Skills
        for s in self.skills:
            if "Description" in s: effects.add(f"Skill: {s.get('Skill Name')} -> {s['Description']}")

        # 4. Species Skills
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
    
    print("\n--- Sample Effects ---")
    all_eff = dl.get_all_effects()
    for e in all_eff[:10]:
        print(e)

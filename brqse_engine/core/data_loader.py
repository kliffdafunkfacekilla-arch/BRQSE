import json
import os
from typing import Dict, List, Any, Optional

class DataLoader:
    """
    Handles loading of static game data (Gear, Spells, etc.)
    and hydration of dynamic objects.
    """
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            # Try to find base_dir relative to this file
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
        self.base_dir = base_dir
        self.gear_path = os.path.join(base_dir, "Web_ui", "public", "data", "Gear.json")
        self.spells_path = os.path.join(base_dir, "Web_ui", "public", "data", "Spells.json")
        self.backgrounds_path = os.path.join(base_dir, "Web_ui", "public", "data", "Backgrounds.json")
        
        self.gear_db: Dict[str, Dict] = {}
        self.spells_db: List[Dict] = []
        
        self.load_all()

    def load_all(self):
        self.load_gear()
        self.load_spells()

    def load_gear(self):
        if not os.path.exists(self.gear_path):
            return
        try:
            with open(self.gear_path, 'r') as f:
                data = json.load(f)
                for item_data in data:
                    name = item_data.get("Name")
                    if name:
                        self.gear_db[name] = item_data
        except Exception as e:
            print(f"[DataLoader] Error loading Gear: {e}")

    def load_spells(self):
        if not os.path.exists(self.spells_path):
             return
        try:
            with open(self.spells_path, 'r') as f:
                self.spells_db = json.load(f)
        except Exception as e:
            print(f"[DataLoader] Error loading Spells: {e}")

    def get_item_data(self, item_name: str) -> Optional[Dict]:
        return self.gear_db.get(item_name)
    
    def get_spell_data(self, spell_name: str) -> Optional[Dict]:
        for s in self.spells_db:
            if s.get("Name") == spell_name:
                return s
        return None

    def get_all_gear(self) -> List[Dict]:
        return list(self.gear_db.values())

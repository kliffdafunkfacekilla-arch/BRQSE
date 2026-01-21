import json
import os
from typing import Dict, List, Any
from brqse_engine.models.item import Item
from brqse_engine.models.character import Character

class DataLoader:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.gear_path = os.path.join(base_dir, "Web_ui", "public", "data", "Gear.json")
        self.spells_path = os.path.join(base_dir, "Web_ui", "public", "data", "Spells.json")
        self.backgrounds_path = os.path.join(base_dir, "Web_ui", "public", "data", "Backgrounds.json")
        
        self.gear_db: Dict[str, Item] = {}
        self.spells_db: List[Dict] = []
        
        self.load_all()

    def load_all(self):
        self.load_gear()
        self.load_spells()
        # Backgrounds not strictly needed for engine logic yet, mostly builder

    def load_gear(self):
        """Loads Gear.json into Item objects."""
        if not os.path.exists(self.gear_path):
            print(f"[DataLoader] Warning: {self.gear_path} not found.")
            return

        try:
            with open(self.gear_path, 'r') as f:
                data = json.load(f)
                for item_data in data:
                    item = Item(item_data)
                    self.gear_db[item.name] = item
            print(f"[DataLoader] Loaded {len(self.gear_db)} items.")
        except Exception as e:
            print(f"[DataLoader] Error loading Gear: {e}")

    def load_spells(self):
        """Loads Spells.json."""
        if not os.path.exists(self.spells_path):
             return
        try:
            with open(self.spells_path, 'r') as f:
                self.spells_db = json.load(f)
        except Exception as e:
            print(f"[DataLoader] Error loading Spells: {e}")

    def get_item(self, item_name: str) -> Item:
        return self.gear_db.get(item_name)
    
    def hydrate_character(self, char_data: Dict[str, Any]) -> Character:
        """
        Creates a Character object and ensures Inventory strings are converted to Items.
        """
        char = Character(char_data)
        
        # Hydrate Inventory
        # Assuming char_data["Inventory"] is a list of strings
        hydrated_inv = []
        raw_inv = char_data.get("Inventory", [])
        for i_entry in raw_inv:
            if isinstance(i_entry, str):
                item = self.get_item(i_entry)
                if item:
                    hydrated_inv.append(item)
            elif isinstance(i_entry, dict):
                 # Already dict? Should ideally be loading from DB to get full stats 
                 # and not relying on saved snapshot if stats changed.
                 # But strictly, the Logic Tags need to be parsed.
                 name = i_entry.get("Name")
                 if name:
                     item = self.get_item(name)
                     if item: hydrated_inv.append(item)
        
        char.inventory = hydrated_inv
        
        # Hydrate Equipment
        raw_eq = char_data.get("Equipment", {})
        for slot, i_name in raw_eq.items():
            if isinstance(i_name, str) and i_name != "Empty":
                char.equipment[slot] = self.get_item(i_name)
                
        return char

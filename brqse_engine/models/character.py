from typing import Dict, Any, List, Optional
from .item import Item

class Character:
    """
    Represents a Player Character or NPC.
    Holds Stats, Skills, Powers, and Inventory.
    """
    def __init__(self, data: Dict[str, Any]):
        self.name = data.get("Name", "Unnamed")
        self.species = data.get("Species", "Unknown")
        self.stats = data.get("Stats", {})
        self.skills = data.get("Skills", [])
        self.skills = data.get("Skills", [])
        self.powers = data.get("Powers", [])
        self.sprite = data.get("Sprite", None)
        
        # Calculate Derived Stats (HP, etc)
        self.max_hp = self._calculate_max_hp()
        self.current_hp = data.get("Current_HP", self.max_hp)
        
        # Inventory Management
        self.inventory: List[Item] = []
        raw_inv = data.get("Inventory", [])
        for i_data in raw_inv:
            if isinstance(i_data, str):
                # If just a string name, we need to load it from DB later. 
                # For now store as stub or handle in Data Loader.
                # Storing strings for now, Controller will hydrate.
                pass 
            elif isinstance(i_data, dict):
                 self.inventory.append(Item(i_data))

        self.equipment: Dict[str, Optional[Item]] = {
            "Main Hand": None,
            "Off Hand": None,
            "Armor": None,
            # Add other slots as needed
        }
        
        # Load Equipment if present in data
        raw_eq = data.get("Equipment", {})
        # Note: Hydration of equipment usually requires the Item DB.
        # This model might just hold the names if we want it to be pure data, 
        # or we inject the Item DB.
        self.equipment_names = raw_eq # Keep raw names for reference

    def _calculate_max_hp(self) -> int:
        """
        HP = Vitality + Fortitude + 10 (Base)
        """
        vit = self.stats.get("Vitality", 0)
        fort = self.stats.get("Fortitude", 0)
        return 10 + vit + fort

    def get_stat(self, stat_name: str) -> int:
        return self.stats.get(stat_name, 0)
    
    def has_skill(self, skill_name: str) -> bool:
        return skill_name in self.skills

    def to_dict(self) -> Dict[str, Any]:
        """Returns JSON-serializable dict representation."""
        return {
            "Name": self.name,
            "Species": self.species,
            "Stats": self.stats,
            "Skills": self.skills,
            "Powers": self.powers,
            "Current_HP": self.current_hp,
            # Serialize inventory/equipment as needed
        }

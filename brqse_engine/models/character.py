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
        self.ai_archetype = data.get("AI_Archetype", "Berserker") # Default to Melee Rush
        
        # Calculate Derived Stats (HP, etc)
        self.max_hp = self._calculate_max_hp()
        self.current_hp = data.get("Current_HP", self.max_hp)
        
        # Social Stats (Composure)
        self.max_composure = self._calculate_max_composure()
        self.current_composure = data.get("Current_Composure", self.max_composure)
        
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

    def _calculate_max_composure(self) -> int:
        """
        Composure = Charm + Logic + 10 (Base)
        """
        charm = self.stats.get("Charm", 0)
        logic = self.stats.get("Logic", 0)
        return 10 + charm + logic

    def get_stat(self, stat_name: str) -> int:
        return self.stats.get(stat_name, 0)
    
    def has_skill(self, skill_name: str) -> bool:
        return skill_name in self.skills

    def get_equipped_armor_bonus(self) -> int:
        """Returns sum of AC bonuses from equipped items."""
        total_ac = 0
        for item in self.inventory:
            if item.is_equipped and item.data.get("AC_Bonus"):
                 total_ac += int(item.data.get("AC_Bonus", 0))
        return total_ac

    def get_equipped_weapon(self) -> Dict[str, Any]:
        """Returns the first equipped weapon found or Unarmed default."""
        for item in self.inventory:
             if item.is_equipped and item.type == "Weapon":
                 return item.data
        
        # Default Unarmed
        return {
            "Name": "Unarmed Strike",
            "Damage": "1d4",
            "Stat": "Might",
            "Range": 1
        }

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

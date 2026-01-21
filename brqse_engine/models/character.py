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
        
        # Calculate Derived Stats: CONDITION (Body HP) and COMPOSURE (Mind HP)
        # Condition = Might + Vitality + Reflexes (Physical Resilience)
        # Composure = Willpower + Logic + Awareness (Mental Resilience)
        self.max_condition = self._calculate_max_condition()
        self.current_condition = data.get("Current_Condition", self.max_condition)
        
        self.max_composure = self._calculate_max_composure()
        self.current_composure = data.get("Current_Composure", self.max_composure)
        
        # Legacy HP alias for compatibility
        self.max_hp = self.max_condition
        self.current_hp = self.current_condition
        
        # Injury/Death System
        self.injuries: List[str] = data.get("Injuries", [])  # List of injury names
        self.death_clock: int = data.get("Death_Clock", self._get_max_death_clock())
        self.is_dying: bool = False
        self.is_broken: bool = False
        
        # Inventory Management
        self.inventory: List[Item] = []
        raw_inv = data.get("Inventory", [])
        for i_data in raw_inv:
            if isinstance(i_data, str):
                pass 
            elif isinstance(i_data, dict):
                 self.inventory.append(Item(i_data))

        self.equipment: Dict[str, Optional[Item]] = {
            "Main Hand": None,
            "Off Hand": None,
            "Armor": None,
        }
        
        raw_eq = data.get("Equipment", {})
        self.equipment_names = raw_eq

    def _calculate_max_condition(self) -> int:
        """Condition = Might + Vitality + Reflexes (Body)"""
        might = self.stats.get("Might", 10)
        vit = self.stats.get("Vitality", 10)
        reflex = self.stats.get("Reflexes", 10)
        return might + vit + reflex

    def _calculate_max_hp(self) -> int:
        """Legacy: Alias for max_condition."""
        return self._calculate_max_condition()

    def _calculate_max_composure(self) -> int:
        """Composure = Willpower + Logic + Awareness (Mind)"""
        will = self.stats.get("Willpower", 10)
        logic = self.stats.get("Logic", 10)
        aware = self.stats.get("Awareness", 10)
        return will + logic + aware
    
    def _get_max_death_clock(self) -> int:
        """Death Clock = Vitality stat (min 1)"""
        return max(1, self.stats.get("Vitality", 10))
    
    @property
    def is_bloodied(self) -> bool:
        """Below 50% Condition triggers 'Bloodied' state."""
        return self.current_condition <= (self.max_condition // 2)
    
    @property
    def is_shaken(self) -> bool:
        """Below 50% Composure triggers 'Shaken' state."""
        return self.current_composure <= (self.max_composure // 2)

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

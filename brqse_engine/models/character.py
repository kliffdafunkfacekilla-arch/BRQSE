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
        self.skill_ranks: Dict[str, int] = data.get("Skill_Ranks", {})  # Skill Name -> Rank (0-12)
        self.powers = data.get("Powers", [])
        self.sprite = data.get("Sprite", None)
        self.ai_archetype = data.get("AI_Archetype", "Berserker") # Default to Melee Rush
        
        # === PROGRESSION SYSTEM ===
        self.level: int = data.get("Level", 1)
        self.xp: int = data.get("XP", 0)
        self.tier: str = self._get_tier_name()
        
        # Resource Pools (Base + Level Bonuses)
        base_stamina = self.stats.get("Endurance", 10) + self.stats.get("Finesse", 10) + self.stats.get("Fortitude", 10)
        base_focus = self.stats.get("Knowledge", 10) + self.stats.get("Charm", 10) + self.stats.get("Intuition", 10)
        
        # Add capacity bonuses from level
        stamina_bonus, focus_bonus = self._get_capacity_bonus()
        self.max_stamina: int = base_stamina + stamina_bonus
        self.max_focus: int = base_focus + focus_bonus
        self.current_stamina: int = data.get("Current_Stamina", self.max_stamina)
        self.current_focus: int = data.get("Current_Focus", self.max_focus)
        
        # Magic Tier = ceil(Level / 2)
        self.max_magic_tier: int = (self.level + 1) // 2  # Level 1=T1, Level 3=T2, etc.
        
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
    
    def _get_tier_name(self) -> str:
        """Returns tier name based on level."""
        if self.level >= 20: return "God"
        if self.level >= 17: return "Mythic"
        if self.level >= 14: return "Legend"
        if self.level >= 10: return "Master"
        if self.level >= 7: return "Elite"
        if self.level >= 4: return "Veteran"
        return "Novice"
    
    def _get_capacity_bonus(self) -> tuple:
        """Returns (stamina_bonus, focus_bonus) from level progression."""
        # Cumulative bonuses based on Progression.csv
        stamina = 0
        focus = 0
        
        # Level thresholds and their bonuses
        capacity_table = {
            2: (2, 0), 3: (0, 2), 4: (2, 0), 5: (0, 2), 6: (4, 0),
            7: (0, 4), 8: (4, 0), 9: (0, 4), 10: (10, 10),
            11: (2, 0), 12: (0, 2), 13: (5, 0), 14: (0, 5), 15: (5, 0),
            16: (0, 5), 17: (10, 0), 18: (0, 10), 19: (10, 10), 20: (999, 999)
        }
        
        for lvl in range(2, self.level + 1):
            if lvl in capacity_table:
                stamina += capacity_table[lvl][0]
                focus += capacity_table[lvl][1]
        
        return stamina, focus
    
    def gain_xp(self, amount: int) -> bool:
        """Add XP and check for level up. Returns True if leveled."""
        self.xp += amount
        leveled = False
        
        # XP thresholds from Progression.csv
        xp_table = [0, 300, 900, 2700, 6500, 14000, 23000, 34000, 48000, 64000,
                    85000, 100000, 120000, 145000, 175000, 210000, 250000, 300000, 355000, 420000]
        
        while self.level < 20 and self.xp >= xp_table[self.level]:
            self.level += 1
            self.tier = self._get_tier_name()
            self.max_magic_tier = (self.level + 1) // 2
            # Recalculate capacity
            stamina_bonus, focus_bonus = self._get_capacity_bonus()
            base_stamina = self.stats.get("Endurance", 10) + self.stats.get("Finesse", 10) + self.stats.get("Fortitude", 10)
            base_focus = self.stats.get("Knowledge", 10) + self.stats.get("Charm", 10) + self.stats.get("Intuition", 10)
            self.max_stamina = base_stamina + stamina_bonus
            self.max_focus = base_focus + focus_bonus
            leveled = True
        
        return leveled
    
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
        return skill_name in self.skills or skill_name in self.skill_ranks
    
    def get_skill_rank(self, skill_name: str) -> int:
        """Returns skill rank (0-12). Skills list grants rank 1, skill_ranks dict has actual values."""
        if hasattr(self, 'skill_ranks') and skill_name in self.skill_ranks:
            return self.skill_ranks[skill_name]
        if skill_name in self.skills:
            return 1  # Default rank for having skill
        return 0
    
    def get_mastery_tier(self, skill_name: str) -> str:
        """Returns mastery tier based on skill rank: 0-2=None, 3-5=Novice, 6-8=Adept, 9-11=Master, 12+=Legend."""
        rank = self.get_skill_rank(skill_name)
        if rank >= 12: return "Legend"
        if rank >= 9: return "Master"
        if rank >= 6: return "Adept"
        if rank >= 3: return "Novice"
        return None
    
    def get_active_mastery_unlocks(self, skill_name: str) -> list:
        """Returns list of all mastery unlocks the character has for a skill."""
        from brqse_engine.abilities.data_loader import DataLoader
        dl = DataLoader()
        
        tier = self.get_mastery_tier(skill_name)
        if not tier:
            return []
        
        # Determine which mastery table to use
        mastery_table = None
        if skill_name in dl.weapon_mastery:
            mastery_table = dl.weapon_mastery[skill_name]
        elif skill_name in dl.armor_mastery:
            mastery_table = dl.armor_mastery[skill_name]
        elif skill_name in dl.tool_mastery:
            mastery_table = dl.tool_mastery[skill_name]
        
        if not mastery_table:
            return []
        
        # Get all unlocks up to current tier
        tier_order = ["Novice", "Adept", "Master", "Legend"]
        unlocks = []
        for t in tier_order:
            if t in mastery_table:
                unlocks.append(mastery_table[t])
            if t == tier:
                break
        
        return unlocks

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

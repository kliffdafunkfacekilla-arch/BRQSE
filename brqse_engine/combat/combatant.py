from typing import Optional, List, Dict
from brqse_engine.models.character import Character
from brqse_engine.core.dice import Dice

class Combatant:
    """
    Runtime wrapper for a Character in combat.
    Manages Position, Initiative, Current HP, and Status Effects.
    """
    def __init__(self, character: Character, x: int = 0, y: int = 0, team: str = "Neutral"):
        self.character = character
        self.x = x
        self.y = y
        self.team = team
        self.initiative = 0
        
        # Runtime State
        self.current_hp = character.current_hp
        self.max_hp = character.max_hp
        
        self.action_used = False
        self.bonus_action_used = False
        self.reaction_used = False
        
        # Status Effects (Simplified list of strings or dicts for now)
        self.conditions: List[str] = []
        self.active_effects: List[Dict] = [] # {name, duration, ...}

        # Resources (Calculated from Stats for compatibility)
        self.sp = self._calc_resource("Endurance") + self._calc_resource("Finesse") + self._calc_resource("Fortitude")
        self.fp = self._calc_resource("Knowledge") + self._calc_resource("Charm") + self._calc_resource("Intuition")
        self.cmp = 10 + self._calc_resource("Willpower") + self._calc_resource("Logic") + self._calc_resource("Awareness")
        
    def _calc_resource(self, stat_name):
        return self.character.get_stat(stat_name)

    @property
    def hp(self): return self.current_hp
    @hp.setter
    def hp(self, val): self.current_hp = val

        
    @property
    def name(self):
        return self.character.name

    @property
    def species(self):
        return self.character.species

    @property
    def ai_archetype(self):
        return self.character.ai_archetype

    @property
    def sprite(self):
        return self.character.sprite

    def roll_initiative(self) -> int:
        """Rolls initiative based on Intuition + Reflexes."""
        intuit = self.character.get_stat("Intuition")
        reflex = self.character.get_stat("Reflexes")
        alertness = intuit + reflex
        
        roll, _, _ = Dice.roll("1d20")
        
        # TODO: Handle advantage/bonuses from Traits if needed
        self.initiative = roll + alertness
        return self.initiative

    def take_damage(self, amount: int) -> bool:
        """
        Applies damage. Returns True if dead/down.
        """
        self.current_hp -= amount
        if self.current_hp < 0:
            self.current_hp = 0
        
        # Sync back to character model? 
        # For now, yes, assume persistent damage within the session.
        self.character.current_hp = self.current_hp
        
        return self.current_hp == 0

    def heal(self, amount: int) -> int:
        """Heals HP up to Max."""
        old = self.current_hp
        self.current_hp = min(self.current_hp + amount, self.max_hp)
        self.character.current_hp = self.current_hp
        return self.current_hp - old

    # --- Social/Composure Logic ---
    @property
    def max_composure(self):
        return self.character.max_composure

    @property
    def current_composure(self):
        return self.character.current_composure
    
    @current_composure.setter
    def current_composure(self, value):
        self.character.current_composure = max(0, min(value, self.max_composure))

    @property
    def is_broken(self): # Social equivalent of Dead
        return self.current_composure <= 0

    def take_social_damage(self, amount: int) -> int:
        """Apply damage to Composure."""
        # Reduce by Willpower/Composure defense? (Future)
        self.current_composure -= amount
        return amount

    def regain_composure(self, amount: int) -> int:
        """Heals Composure."""
        old = self.current_composure
        self.current_composure += amount
        return self.current_composure - old

    def get_stat_mod(self, stat: str) -> int:
        val = self.character.get_stat(stat)
        return (val - 10) // 2

    def get_ac(self) -> int:
        """
        Calculates Armor Class.
        Base 10 + Reflex Mod + (TODO: Armor/Shield/Buffs)
        """
        base = 10
        dex_mod = self.get_stat_mod("Reflexes")
        armor_bonus = self.character.get_equipped_armor_bonus()
        return base + dex_mod + armor_bonus

    # --- Status Management ---
    
    # --- Status Management ---
    
    def add_condition(self, condition: str):
        if condition not in self.conditions:
            self.conditions.append(condition)
            
    def remove_condition(self, condition: str):
        if condition in self.conditions:
            self.conditions.remove(condition)
            
    def has_condition(self, condition: str) -> bool:
        return condition in self.conditions

    def add_timed_effect(self, name: str, duration: int):
        """Adds an effect that expires after X rounds."""
        self.active_effects.append({"name": name, "duration": duration})
        
    def tick_effects(self) -> List[str]:
        """
        Decrements duration of effects. Returns list of expired effects.
        """
        expired = []
        active = []
        for effect in self.active_effects:
            effect["duration"] -= 1
            if effect["duration"] <= 0:
                expired.append(effect["name"])
            else:
                active.append(effect)
        self.active_effects = active
        return expired

    @property
    def is_alive(self) -> bool:
        return self.current_hp > 0
        
    @property
    def is_prone(self): return self.has_condition("Prone")
    
    @property
    def is_stunned(self): return self.has_condition("Stunned")

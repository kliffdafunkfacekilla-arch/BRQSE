import json
import os
import random

class Combatant:
    def __init__(self, filepath):
        self.filepath = filepath
        self.data = self._load_data(filepath)
        
        self.name = self.data.get("Name", "Unknown")
        self.stats = self.data.get("Stats", {})
        self.derived = self.data.get("Derived", {})
        self.body_parts = self.data.get("BodyParts", [])
        self.skills = self.data.get("Skills", [])
        
        # Combat State
        self.max_hp = self.derived.get("HP", 10)
        self.current_hp = self.max_hp
        self.initiative = 0
        
    def _load_data(self, filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return {}

    def roll_initiative(self):
        # Init based on Speed (Vitality + Willpower) from charcreate logic
        # But let's add a random d20 variance
        base_speed = self.derived.get("Speed", 10) 
        self.initiative = base_speed + random.randint(1, 20)
        return self.initiative

    def is_alive(self):
        return self.current_hp > 0

    def take_damage(self, amount):
        self.current_hp -= amount
        if self.current_hp < 0: self.current_hp = 0
        return self.current_hp

    def heal(self, amount):
        self.current_hp += amount
        if self.current_hp > self.max_hp: self.current_hp = self.max_hp

class CombatEngine:
    def __init__(self):
        self.combatants = []
        self.log = []

    def add_combatant(self, combatant):
        self.combatants.append(combatant)

    def roll_d20(self):
        return random.randint(1, 20)

    def resolve_round(self):
        # Sort by initiative
        self.combatants.sort(key=lambda c: c.initiative, reverse=True)
        
        results = []
        
        # Simple 1v1 logic for now for the loop
        # Everyone attacks the next person in the list, last attacks first
        for i, attacker in enumerate(self.combatants):
            if not attacker.is_alive(): continue
            
            # Find a target (next alive enemy)
            target = None
            for j in range(1, len(self.combatants)):
                idx = (i + j) % len(self.combatants)
                candidate = self.combatants[idx]
                if candidate.is_alive() and candidate != attacker:
                    target = candidate
                    break
            
            if target:
                res = self.attack(attacker, target)
                results.append(res)
            else:
                results.append(f"{attacker.name} has no one to fight!")
                
        return results

    def attack(self, attacker, target):
        # 1. Roll to Hit
        # Using 'Might' for melee, 'Reflexes' for hit chance default
        # If they have a weapon in inventory, we could check that, but let's stick to stats.
        
        atk_stat = attacker.stats.get("Might", 0)
        # Defense: 10 + Reflexes
        def_stat = target.stats.get("Reflexes", 0)
        defense = 10 + def_stat
        
        roll = self.roll_d20()
        total_hit = roll + atk_stat
        
        log_entry = f"{attacker.name} attacks {target.name}..."
        
        if total_hit >= defense:
            # Hit!
            # Damage: 1d6 + Might (Unarmed/Basic)
            dmg_roll = random.randint(1, 6)
            dmg_bonus = attacker.stats.get("Might", 0)
            total_dmg = max(1, dmg_roll + dmg_bonus) # Min 1 damage
            
            target.take_damage(total_dmg)
            log_entry += f" HIT! ({total_hit} vs {defense}) for {total_dmg} dmg. {target.name} HP: {target.current_hp}/{target.max_hp}"
        else:
            log_entry += f" MISS! ({total_hit} vs {defense})"
            
        return log_entry

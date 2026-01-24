
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../abilities"))
from data_loader import DataLoader

# --- CONFIGURATION ---
XP_COST_SKILL_BASE = 10  # Cost = Next Rank * 10
XP_COST_ATTR_BASE = 50   # Cost = Next Score * 50 (Attributes are expensive!)

class ProgressionEngine:
    def __init__(self):
        self.loader = DataLoader()
        if not self.loader.talents:
            self.loader.reload_all()

    def get_skill_upgrade_cost(self, current_rank):
        # Example: Rank 1->2 costs 20xp. Rank 4->5 costs 50xp.
        return (current_rank + 1) * XP_COST_SKILL_BASE

    def get_attr_upgrade_cost(self, current_score):
        # Example: Might 10->11 costs 550xp.
        return (current_score + 1) * XP_COST_ATTR_BASE

    def buy_skill_rank(self, combatant, skill_name):
        """Attempts to buy a skill rank. Returns (Success, Message)"""
        current_rank = combatant.skills.get(skill_name, 0)
        cost = self.get_skill_upgrade_cost(current_rank)
        
        if combatant.xp < cost:
            return False, f"Not enough XP! Need {cost}, have {combatant.xp}."
        
        # Transaction
        combatant.xp -= cost
        combatant.skills[skill_name] = current_rank + 1
        
        # Check for new Talents immediately
        new_talents = self.check_unlocks(combatant)
        
        # Save
        if hasattr(combatant, 'save_state'):
            combatant.save_state()
        
        msg = f"Upgraded {skill_name} to Rank {combatant.skills[skill_name]}."
        if new_talents:
            msg += f" Unlocked: {', '.join(new_talents)}!"
            
        return True, msg

    def buy_attribute(self, combatant, attr_name):
        """Attempts to increase an Attribute (Might, Reflex, etc)"""
        current_val = combatant.stats.get(attr_name, 10)
        cost = self.get_attr_upgrade_cost(current_val)
        
        if combatant.xp < cost:
            return False, f"Not enough XP! Need {cost}, have {combatant.xp}."
            
        combatant.xp -= cost
        combatant.stats[attr_name] = current_val + 1
        
        # Save
        if hasattr(combatant, 'save_state'):
            combatant.save_state()
        return True, f"Increased {attr_name} to {combatant.stats[attr_name]}."

    def check_unlocks(self, combatant):
        """Scans stats/skills to unlock Talents."""
        new_unlocks = []
        skills = combatant.skills
        if isinstance(skills, list): skills = {k: 1 for k in skills}
        if isinstance(skills, list): skills = {k: 1 for k in skills}
        
        # FIX: Ensure traits are strings not dicts
        normalized_traits = []
        for t in combatant.traits:
            if isinstance(t, dict): normalized_traits.append(t.get("Name") or t.get("name", "Unknown"))
            elif isinstance(t, str): normalized_traits.append(t)
            
        existing_traits = set(normalized_traits)
        
        for talent in self.loader.talents:
            t_name = talent.get("Talent_Name")
            if not t_name or t_name in existing_traits: continue
            
            req_type = talent.get("Requirement_Type")
            req_id = talent.get("Requirement_ID")
            try: req_val = int(talent.get("Requirement_Value", 0))
            except: req_val = 0
            
            met = False
            if req_type == "Skill_Rank":
                if skills.get(req_id, 0) >= req_val: met = True
                
            elif req_type == "Attribute":
                # Check Stat
                # Heuristic: If val <= 10, assume Modifier Requirement.
                # If val > 10, assume Score Requirement.
                check_mod = (req_val <= 10)
                
                if check_mod and hasattr(combatant, 'get_stat_modifier'):
                     current_val = combatant.get_stat_modifier(req_id)
                else:
                     current_val = combatant.stats.get(req_id, 0)
                     
                if current_val >= req_val:
                    met = True
            
            if met:
                combatant.traits.append(t_name)
                new_unlocks.append(t_name)
                
        if new_unlocks:
             if hasattr(combatant, 'save_state'):
                combatant.save_state()
            
        return new_unlocks

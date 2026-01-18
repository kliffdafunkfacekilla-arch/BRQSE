
import sys
import os

# Ensure we can import from abilities
sys.path.append(os.path.join(os.path.dirname(__file__), "../abilities"))
# But mechanics.py is in 'combat simulator', abilities is sibling 'abilities'.
# Assuming this file is in 'combat simulator' too?
# Or 'scripts'? 
# Let's put it in 'combat simulator/progression_engine.py'

from data_loader import DataLoader

class ProgressionEngine:
    def __init__(self):
        self.loader = DataLoader()
        # Initialize talents
        if not self.loader.talents:
            self.loader.reload_all()
            
    def check_unlocks(self, combatant):
        """
        Scans combatant stats and skills to unlock Talents.
        Returns a list of newly unlocked talent names.
        """
        new_unlocks = []
        
        # Verify combatant structure
        # combatant.stats = {"Might": 1, ...}
        # combatant.skills = {"Athletics": 3, ...} OR ["Athletics"] (Legacy)
        
        # Normalize Skills to Dict if List
        skills = combatant.skills
        if isinstance(skills, list):
            # Assume Rank 1 for existing skills
            skills = {k: 1 for k in skills}
            
        existing_traits = set(combatant.traits)
        
        for talent in self.loader.talents:
            t_name = talent.get("Talent_Name")
            if not t_name or t_name in existing_traits:
                continue
                
            req_type = talent.get("Requirement_Type")
            req_id = talent.get("Requirement_ID")
            
            try:
                req_val = int(talent.get("Requirement_Value", 0))
            except:
                req_val = 0
                
            met = False
            
            if req_type == "Skill_Rank":
                # Check Skill Rank
                # req_id is Skill Name (e.g. "The Great Weapons")
                rank = skills.get(req_id, 0)
                if rank >= req_val:
                    met = True
                    
            elif req_type == "Attribute":
                # Check Stat
                # Heuristic: If val <= 10, assume Modifier Requirement.
                # If val > 10, assume Score Requirement.
                # User confirmed: "Might 16 unlocks [because] +3 mod". 
                # Meaning Req Value is likely 3?
                
                check_mod = (req_val <= 10)
                
                if check_mod and hasattr(combatant, 'get_stat_modifier'):
                     current_val = combatant.get_stat_modifier(req_id)
                else:
                     current_val = combatant.stats.get(req_id, 0)
                     
                if current_val >= req_val:
                    met = True
                    
            elif req_type == "Level" or req_type == "None" or not req_type:
                # Basic/Free talents? Or Level check?
                # For now, ignore unless strict requirement
                pass
                
            if met:
                combatant.traits.append(t_name)
                new_unlocks.append(t_name)
                # Apply Immediate Effects? 
                # Most effects are handled by Engine Hooks (Active/Passive checks)
                
        return new_unlocks


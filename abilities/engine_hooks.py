
from .effects_registry import registry
from .data_loader import DataLoader

# Global loader to keep data in memory
loader = DataLoader()

def get_entity_effects(combatant):
    """
    Collects all effect strings from a combatant's species, skills, and talents.
    """
    effects = []
    
    # Species Skills
    sp_skills = loader.species_skills.get(combatant.species, [])
    for skill_name in combatant.skills:
        # Check species skills
        for s in sp_skills:
             name = s.get("Skill Name") or s.get("Skill")
             if name == skill_name:
                 eff = s.get("Effect Description") or s.get("Effect")
                 if eff: effects.append(eff)
                 
    # Generic Skills
    for s_row in loader.skills:
        if s_row.get("Skill Name") in combatant.skills:
            if s_row.get("Description"): effects.append(s_row.get("Description"))
            
    # Talents (Stored in combatant.traits or similar?)
    # mechanics.py says: self.skills is list of strings.
    # We might need to check 'Stats' or 'Derived' keys if talents are stored there, 
    # but charcreate.py stores Traits in 'Traits'.
    # mechanics.py currently doesn't load 'Traits' explicitly in __init__ ?
    # Let's peek at mechanics.py again or assume we can patch it.
    traits = getattr(combatant, "traits", []) # Safe access
    for t_row in loader.talents:
        if t_row.get("Talent_Name") in traits:
            if t_row.get("Effect"): effects.append(t_row.get("Effect"))

    # Schools (Powers)
    # mechanics.py doesn't seem to have 'powers' list, maybe 'skills' has them?
    # charcreate saves "Powers" list.
    powers = getattr(combatant, "powers", [])
    for p_name in powers:
        # Check Schools
        for sch in loader.schools:
            if sch.get("School") == p_name: # Or contained in string
                if sch.get("Description"): effects.append(sch.get("Description"))

    return effects

def apply_hooks(combatant, hook_type, context):
    """
    Run registry resolution for an entity's effects on a specific trigger.
    hook_type: 'ON_ATTACK', 'ON_HIT', 'ON_DEFEND', etc.
    context: dict
    """
    all_effs = get_entity_effects(combatant)
    print(f"DEBUG: apply_hooks {hook_type} for {combatant.name}. Effects: {all_effs}", flush=True)
    # Filter based on hook_type keywords? 
    # The registry uses regex matching on the DESCRIPTION. 
    # So we pass ALL descriptions to the registry?
    # No, that would be slow and trigger wrong things.
    # We rely on the extraction list categorization logic roughly.
    
    # Heuristic: Check keywords in description to decide if we run it?
    # Or just run specific regexes?
    
    # Ideally, we'd pre-parse effects into buckets.
    # For now, let's just try to resolve all of them against the registry
    # The registry matchers should be specific enough (e.g. "When attacked...")
    
    for eff in all_effs:
        # We can implement a filter here to avoid running "Active" effects as "Passive"
        low = eff.lower()
        if hook_type == "ON_ATTACK":
            # Allow attack modifiers, healing, buffs
            if not any(k in low for k in ["attack", "heal", "regain", "damage", "push", "teleport", "stun", "poison", "fear", "charm", "grapple"]): 
                continue
        elif hook_type == "ON_DEFEND":
            if not any(k in low for k in ["defend", "hit", "reflex", "will", "fortitude", "armor", "ac ", "resistance", "immune"]): 
                continue
            
        registry.resolve(eff, context)

        registry.resolve(eff, context)

def get_ability_data(ability_name):
    """
    Search schools, talents, and skills for a data dictionary matching the name.
    Returns the dict or None.
    """
    # Check Talents
    for t in loader.talents:
        if t.get("Talent_Name") == ability_name:
             return t
    
    # Check Schools/Powers
    for s in loader.schools: 
        if s.get("School") == ability_name: 
            return s
                
    # Check Generic Skills
    for sk in loader.skills:
        if sk.get("Skill Name") == ability_name:
            return sk
            
    return None

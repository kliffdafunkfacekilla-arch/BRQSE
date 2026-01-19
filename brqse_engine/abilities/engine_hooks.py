
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
            
    # Talents (Stored in combatant.traits)
    traits = getattr(combatant, "traits", [])
    for t_row in loader.talents:
        if t_row.get("Talent_Name") in traits:
            if t_row.get("Effect"): effects.append(t_row.get("Effect"))

    # Schools (Powers) - match by Name column
    powers = getattr(combatant, "powers", [])
    for p_name in powers:
        for sch in loader.schools:
            if sch.get("Name") == p_name:
                if sch.get("Description"): effects.append(sch.get("Description"))

    return effects

def apply_hooks(combatant, hook_type, context):
    """
    Run registry resolution for an entity's effects on a specific trigger.
    hook_type: 'ON_ATTACK', 'ON_HIT', 'ON_DEFEND', etc.
    context: dict
    """
    all_effs = get_entity_effects(combatant)
    
    for eff in all_effs:
        low = eff.lower()
        if hook_type == "ON_ATTACK":
            if not any(k in low for k in ["attack", "heal", "regain", "damage", "push", "teleport", "stun", "poison", "fear", "charm", "grapple"]): 
                continue
        elif hook_type == "ON_DEFEND":
            if not any(k in low for k in ["defend", "hit", "reflex", "will", "fortitude", "armor", "ac ", "resistance", "immune"]): 
                continue
            
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
    
    # Check Schools/Powers - match by "Name" column NOT "School"
    for s in loader.schools: 
        if s.get("Name") == ability_name: 
            return s
                
    # Check Generic Skills
    for sk in loader.skills:
        if sk.get("Skill Name") == ability_name:
            return sk
            
    return None

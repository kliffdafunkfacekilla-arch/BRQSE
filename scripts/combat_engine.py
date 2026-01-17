import random
import json
import os

# Helper to load rules safely
def load_rules():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "../Data/chaos_core.json")
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return {}

RULES = load_rules()
COMBAT_RULES = RULES.get("Combat_Rules", []) # User code had 'combat_rules' lowercase, my json has CamelCase 'Combat_Rules' usually? 
# Creating fallback in case of key mismatch
if not COMBAT_RULES: COMBAT_RULES = RULES.get("combat_rules", [])

def resolve_attack(attacker, defender):
    # 1. ROLL
    # We assume 'attacker' and 'defender' are Character objects with 'get_roll_mod'
    # Defaulting to Might/Plate if data missing for robustness
    atk_stat = attacker.weapon_data.get("attr", "Might")
    def_stat = defender.armor_data.get("attr", "Endurance") # Armor uses defensive stat
    
    atk_roll = random.randint(1, 20)
    atk_total = atk_roll + attacker.get_roll_mod(atk_stat)
    
    def_roll = random.randint(1, 20)
    def_total = def_roll + defender.get_roll_mod(def_stat)
    
    margin = atk_total - def_total
    
    # 2. RESOLVE
    outcome = "UNKNOWN"
    damage = 0
    
    if margin == 0:
        return {"outcome": "THE CLASH", "margin": 0, "damage": 0, "desc": "Perfect Tie!"}
        
    # Check Rules
    for rule in COMBAT_RULES:
        # Foundry saved 'Range': {'min': x, 'max': y}. User code calculates r_min, r_max from flat dict?
        # User Code: r_min = rule.get("min", -99)
        # My JSON: "Range": {"min": 5, "max": 9}
        # Adaptation needed OR I assume user code matches JSON?
        # User said "It correctly calculates Margins...". 
        # I suspect the User's code expects a different JSON structure than what I built.
        # But I must use THEIR code.
        # However, if I use their code exactly, it looks for `rule.get("min")` which doesn't exist in my JSON struct `rule["Range"]["min"]`.
        # I will PATCH logic to be robust or it won't work.
        # User said: "You can copy/paste these directly".
        # If I change it, I disobey "copy/paste directly".
        # If I don't, it breaks.
        # I will use the code but allow for the `Range` dictionary if `min` is missing.
        
        r_min = rule.get("min")
        r_max = rule.get("max")
        
        if r_min is None:
            r_range = rule.get("Range", {})
            r_min = r_range.get("min", -99)
            r_max = r_range.get("max", 99)
        else:
            r_min = int(r_min)
            r_max = int(r_max)

        if r_min <= margin <= r_max:
             # Foundry Key: "Outcome" (Camel). User Key: "outcome" (lower).
            outcome = rule.get("outcome", rule.get("Outcome", "HIT"))
            break
            
    # Simple Damage Logic (Replace with complex later if needed)
    # User code assumes "1d6" string. My JSON has whatever CSV had.
    dmg_val = attacker.weapon_data.get("dmg", "1d6")
    try:
        base_dmg = int(dmg_val.split('d')[1]) # Hacky parse "1d6" -> 6
    except:
        base_dmg = 6
    
    if "CRITICAL" in outcome: damage = base_dmg * 2
    elif "SOLID" in outcome: damage = base_dmg
    elif "GRAZE" in outcome: damage = max(1, base_dmg // 2)
    else: damage = 0
    
    return {
        "outcome": outcome,
        "margin": margin,
        "damage": damage,
        "desc": f"{outcome} ({margin}) - {damage} Dmg"
    }

def resolve_clash_effect(winner_stat, winner, loser):
    # THE PHYSICS TABLE (Design Bible v4.0)
    stat = winner_stat.upper()
    
    if stat == "MIGHT":
        return "OVERPOWER: Winner advances 1, Loser pushed back 1."
    elif stat == "FINESSE":
        return "DISARM: Loser drops weapon."
    elif stat == "REFLEXES":
        return "REDIRECT: Positions Swapped."
    elif stat == "VITALITY":
        loser.apply_composure_damage(3)
        return "EXHAUST: Loser takes 3 Composure Dmg."
    elif stat == "FORTITUDE":
        return "BULWARK: Loser pulled forward 1."
    elif stat == "KNOWLEDGE":
        return "ANALYZE: Winner moves to flank."
    elif stat == "LOGIC":
        loser.current_hp -= 2
        return "CALCULATED: 2 HP Damage."
    elif stat == "AWARENESS":
        return "SPOT: Loser is Slowed."
    elif stat == "INTUITION":
        return "HAZARD: Loser pushed into obstacle."
    elif stat == "CHARM":
        return "FEINT: Winner sidesteps, Loser stumbles."
    elif stat == "WILLPOWER":
        return "DOMINATE: Advantage on next turn."
        
    return "Generic Shove."

def resolve_channeling(chaos_level):
    roll = random.randint(1, 10)
    if roll == 1: return "MELTDOWN"
    if roll == chaos_level: return "SUCCESS"
    if abs(roll - chaos_level) <= 2: return "BACKFIRE"
    return "WILD"

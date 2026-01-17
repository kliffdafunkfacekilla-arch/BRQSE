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
COMBAT_RULES = RULES.get("Combat_Rules", [])
if not COMBAT_RULES: COMBAT_RULES = RULES.get("combat_rules", [])

# --- WEAPON DB LOADING (Ported from mechanics.py) ---
def load_weapon_db():
    db = {}
    # Path relative to scripts/combat_engine.py
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../Data/weapons_and_armor.csv")
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            header = f.readline()
            for line in f:
                parts = line.strip().split(',')
                if len(parts) < 7: continue
                name = parts[0]
                tags = parts[6]
                
                dice = "1d4"
                if "DMG:" in tags:
                    for t in tags.split('|'):
                        if t.startswith("DMG:"):
                            sub = t.split(':')
                            if len(sub) > 1: dice = sub[1]
                            break
                db[name] = dice
    except: pass
    return db

WEAPON_DB = load_weapon_db()

def resolve_attack(attacker, defender):
    # 1. Roll (Opposed)
    # Attacker: d20 + Weapon Skill + Stat
    # Defender: d20 + Armor Skill + Stat
    
    # Resolve Stats
    atk_stat = attacker.weapon_data.get("attr", "Might")
    def_stat = defender.armor_data.get("attr", "Reflexes")
    
    # If char_engine didn't load weapon data (because json empty), defaults might be wrong.
    # We rely on get_roll_mod doing the heavy lifting if possible, 
    # but currently char_engine relies on weapon_data too.
    # For now, we trust attacker.get_roll_mod handles the stat lookup.
    
    atk_roll = random.randint(1, 20)
    atk_total = atk_roll + attacker.get_roll_mod(atk_stat)
    
    def_roll = random.randint(1, 20)
    def_total = def_roll + defender.get_roll_mod(def_stat)
    
    margin = atk_total - def_total
    
    # 2. Results
    outcome = "MISS"
    damage = 0
    desc = f"Missed! ({margin})"
    
    if margin == 0:
        return {"outcome": "THE CLASH", "margin": 0, "damage": 0, "desc": "CLASH TRIGGERED! (Tie)"}
    
    elif margin > 0:
        outcome = "HIT"
        # Calculate Damage
        # Try Weapon DB first (more reliable if JSON empty)
        w_name = attacker.weapon_name
        dice = WEAPON_DB.get(w_name, "1d4")
        
        # Roll Dice
        try:
            num, sides = map(int, dice.split('d'))
            base_dmg = sum(random.randint(1, sides) for _ in range(num))
        except: base_dmg = 1
        
        # Add Stat Mod (Default Might for now, or match weapon attr)
        stat_bonus = attacker.attributes.get(atk_stat, 0)
        damage = max(1, base_dmg + int(stat_bonus))
        
        desc = f"HIT! ({w_name}) Dmg: {damage}"

    return {
        "outcome": outcome,
        "margin": margin,
        "damage": damage,
        "desc": desc
    }

def resolve_clash_effect(winner_stat, winner, loser):
    # THE CLASH TABLE (User Rules)
    stat = winner_stat.upper()
    effect = "Staggered"
    
    if "MIGHT" in stat:
        effect += ", Pushed Back 1, Winner Steps Forward 1"
    elif "ENDURANCE" in stat:
        effect += ", Pushed Back 1"
    elif "FINESSE" in stat:
        effect += ", Disarmed"
    elif "REFLEX" in stat:
        effect += ", Positions Swapped"
    elif "KNOWLEDGE" in stat:
        effect += ", Winner Moves Beside Loser"
    elif "LOGIC" in stat:
        loser.current_hp -= 2
        effect += ", 2 HP Damage"
    elif "VITALITY" in stat:
        loser.apply_composure_damage(2)
        effect += ", 2 CMP Damage"
    elif "FORTITUDE" in stat:
        effect += ", Loser Moved Sideways, Winner Steps Forward"
    elif "AWARENESS" in stat:
        effect += ", Winner Side Steps, Loser Steps Opposite"
    elif "INTUITION" in stat:
        effect += ", Winner Moves Beside, Loser into Hazard"
    elif "CHARM" in stat:
        effect += ", Winner Side Steps, Loser Forward 2"
    elif "WILLPOWER" in stat:
        effect += ", Winner Moves Behind Loser"
    else:
        effect += ", Shoved"
        
    return effect

def resolve_channeling(chaos_level):
    roll = random.randint(1, 10)
    if roll == 1: return "MELTDOWN"
    if roll == chaos_level: return "SUCCESS"
    if abs(roll - chaos_level) <= 2: return "BACKFIRE"
    return "WILD"

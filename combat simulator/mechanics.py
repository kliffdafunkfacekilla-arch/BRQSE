import json
import os
import random

import sys
# Ensure we can import abilities module if it's in a subfolder relative to this script
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from abilities import engine_hooks

# --- CONSTANTS ---
STAT_BLOCK = ["Might", "Reflexes", "Endurance", "Vitality", "Fortitude", "Knowledge", "Logic", "Awareness", "Intuition", "Charm", "Willpower", "Finesse"]

class Combatant:
    def __init__(self, filepath):
        self.filepath = filepath
        self.data = self._load_data(filepath)
        
        self.name = self.data.get("Name", "Unknown")
        self.species = self.data.get("Species", "Unknown")
        
        self.stats = self.data.get("Stats", {})
        self.derived = self.data.get("Derived", {})
        self.skills = self.data.get("Skills", []) # List of strings "SkillName"
        self.traits = self.data.get("Traits", []) # List of strings "TraitName"
        self.powers = self.data.get("Powers", []) # List of strings "PowerName"
        self.inventory = self.data.get("Inventory", [])
        
        # Temp flags for status effects
        self.is_prone = False
        self.is_grappled = False
        self.is_blinded = False
        self.is_restrained = False
        self.is_stunned = False
        self.is_paralyzed = False
        self.is_poisoned = False
        self.is_frightened = False
        self.is_charmed = False
        self.is_deafened = False
        self.is_invisible = False
        self.is_confused = False
        self.is_berserk = False
        self.is_sanctuary = False
        self.taunted_by = None
        
        # Resources
        self.max_hp = self.derived.get("HP", 10)
        self.max_cmp = self.derived.get("CMP", 10)
        self.max_sp = self.derived.get("SP", 10)
        self.max_fp = self.derived.get("FP", 10)
        
        self.hp = self.max_hp
        self.cmp = self.max_cmp
        self.sp = self.max_sp
        self.fp = self.max_fp
        
        # Spatial State
        self.x = 0
        self.y = 0
        # Spatial State
        self.x = 0
        self.y = 0
        self.movement = self.derived.get("Speed", 0)
        self.movement_remaining = self.movement

    def _load_data(self, filepath):
        try:
            with open(filepath, 'r') as f: return json.load(f)
        except: return {}

    def roll_initiative(self):
        # Speed + d20
        spd = self.derived.get("Speed", 0)
        self.movement = spd # Ensure max movement is set
        self.initiative = spd + random.randint(1, 20)
        return self.initiative

    def get_stat(self, stat_name):
        return self.stats.get(stat_name, 0)

    def get_skill_rank(self, skill_name):
        # Simplified: If in list, Rank 1. Else 0.
        for s in self.skills:
            if skill_name in s: return 1 # Basic proficiency
        return 0

    def is_alive(self):
        return self.hp > 0

class CombatEngine:
    def __init__(self):
        self.combatants = []
        self.log = []
        self.clash_active = False
        self.clash_participants = (None, None) 
        self.clash_stat = None
        self.weapon_db = self._load_weapon_db()
        self.turn_order = []
        self.current_turn_idx = 0

    def _load_weapon_db(self):
        db = {}
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

    def add_combatant(self, combatant, x, y):
        combatant.x = x
        combatant.y = y
        self.combatants.append(combatant)

    def start_combat(self):
        for c in self.combatants: 
             c.roll_initiative()
             c.movement_remaining = c.movement # Reset at start
        self.combatants.sort(key=lambda c: c.initiative, reverse=True)
        self.turn_order = self.combatants
        self.current_turn_idx = 0
        return [f"Combat Started! {self.turn_order[0].name}'s Turn."]

    def get_active_char(self):
        if not self.turn_order: return None
        return self.turn_order[self.current_turn_idx]

    def end_turn(self):
        self.current_turn_idx = (self.current_turn_idx + 1) % len(self.turn_order)
        # Skip dead
        start = self.current_turn_idx
        while not self.turn_order[self.current_turn_idx].is_alive():
            self.current_turn_idx = (self.current_turn_idx + 1) % len(self.turn_order)
            if self.current_turn_idx == start: break # Everyone dead
        
        # Reset movement for new active char
        active = self.turn_order[self.current_turn_idx]
        active.movement_remaining = active.movement
        
        return [f"{active.name}'s Turn. (Speed: {active.movement_remaining})"]

    def execute_ai_turn(self, ai_char):
        """
        Execute a turn for an AI-controlled character.
        Returns action log.
        """
        log = [f"[AI] {ai_char.name} thinks..."]
        
        # Get AI template from data
        ai_template = ai_char.data.get("AI", "Aggressive")
        
        # Find targets (other living combatants)
        targets = [c for c in self.combatants if c.is_alive() and c != ai_char]
        if not targets:
            log.append(f"[AI] No targets found.")
            return log
        
        target = targets[0] # Simple: pick first target
        
        # Calculate distance
        dx = abs(ai_char.x - target.x)
        dy = abs(ai_char.y - target.y)
        dist_sq = max(dx, dy)
        
        if ai_template == "Aggressive":
            # Charge and attack
            if dist_sq > 1:
                # Move toward target
                move_x = ai_char.x + (1 if target.x > ai_char.x else (-1 if target.x < ai_char.x else 0))
                move_y = ai_char.y + (1 if target.y > ai_char.y else (-1 if target.y < ai_char.y else 0))
                ok, msg = self.move_char(ai_char, move_x, move_y)
                log.append(f"[AI] Move: {msg}")
                # Try again until in range or out of movement
                while ai_char.movement_remaining >= 5 and max(abs(ai_char.x - target.x), abs(ai_char.y - target.y)) > 1:
                    move_x = ai_char.x + (1 if target.x > ai_char.x else (-1 if target.x < ai_char.x else 0))
                    move_y = ai_char.y + (1 if target.y > ai_char.y else (-1 if target.y < ai_char.y else 0))
                    ok, msg = self.move_char(ai_char, move_x, move_y)
                    if not ok: break
            
            # Attack if adjacent
            if max(abs(ai_char.x - target.x), abs(ai_char.y - target.y)) <= 1:
                attack_log = self.attack_target(ai_char, target)
                log.extend(attack_log)
            else:
                log.append(f"[AI] Couldn't reach {target.name}.")
                
        elif ai_template == "Defensive":
            # Only attack if already adjacent
            if dist_sq <= 1:
                attack_log = self.attack_target(ai_char, target)
                log.extend(attack_log)
            else:
                log.append(f"[AI] Waiting (Defensive)")
                
        elif ai_template == "Ranged":
            # Stay at distance, attack (assuming ranged attack)
            if dist_sq <= 1:
                # Move away
                move_x = ai_char.x - (1 if target.x > ai_char.x else (-1 if target.x < ai_char.x else 0))
                move_y = ai_char.y - (1 if target.y > ai_char.y else (-1 if target.y < ai_char.y else 0))
                self.move_char(ai_char, move_x, move_y)
            log.append(f"[AI] Ranged Attack (Not fully impl)")
            
        elif ai_template == "Berserker":
            # Random movement + attack
            import random
            move_x = ai_char.x + random.choice([-1, 0, 1])
            move_y = ai_char.y + random.choice([-1, 0, 1])
            self.move_char(ai_char, move_x, move_y)
            if max(abs(ai_char.x - target.x), abs(ai_char.y - target.y)) <= 1:
                log.extend(self.attack_target(ai_char, target))
            else:
                log.append(f"[AI] Berserker flails wildly!")
        else:
            log.append(f"[AI] Unknown template: {ai_template}")
            
        return log

    def move_char(self, char, tx, ty):
        # Boundaries (Hardcoded 12x12 for now matching Arena)
        if not (0 <= tx < 12 and 0 <= ty < 12):
            return False, "Out of Bounds!"

        # Calculate distance
        dist = max(abs(char.x - tx), abs(char.y - ty)) * 5 # 5ft per square
        
        if dist > char.movement_remaining:
            return False, f"Not enough movement! ({char.movement_remaining} left)"
        
        # Check collision
        for c in self.combatants:
            if c.is_alive() and c != char and c.x == tx and c.y == ty:
                return False, "Blocked!"
                
        char.x = tx
        char.y = ty
        char.movement_remaining -= dist
        return True, f"Moved to {tx},{ty}. ({char.movement_remaining} left)"

    def attack_target(self, attacker, target):
        # Range Check
        reach = 1.5 # 5ft + diagonals
        # Allow reach override from context (can't easily do BEFORE effect loading...)
        # Chicken/Egg: We need to load effects to know reach, but we check range before rolling.
        # Solution: Load effects for "Passive" reach first? Or just allow attack if within expanded reach?
        # For now, let's keep basic check.
        
        dx = abs(attacker.x - target.x)
        dy = abs(attacker.y - target.y)
        dist_sq = max(dx, dy)
        
        # Check defaults
        if dist_sq > 1: # Default 5ft
             # Check if we have reach effect?
             # This requires pre-loading.
             pass

        # 1. Determine Stats
        atk_stat = "Might"
        atk_skill = "Weapon" 
        def_stat = "Reflexes"
        def_skill = "Dodge"
        
        # Roll
        atk_roll = random.randint(1, 20)
        atk_mod = attacker.get_stat(atk_stat) + attacker.get_skill_rank(atk_skill)
        
        # Hook Context
        ctx = {
            "attacker": attacker,
            "target": target,
            "engine": self,
            "log": [],
            "attack_roll": atk_roll + atk_mod, # Mutable
            "damage_type": "Physical",
            "auto_hit": False,
            "is_crit": False,
            "advantage": False,
            "disadvantage": False
        }
        
        # ON_ATTACK Hooks
        engine_hooks.apply_hooks(attacker, "ON_ATTACK", ctx)
        
        # Re-calc total based on context changes
        if ctx["advantage"] and not ctx["disadvantage"]:
             r2 = random.randint(1, 20)
             atk_roll = max(atk_roll, r2)
             # Re-calc base
             ctx["attack_roll"] = atk_roll + atk_mod 
             # Note: Context modifiers to "attack_roll" (like +2) might be lost if we just reset it here.
             # Better: track bonus separate from roll. But for now, let's just assume simple flow.
             
        atk_total = ctx["attack_roll"]

        
        def_roll = random.randint(1, 20)
        def_mod = target.get_stat(def_stat) + target.get_skill_rank(def_skill)
        def_total = def_roll + def_mod
        
        margin = atk_total - def_total
        
        log = [f"{attacker.name} attacks {target.name}!"]
        if ctx["log"]: log.extend(ctx["log"])
        
        log.append(f"ATK: {atk_total} ({atk_roll}+{atk_mod}) vs DEF: {def_total} ({def_roll}+{def_mod})")
        
        # Crit check
        crit_thresh = ctx.get("crit_threshold", 20)
        if atk_roll >= crit_thresh:
            ctx["is_crit"] = True
            log.append(f"CRITICAL HIT! (Rolled {atk_roll})")

        margin = atk_total - def_total
        if ctx["auto_hit"]: margin = max(1, margin)

        
        if margin == 0:
            self.clash_active = True
            self.clash_participants = (attacker, target)
            self.clash_stat = atk_stat 
            log.append("--- CLASH INITIATED! ---")
            log.append("CLASH START")
            return log
            
        elif margin > 0:
            dmg, w_name = self.calc_damage(attacker, margin)
            
            # Apply HIT Effects
            ctx["incoming_damage"] = dmg
            engine_hooks.apply_hooks(attacker, "ON_HIT", ctx)
            engine_hooks.apply_hooks(target, "ON_DEFEND", ctx) # Apply defenses
            
            final_dmg = max(0, ctx["incoming_damage"])
            target.hp -= final_dmg
            
            if target.hp < 0: target.hp = 0
            log.append(f"HIT! ({w_name}) Dmg: {final_dmg}. {target.name} HP: {target.hp}")
            if ctx["log"]: log.extend(ctx["log"])
            
        else:
            log.append("MISS!")
            
        if "log" in ctx: ctx["log"].extend(ctx["log"]) # This was redundant in original code, fixing
            
        else:
            log.append("MISS!")
            
        return log

    def activate_ability(self, char, ability_name, target=None):
        destination_name = target.name if target else "Self/Area"
        log = [f"{char.name} uses {ability_name} on {destination_name}!"]
        
        # Context
        ctx = {
            "attacker": char,
            "engine": self,
            "log": [],
            "target": target # Now optionally passed in
        }
        
        try:
            # Lookup Data
            data_item = engine_hooks.get_ability_data(ability_name)
            
            if data_item:
                # 1. Check Cost
                cost_str = data_item.get("Cost")
                if cost_str:
                    # Parse "5 SP", "10 FP" etc
                    # Simple split
                    parts = cost_str.split()
                    if len(parts) >= 2:
                        val = int(parts[0])
                        res = parts[1].upper()
                        
                        curr = 0
                        if res == "SP": curr = char.sp
                        elif res == "FP": curr = char.fp
                        elif res == "CMP": curr = char.cmp
                        elif res == "HP": curr = char.hp
                        
                        if curr < val:
                            log.append(f"Not enough {res}! Need {val}.")
                            return log
                            
                        # Consume
                        if res == "SP": char.sp -= val
                        elif res == "FP": char.fp -= val
                        elif res == "CMP": char.cmp -= val
                        elif res == "HP": char.hp -= val
                        log.append(f"Consumed {val} {res}")

                # 2. Resolve Effect
                effect_str = data_item.get("Effect") or data_item.get("Description")
                if effect_str:
                    from abilities.effects_registry import registry
                    handled = registry.resolve(effect_str, ctx)
                    if not handled: log.append("No effect resolved (or unimplemented).")
                else:
                    log.append("No Effect Description.")
            else:
                log.append(f"Ability data not found for '{ability_name}'.")

        except Exception as e:
            log.append(f"FAILED: {e}")
            
        log.extend(ctx["log"])
        return log

    def calc_damage(self, attacker, margin):
        dice = "1d4"; w_name = "Unarmed"
        for item in attacker.inventory:
            if item in self.weapon_db:
                dice = self.weapon_db[item]; w_name = item
                break
        
        try:
            num, sides = map(int, dice.split('d'))
            roll = sum(random.randint(1, sides) for _ in range(num))
        except: roll = 1
            
        bonus = attacker.get_stat("Might")
        return max(1, roll + bonus), w_name

    def resolve_clash(self, choice):
        p1, p2 = self.clash_participants
        if not p1 or not p2: return ["Clash Error"]
        stat = self.clash_stat 
        
        r1 = random.randint(1, 20) + p1.get_stat(stat)
        r2 = random.randint(1, 20) + p2.get_stat(stat)
        
        log = [f"CLASH ROLL ({choice}): {p1.name}({r1}) vs {p2.name}({r2})"]
        
        winner = p1 if r1 >= r2 else p2
        loser = p2 if winner == p1 else p1
        
        effect_desc = "Impact"
        s_key = stat.lower()
        
        # Spatial helpers
        dx = loser.x - winner.x
        dy = loser.y - winner.y
        # Normalize to 1 (direction)
        dir_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
        dir_y = 1 if dy > 0 else (-1 if dy < 0 else 0)
        
        if "might" in s_key or "endurance" in s_key:
            # Push Back 1
            loser.x += dir_x
            loser.y += dir_y
            effect_desc = "Pushed Back"
            if "might" in s_key: # Winner Follows
                winner.x += dir_x
                winner.y += dir_y
                effect_desc += " & Follow Up"
                
        elif "finesse" in s_key:
            effect_desc = "Disarmed (Status Applied)"
            
        elif "reflex" in s_key:
            # Swap
            temp_x, temp_y = winner.x, winner.y
            winner.x, winner.y = loser.x, loser.y
            loser.x, loser.y = temp_x, temp_y
            effect_desc = "Positions Swapped"
            
        elif "knowledge" in s_key or "intuition" in s_key:
            # Move Beside (Flank essentially)
            # Try to move winner to valid adjacent spot? 
            # Simplified: Winner moves to x+dir_y, y+dir_x (Rotated 90)
            winner.x += dir_y
            winner.y += dir_x
            effect_desc = "Flanking Position"
            
        elif "logic" in s_key or "vitality" in s_key:
             dmg = 2
             if "logic" in s_key: loser.hp -= dmg; effect_desc = "2 HP Dmg"
             else: loser.cmp -= dmg; effect_desc = "2 CMP Dmg"
             
        elif "fortitude" in s_key:
            # Loser sideways, Winner forward
             loser.x += dir_y
             loser.y += dir_x
             winner.x += dir_x
             winner.y += dir_y
             effect_desc = "Bulwark Shove"
             
        elif "charm" in s_key:
             # Winner Side Step, Loser Stumble Forward 2
             winner.x += dir_y
             winner.y += dir_x
             loser.x += (dir_x * 2)
             loser.y += (dir_y * 2)
             effect_desc = "Matador Feint"
        
        elif "willpower" in s_key:
             # Move Behind
             winner.x = loser.x + dir_x
             winner.y = loser.y + dir_y
             effect_desc = "Domination (Behind)"
             
        else:
             effect_desc = "Shoved"

        log.append(f"{winner.name} WINS! {effect_desc}")
        
        self.clash_active = False
        self.clash_participants = (None, None)
        return log

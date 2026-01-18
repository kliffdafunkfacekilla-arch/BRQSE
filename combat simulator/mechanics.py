
import json
import os
import random
import math
import sys

# Add local directory to path for imports
sys.path.append(os.path.dirname(__file__))

# Try to import Engines
try:
    from ai_engine import AIDecisionEngine
except ImportError:
    AIDecisionEngine = None
    
try:
    from inventory_engine import Inventory
except ImportError:
    Inventory = None

try:
    from progression_engine import ProgressionEngine
except ImportError:
    ProgressionEngine = None
    print("[Mechanics] Warning: Could not import Inventory")

# Ensure we can import abilities module if it's in a subfolder relative to this script
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from abilities import engine_hooks

# --- CONSTANTS ---
STAT_BLOCK = ["Might", "Reflexes", "Endurance", "Vitality", "Fortitude", "Knowledge", "Logic", "Awareness", "Intuition", "Charm", "Willpower", "Finesse"]

class Combatant:
    def __init__(self, filepath=None, data=None):
        self.filepath = filepath
        if data:
            self.data = data
        else:
            self.data = self._load_data(filepath)
        
        self.name = self.data.get("Name", "Unknown")
        self.species = self.data.get("Species", "Unknown")
        
        self.stats = self.data.get("Stats", {})
        self.derived = self.data.get("Derived", {})
        
        # Skills: Normalize to Dict {Name: Rank}
        raw_skills = self.data.get("Skills", [])
        if isinstance(raw_skills, list):
            self.skills = {s: 1 for s in raw_skills}
        else:
            self.skills = raw_skills # Assume dict
            
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
        
        # FIX: Critical states
        self.is_dead = False          # True = permanently dead until revived
        
        # INVENTORY SYSTEM
        self.inventory = Inventory() if Inventory else None
        self._init_loadout()
        
        # PROGRESSION SYSTEM (Auto-Unlock Talents)
        if ProgressionEngine:
            pe = ProgressionEngine()
            new_traits = pe.check_unlocks(self)
            if new_traits:
                # Log or just accept? mechanics doesn't log on init easily.
                # Just keeping them in self.traits is enough.
                pass
        
    def _init_loadout(self):
        """Auto-equip items from data if Inventory exists"""
        if not self.inventory: return
        
        # Check 'Gear' or 'Weapons' list in data
        # Assuming simple list of strings for now
        gear = self.data.get("Gear", []) + self.data.get("Weapons", []) + self.data.get("Armor", [])
        
        for item_name in gear:
            # Simple heuristic: try to equip everything
            # The inventory engine handles lookup
            self.inventory.equip(item_name) # Will slot into Armor/MainHand automatically

        self.is_broken = False        # True = CMP at 0 (mental break)
        self.is_exhausted = False     # True = SP at 0 (physical exhaustion)
        self.is_drained = False       # True = FP at 0 (focus depleted)
        
        # Duration-based effects: list of {name, duration, on_expire}
        # duration = rounds remaining (-1 = permanent until cleared)
        self.active_effects = []
        
        # Resources
        self.max_hp = self.derived.get("HP", 10)
        self.max_cmp = self.derived.get("CMP", 10)
        self.max_sp = self.derived.get("SP", 10)
        self.max_fp = self.derived.get("FP", 10)
        
        self.hp = self.max_hp
        self.cmp = self.max_cmp
        self.sp = self.max_sp
        self.fp = self.max_fp
        
        self.base_movement = self.derived.get("Speed", 30) // 5
        self.movement = self.base_movement
        self.movement_remaining = self.movement
        
        # Action Economy Flags
        self.action_used = False
        self.bonus_action_used = False
        self.reaction_used = False
        
        # Position
        self.x = 0
        self.y = 0
        self.initiative = 0
        self.team = "Neutral" # Default team
        
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
        return self.stats.get(stat_name, 10) # Default to 10 (Mod +0)

    def get_stat_modifier(self, stat_name):
        """
        Returns D&D 5e style modifier: (Score - 10) // 2
        e.g. 10 -> +0, 12 -> +1, 16 -> +3, 8 -> -1
        """
        score = self.get_stat(stat_name)
        return (score - 10) // 2

    def get_skill_rank(self, skill_name):
        return self.skills.get(skill_name, 0)

    def is_alive(self):
        # FIX: Also check is_dead flag
        return self.hp > 0 and not self.is_dead
    
    def take_damage(self, amount):
        """
        Apply damage with death checking.
        Returns actual damage dealt.
        """
        if self.is_dead:
            return 0  # Can't damage a corpse
        
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.is_dead = True
        return amount
    
    def heal(self, amount):
        """
        Heal HP. FIX: Cannot heal if dead.
        Returns actual healing applied.
        """
        if self.is_dead:
            return 0  # Need resurrection, not healing
        
        old_hp = self.hp
        self.hp = min(self.hp + amount, self.max_hp)
        return self.hp - old_hp
    
    def revive(self, hp_amount=1):
        """
        Revive a dead character.
        """
        if self.is_dead:
            self.is_dead = False
            self.hp = min(hp_amount, self.max_hp)
            return True
        return False
    
    def check_resources(self):
        """
        Check resource levels and set broken states.
        Call this after modifying CMP/SP/FP.
        """
        # CMP = Mental break
        if self.cmp <= 0:
            self.cmp = 0
            self.is_broken = True
        elif self.cmp > 0:
            self.is_broken = False
            
        # SP = Exhaustion
        if self.sp <= 0:
            self.sp = 0
            self.is_exhausted = True
        elif self.sp > 0:
            self.is_exhausted = False
            
        # FP = Drained
        if self.fp <= 0:
            self.fp = 0
            self.is_drained = True
        elif self.fp > 0:
            self.is_drained = False

    def roll_save(self, save_type):
        """
        Roll a saving throw.
        save_type: 'Endurance' (tank), 'Reflex' (dodge), 'Fortitude' (resist), 
                   'Willpower' (mental), 'Intuition' (see through)
        Returns: (roll_total, roll_natural)
        """
        stat_map = {
            "Endurance": "Endurance",
            "Reflex": "Reflexes",
            "Fortitude": "Fortitude",
            "Willpower": "Willpower",
            "Intuition": "Intuition"
        }
        stat = stat_map.get(save_type, save_type)
        nat_roll = random.randint(1, 20)
        mod = self.get_stat_modifier(stat)
        return nat_roll + mod, nat_roll

    def apply_effect(self, effect_name, duration=1, on_expire=None):
        """
        Apply a timed effect.
        effect_name: e.g. 'Frightened', 'Poisoned'
        duration: rounds (-1 = permanent)
        on_expire: optional callback or flag name to clear
        
        FIX: Now refreshes duration if effect already exists (no stacking).
        """
        flag = f"is_{effect_name.lower()}"
        on_exp = on_expire or flag
        
        # Check if effect already exists - refresh duration instead of stacking
        for eff in self.active_effects:
            if eff["name"] == effect_name:
                # Refresh: take the longer duration
                eff["duration"] = max(eff["duration"], duration)
                return
        
        # New effect
        self.active_effects.append({
            "name": effect_name,
            "duration": duration,
            "on_expire": on_exp
        })
        # Also set the flag immediately
        if hasattr(self, flag):
            setattr(self, flag, True)

    def tick_effects(self):
        """
        Called at start/end of turn. Decrements durations and clears expired.
        Returns list of expired effect names.
        """
        expired = []
        remaining = []
        
        for eff in self.active_effects:
            if eff["duration"] == -1:
                remaining.append(eff) # Permanent
                continue
                
            eff["duration"] -= 1
            if eff["duration"] <= 0:
                # Expired - clear the flag
                flag = eff.get("on_expire")
                if flag and hasattr(self, flag):
                    setattr(self, flag, False)
                expired.append(eff["name"])
            else:
                remaining.append(eff)
        
        self.active_effects = remaining
        return expired

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
        self.log = []
        self.walls = set() # (x,y) tuples
        self.terrain = [] # Dictionaries {x,y,type,active}
        self.ai = AIDecisionEngine() if AIDecisionEngine else None

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
             c.action_used = False
             c.bonus_action_used = False
        self.combatants.sort(key=lambda c: c.initiative, reverse=True)
        self.turn_order = self.combatants
        self.current_turn_idx = 0
        return [f"Combat Started! {self.turn_order[0].name}'s Turn."]

    def get_active_char(self):
        if not self.turn_order: return None
        return self.turn_order[self.current_turn_idx]

    def start_turn(self, combatant):
        """
        Called when a combatant's turn begins.
        Returns False if turn is skipped (Stunned/Paralyzed), True otherwise.
        """
        log = []
        
        # 1. Tick Start-of-Turn Effects (DoTs)
        # Assuming some effects are active
        
        # 2. Check Conditions
        if combatant.is_stunned:
             log.append(f"{combatant.name} is STUNNED and skips their turn!")
             return False, log
             
        if combatant.is_paralyzed:
             log.append(f"{combatant.name} is PARALYZED and skips their turn!")
             return False, log
             
        return True, log

    def end_turn(self):
        # Tick effects on current character before ending
        active = self.turn_order[self.current_turn_idx]
        
        # Tick End-of-Turn Effects (Buffs)
        expired = active.tick_effects() # Renamed/Modified logic below? 
        # For now, keep tick_effects as general ticker
        
        log = []
        if expired:
            log.append(f"Effects expired on {active.name}: {', '.join(expired)}")
        
        self.current_turn_idx = (self.current_turn_idx + 1) % len(self.turn_order)
        # Skip dead
        start = self.current_turn_idx
        while not self.turn_order[self.current_turn_idx].is_alive():
            self.current_turn_idx = (self.current_turn_idx + 1) % len(self.turn_order)
            if self.current_turn_idx == start: break # Everyone dead
        
        # Reset movement for new active char
        new_active = self.turn_order[self.current_turn_idx]
        new_active.movement_remaining = new_active.movement
        # Reset Actions
        new_active.action_used = False
        new_active.bonus_action_used = False
        new_active.reaction_used = False
        
        # TRIGGER START TURN logic for new active
        can_act, start_log = self.start_turn(new_active)
        log.extend(start_log)
        
        if not can_act:
             # Recursively end turn if skipped? 
             # Or just return log and let caller see they can't act.
             # Better: automatically skip to next.
             # CAUTION: Recursive loop if everyone stunning.
             # For safety, just set their actions to used or invalid?
             # Simple approach: If not can_act, we assume the UI/AI loop handles it.
             # But since 'end_turn' is called by UI button...
             # If I skip here, who updates UI?
             # Let's just return the log saying they are stunned. 
             # The UI should disable buttons if 'is_stunned'.
             # Or better, we auto-end their turn? 
             pass

        log.append(f"{new_active.name}'s Turn. (Speed: {new_active.movement_remaining})")
        return log

    def execute_ai_turn(self, ai_char):
        """
        Execute a turn for an AI-controlled character.
        Returns action log.
        """
        # USE NEW AI ENGINE IF AVAILABLE
        if self.ai:
            return self.ai.evaluate_turn(ai_char, self)
            
        # --- FALLBACK LEGACY LOGIC ---
        log = [f"[AI] {ai_char.name} thinks (Legacy)..."]
        
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
        
        if (tx, ty) in self.walls:
            return False, "Blocked by Wall!"
                
        char.x = tx
        char.y = ty
        char.movement_remaining -= dist
        return True, f"Moved to {tx},{ty}. ({char.movement_remaining} left)"

    def attack_target(self, attacker, target):
        # FIX #4: Proper Range Check
        dx = abs(attacker.x - target.x)
        dy = abs(attacker.y - target.y)
        dist_sq = max(dx, dy)  # Chebyshev distance in squares
        
        # Default melee reach is 1 square (5ft)
        # Check for reach-extending effects
        reach = 1
        for eff in attacker.active_effects:
            if "reach" in eff["name"].lower():
                reach = 2  # 10ft reach
        
        if dist_sq > reach:
            return [f"Target out of range! (Distance: {dist_sq * 5}ft, Reach: {reach * 5}ft)"]

        # Action Check
        if attacker.action_used:
            return [f"{attacker.name} has already used their Action!"]

        log = [f"{attacker.name} attacks {target.name}!"]
        
        # Consume Action
        attacker.action_used = True

        # 1. Determine Damage Dice & Type
        dmg_dice = "1d4"
        damage_type = "Bludgeoning"
        weapon_tags = {}
        
        if attacker.inventory:
            dmg_dice, damage_type, weapon_tags = attacker.inventory.get_weapon_stats()
            
        # Parse Dice (e.g. "2d6")
        if "d" in dmg_dice:
            num, sides = map(int, dmg_dice.split("d"))
            damage = sum(random.randint(1, sides) for _ in range(num))
        else:
            damage = int(dmg_dice)
            
        # 2. To Hit Calculation (Resource Clash)
        # Attacker uses Might/Finesse vs Defender's Armor Stat
        def_stat_name = "Reflexes"
        if target.inventory: 
            def_stat_name = target.inventory.get_defense_stat()
            
        # USE MODIFIERS
        hit_mod = attacker.get_stat_modifier("Might") 
        # TODO: Support Finesse weapons using Finesse/Agility?
        
        hit_score = hit_mod + random.randint(1, 20)
        
        # Defender uses AC (Base 10 + Dex/Armor Mod)
        # In D&D: AC = 10 + Mod. 
        # Here: Armor might provide base AC? 
        # For now, let's use: Def_Score = 10 + Def_Stat_Mod
        
        def_mod = target.get_stat_modifier(def_stat_name)
        def_target = 10 + def_mod
        
        # If armor provides bonus? 
        # Currently Armor Item adds "Effects". 
        # Let's assume Active Defense Roll for now (Opposed Roll) as implemented before?
        # User requested "Active Defense".
        # So Defender Rolls: d20 + Mod
        
        def_roll = def_mod + random.randint(1, 20)
        
        # LOGIC: Check Hit
        if hit_score >= def_roll:
            # HIT
             target.take_damage(damage) # Simplified for now, removed damage_type, attacker
             log.append(f"Attack HIT! ({hit_score} vs {def_roll}). Dealt {damage} {damage_type}.")
        else:
             log.append(f"Attack MISSED. ({hit_score} vs {def_roll})")
             
        return log

    def create_wall(self, x, y):
        """Creates a blocking wall at x,y"""
        if 0 <= x < 12 and 0 <= y < 12:
            self.walls.add((x, y))
            return True
        return False

    def spawn_minion(self, name, x, y, team="Enemy"):
        """Spawns a temporary combatant"""
        # Minimal template
        data = {
            "Name": name,
            "Species": "Construct",
            "Stats": {"Might": 10, "Reflexes": 10, "Endurance": 10, "Speed": 30},
            "Derived": {"HP": 20, "CMP": 10, "SP": 10, "FP": 10},
            "Skills": [],
            "Traits": [],
            "Powers": [],
            "AI": "Aggressive"
        }
        
        minion = Combatant(filepath=None, data=data)
        minion.name = f"{name}_{len(self.combatants)}" # Unique-ish ID
        self.add_combatant(minion, x, y)
        self.turn_order.append(minion) # Add to turn order immediately
        return minion

    def cast_power(self, caster, target, power_data, save_type="Willpower"):
        """
        Cast a power/spell with opposed roll saving throw.
        caster: The one casting
        target: The one being affected
        power_data: dict with 'Name', 'Stat', 'Effect', etc.
        save_type: How the target chooses to resist (Endurance/Reflex/Fortitude/Willpower/Intuition)
        """
        power_name = power_data.get("Name", "Unknown Power")
        power_stat = power_data.get("Stat", "Knowledge") # Default casting stat
        effect_desc = power_data.get("Effect", "")
        
        log = [f"{caster.name} casts {power_name} on {target.name}!"]
        
        # Caster rolls d20 + Power Stat (Mod)
        caster_roll = random.randint(1, 20)
        caster_mod = caster.get_stat_modifier(power_stat)
        caster_total = caster_roll + caster_mod
        log.append(f"Caster Roll: {caster_total} ({caster_roll}+{caster_mod} {power_stat})")
        
        # Target rolls d20 + Chosen Save Stat
        target_total, target_nat = target.roll_save(save_type)
        target_mod = target_total - target_nat
        log.append(f"Save Roll ({save_type}): {target_total} ({target_nat}+{target_mod})")
        
        # Context for effects
        ctx = {
            "attacker": caster,
            "target": target,
            "engine": self,
            "log": [],
            "caster_total": caster_total,
            "save_total": target_total,
            "save_success": target_total >= caster_total
        }
        
        if target_total >= caster_total:
            log.append(f"{target.name} resists! (Save Success)")
            # Some effects still apply on save (half damage, etc.)
            ctx["save_success"] = True
        else:
            log.append(f"{target.name} fails to resist!")
            ctx["save_success"] = False
            # Apply full effect
            from abilities.effects_registry import registry
            registry.resolve(effect_desc, ctx)
        
        if ctx["log"]:
            log.extend(ctx["log"])
            
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
        
        # USE MODIFIERS
        r1 = random.randint(1, 20) + p1.get_stat_modifier(stat)
        r2 = random.randint(1, 20) + p2.get_stat_modifier(stat)
        
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

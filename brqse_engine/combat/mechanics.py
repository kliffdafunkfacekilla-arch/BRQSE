
import json
import os
import random
import math
import sys

# Add local directory to path for imports
sys.path.append(os.path.dirname(__file__))

# Try to import Engines
try:
    from .ai_engine import AIDecisionEngine
except ImportError:
    AIDecisionEngine = None
    
try:
    from brqse_engine.systems.inventory import Inventory
except ImportError:
    Inventory = None

try:
    from brqse_engine.systems.progression import ProgressionEngine
except ImportError:
    ProgressionEngine = None
    print("[Mechanics] Warning: Could not import Inventory")

# Ensure we can import abilities module if it's in a subfolder relative to this script
# sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from brqse_engine.abilities import engine_hooks

try:
    from brqse_engine.core.constants import Stats, Conditions
    from brqse_engine.core.status_manager import StatusManager
except ImportError as e:
    print(f"[Mechanics] Warning: Could not import Constants/StatusManager: {e}")

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
        
        # Initialize Inventory Manager
        # FIX: Ensure we use the class, not a raw list
        if Inventory:
            self.inventory = Inventory()
            inv_data = self.data.get("Inventory", [])
            if isinstance(inv_data, list):
                for item_name in inv_data:
                    self.inventory.equip(item_name)
        else:
            self.inventory = None
            
        self.xp = self.data.get("XP", 0) # Load XP, default 0
        
        # STATUS MANAGER
        if 'StatusManager' in globals():
            self.status = StatusManager(self)
        else:
            self.status = None
            
        self.taunted_by = None
        self.charmed_by = None # Reference to the entity that charmed this combatant
        
        # FIX: Critical states
        self.is_dead = False          # True = permanently dead until revived
        
        # INVENTORY SYSTEM
        self.inventory = Inventory() if Inventory else None
        self._init_loadout()

        self.ai = None # Placeholder for AI Logic
        
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
        gear = self.data.get("Inventory", []) + self.data.get("Gear", []) + self.data.get("Weapons", []) + self.data.get("Armor", [])
        
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
        # Resources (Formula: Derived_Stats.csv)
        def get_score(name): return self.data.get("Stats", {}).get(name, 10) # default to 10 if missing
        
        self.max_hp = 10 + get_score("Might") + get_score("Reflexes") + get_score("Vitality")
        self.max_cmp = 10 + get_score("Willpower") + get_score("Logic") + get_score("Awareness")
        self.max_sp = get_score("Endurance") + get_score("Finesse") + get_score("Fortitude")
        self.max_fp = get_score("Knowledge") + get_score("Charm") + get_score("Intuition")

        # Override with JSON Derived if explicit override logic exists? 
        # User requested "formulas for calculations", implying we should trust formula.
        # But let's respect "Current" vs "Max". Max should be formula. 
        # If JSON has higher/custom Max, that's tricky. For now, Formula is source of truth.
        
        self.hp = self.max_hp # Reset to max on load? Or load current?
        # Typically we load current. But for this simulation, we reset.
        
        self.cmp = self.max_cmp
        self.sp = self.max_sp
        self.fp = self.max_fp
        
        # Speed: Vitality + Willpower -> Round nearest 5
        raw_speed = get_score("Vitality") + get_score("Willpower")
        self.base_movement = int(5 * round(raw_speed / 5))
        if self.base_movement < 5: self.base_movement = 5
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

    def save_state(self):
        """Saves current stats/skills/xp back to the JSON file."""
        if not self.filepath: return
        
        # Update internal data dict structure
        self.data["Stats"] = self.stats
        self.data["Skills"] = self.skills
        self.data["Traits"] = self.traits
        self.data["XP"] = self.xp
        # Derived stats usually don't need saving if they are calc'd on load, 
        # but if you have permanent modifiers, save them here.
        
        try:
            with open(self.filepath, 'w') as f:
                json.dump(self.data, f, indent=4)
            print(f"Character saved: {self.filepath}")
        except Exception as e:
            print(f"Error saving character: {e}")

    def roll_initiative(self):
        # Use Alertness (Intuition + Reflexes) from CSV
        from brqse_engine.core.constants import Stats # Local import if needed or use existing
        
        # We assume self.get_stat handles strings or constants if mapped.
        # But mechanics.py uses strings primarily.
        intuit = self.get_stat("Intuition")
        reflex = self.get_stat("Reflexes")
        alertness = intuit + reflex
        
        # BURT'S UPDATE: Check for Talent Flags
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        
        if getattr(self, "initiative_advantage", False):
            roll = max(roll1, roll2)
        else:
            roll = roll1
            
        bonus = getattr(self, "initiative_bonus", 0)
        
        self.initiative = alertness + roll + bonus
        return self.initiative

    def get_attack_range(self):
        """
        Calculates range based on equipped weapon + tags.
        """
        base_range = 5 # Default melee
        
        # Check equipped weapon tags (assuming you have an 'equipped_weapon' dict or object)
        # If your system is simple, maybe it's just in self.weapon_data
        
        # Mock weapon data access if not present
        wep = getattr(self, "weapon_data", {})
        tags = wep.get("tags", set())
        
        # Handle "Reach"
        if "Reach" in tags:
            base_range += 5
            
        # Handle "Thrown" (if we are throwing it)
        # For simplicity, if it has 'Thrown', we use the thrown range provided in data
        # or default to 30ft.
        if "Thrown" in tags:
            base_range = max(base_range, 30) 
            
        return base_range

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

    # --- PROPERTIES FOR BACKWARD COMPATIBILITY ---
    def _get_status(self, condition):
        return self.status.has(condition) if self.status else False
    def _set_status(self, condition, val):
        if self.status:
            if val: self.status.add_condition(condition)
            else: self.status.remove_condition(condition)

    @property
    def is_prone(self): return self._get_status(Conditions.PRONE)
    @is_prone.setter
    def is_prone(self, val): self._set_status(Conditions.PRONE, val)

    @property
    def is_grappled(self): return self._get_status(Conditions.GRAPPLED)
    @is_grappled.setter
    def is_grappled(self, val): self._set_status(Conditions.GRAPPLED, val)

    @property
    def is_blinded(self): return self._get_status(Conditions.BLINDED)
    @is_blinded.setter
    def is_blinded(self, val): self._set_status(Conditions.BLINDED, val)

    @property
    def is_restrained(self): return self._get_status(Conditions.RESTRAINED)
    @is_restrained.setter
    def is_restrained(self, val): self._set_status(Conditions.RESTRAINED, val)

    @property
    def is_stunned(self): return self._get_status(Conditions.STUNNED)
    @is_stunned.setter
    def is_stunned(self, val): self._set_status(Conditions.STUNNED, val)

    @property
    def is_paralyzed(self): return self._get_status(Conditions.PARALYZED)
    @is_paralyzed.setter
    def is_paralyzed(self, val): self._set_status(Conditions.PARALYZED, val)

    @property
    def is_poisoned(self): return self._get_status(Conditions.POISONED)
    @is_poisoned.setter
    def is_poisoned(self, val): self._set_status(Conditions.POISONED, val)

    @property
    def is_frightened(self): return self._get_status(Conditions.FRIGHTENED)
    @is_frightened.setter
    def is_frightened(self, val): self._set_status(Conditions.FRIGHTENED, val)

    @property
    def is_charmed(self): return self._get_status(Conditions.CHARMED)
    @is_charmed.setter
    def is_charmed(self, val): self._set_status(Conditions.CHARMED, val)

    @property
    def is_deafened(self): return self._get_status(Conditions.DEAFENED)
    @is_deafened.setter
    def is_deafened(self, val): self._set_status(Conditions.DEAFENED, val)

    @property
    def is_invisible(self): return self._get_status(Conditions.INVISIBLE)
    @is_invisible.setter
    def is_invisible(self, val): self._set_status(Conditions.INVISIBLE, val)

    @property
    def is_confused(self): return self._get_status(Conditions.CONFUSED)
    @is_confused.setter
    def is_confused(self, val): self._set_status(Conditions.CONFUSED, val)

    @property
    def is_berserk(self): return self._get_status(Conditions.BERSERK)
    @is_berserk.setter
    def is_berserk(self, val): self._set_status(Conditions.BERSERK, val)
    
    @property
    def is_staggered(self): return self._get_status(Conditions.STAGGERED)
    @is_staggered.setter
    def is_staggered(self, val): self._set_status(Conditions.STAGGERED, val)

    @property
    def is_burning(self): return self._get_status(Conditions.BURNING)
    @is_burning.setter
    def is_burning(self, val): self._set_status(Conditions.BURNING, val)

    @property
    def is_bleeding(self): return self._get_status(Conditions.BLEEDING)
    @is_bleeding.setter
    def is_bleeding(self, val): self._set_status(Conditions.BLEEDING, val)

    @property
    def is_frozen(self): return self._get_status(Conditions.FROZEN)
    @is_frozen.setter
    def is_frozen(self, val): self._set_status(Conditions.FROZEN, val)

    @property
    def is_sanctuary(self): return self._get_status(Conditions.SANCTUARY)
    @is_sanctuary.setter
    def is_sanctuary(self, val): self._set_status(Conditions.SANCTUARY, val)


    def apply_effect(self, effect_name, duration=1, on_expire=None):
        """
        Apply a timed effect via StatusManager.
        """
        if self.status:
            self.status.add_timed_effect(effect_name, duration, on_expire)

    def tick_effects(self):
        """
        Delegates to StatusManager.tick()
        """
        if self.status:
            return self.status.tick()
        return []

class CombatEngine:
    def __init__(self, cols=12, rows=12):
        self.combatants = []
        self.turn_order = []
        self.current_turn_index = 0
        self.round_counter = 1
        
        # Map
        self.cols = cols
        self.rows = rows
        self.walls = set()
        self.hazards = [] # <--- BURT'S UPDATE: Add this list!
        self.aoe_templates = []
        
        self.ai = None # Placeholder for AI Engine
        self.log_callback = None
        
        # Clash State
        self.clash_active = False
        self.clash_participants = (None, None)
        self.clash_stat = None
        
    def create_wall(self, x, y):
        """Creates a wall at the specified coordinates."""
        if 0 <= x < self.cols and 0 <= y < self.rows:
            self.walls.add((x, y))
            
    def tick_hazards(self):
        """
        Call this at end of round to clean up expired zones.
        """
        active = []
        for h in self.hazards:
            h["duration"] -= 1
            if h["duration"] > 0:
                active.append(h)
        self.hazards = active

    def log(self, message):
        """Logs a message using the callback if available."""
        if self.log_callback:
            self.log_callback(message)
        
        self.clash_active = False
        self.clash_participants = (None, None) 
        self.clash_stat = None
        self.weapon_db = self._load_weapon_db()
        self.ai = AIDecisionEngine() if AIDecisionEngine else None

    def _load_weapon_db(self):
        db = {}
        # Path relative to brqse_engine/combat/mechanics.py -> ../../Data
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../Data/weapons_and_armor.csv")
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

    def attack_target(self, attacker, target):
        # 1. Check Range
        r_dist = max(abs(attacker.x - target.x), abs(attacker.y - target.y)) * 5
        max_reach = attacker.get_attack_range()
        
        if r_dist > max_reach:
            return f"Out of Range! (Target: {r_dist}ft, Reach: {max_reach}ft)"

        # 2. Resolve Finesse (Stat Swapping)
        # Check for Finesse tag
        wep = getattr(attacker, "weapon_data", {})
        tags = wep.get("tags", set())
        
        stat_used = "Might" # Default
        if "Finesse" in tags:
            # Use better of Might vs Reflexes
            might = attacker.get_stat("Might")
            ref = attacker.get_stat("Reflexes")
            if ref > might:
                stat_used = "Reflexes"
        
        # Calculate Chance to Hit
        # 1d20 + Stat + Tier vs Target Reflex
        # Tier logic? Assume Tier 1 for now or get from weapon (TODO)
        roll = random.randint(1, 20)
        bonus = attacker.get_stat(stat_used)
        total = roll + bonus
        
        defense = target.get_stat("Reflexes") + 10 # Base AC
        
        hit = total >= defense
        
        if hit:
            dmg = random.randint(1, 6) + bonus # Base D6
            target.hp -= dmg
            return f"Hit! Dealt {dmg} damage."
        else:
            return "Miss!"

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
        if hasattr(combatant, 'is_burning') and combatant.is_burning:
            dmg = random.randint(1, 4)
            combatant.take_damage(dmg)
            log.append(f"{combatant.name} takes {dmg} Fire damage from Burning!")
            
        if hasattr(combatant, 'is_bleeding') and combatant.is_bleeding:
            dmg = 1
            combatant.take_damage(dmg)
            log.append(f"{combatant.name} takes {dmg} Bleed damage!")

        # 2. Check Conditions
        if hasattr(combatant, 'is_frozen') and combatant.is_frozen:
             log.append(f"{combatant.name} is FROZEN solid and skips their turn!")
             return False, log

        if combatant.is_stunned:
             log.append(f"{combatant.name} is STUNNED and skips their turn!")
             return False, log
             
        if combatant.is_paralyzed:
             log.append(f"{combatant.name} is PARALYZED and skips their turn!")
             return False, log
             
        if combatant.is_confused:
            # 50% chance to act normally
            if random.random() < 0.5:
                 log.append(f"{combatant.name} is CONFUSED but maintains focus!")
            else:
                 log.append(f"{combatant.name} moves wildly in CONFUSION!")
                 # Logic for random action would go here. For now, skip turn (flail).
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
    
        # Check Round Cycle
        if self.current_turn_idx == 0:
            self.round_counter += 1
            self.tick_hazards()
            if self.log_callback: self.log_callback(f"--- Round {self.round_counter} ---")

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
        
        # STATUS OVERRIDE: Berserk -> Force Aggressive + Attack Nearest (Friend or Foe)
        if ai_char.is_berserk:
             ai_template = "Berserk" # Handled below
             
        # Find targets (other living combatants)
        # Normal AI: Enemies only
        # Berserk/Confused: Might target allies
        targets = []
        if ai_template == "Berserk":
             targets = [c for c in self.combatants if c.is_alive() and c != ai_char] # Everyone is a target
        else:
             targets = [c for c in self.combatants if c.is_alive() and c != ai_char] # Simplified Team check later? 
             # Currently no Teams. Everyone is enemy of everyone in deathmatch.
             pass
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
            # Strategy: Maintain Distance (Range 3-5) and Attack/Cast
            ideal_range = 4
            
            # 1. MOVEMENT (Kiting)
            # If too close (<= 2), run away
            if dist_sq <= 2:
                # Move AWAY from target
                move_x = ai_char.x - (1 if target.x > ai_char.x else (-1 if target.x < ai_char.x else 0))
                move_y = ai_char.y - (1 if target.y > ai_char.y else (-1 if target.y < ai_char.y else 0))
                ok, msg = self.move_char(ai_char, move_x, move_y)
                log.append(f"[AI] Kiting: {msg}")
            
            # If too far (> 5), move closer
            elif dist_sq > 5:
                move_x = ai_char.x + (1 if target.x > ai_char.x else (-1 if target.x < ai_char.x else 0))
                move_y = ai_char.y + (1 if target.y > ai_char.y else (-1 if target.y < ai_char.y else 0))
                ok, msg = self.move_char(ai_char, move_x, move_y)
                log.append(f"[AI] Closing: {msg}")
                
            # 2. ACTION (Cast or Attack)
            # Recalculate distance after move
            dx = abs(ai_char.x - target.x)
            dy = abs(ai_char.y - target.y)
            new_dist = max(dx, dy)
            
            # Try Casting Spell first (if available)
            casted = False
            # Try Casting Spell first (if available)
            casted = False
            # Fix: Check SP or FP (since we don't know which stat uses which yet, assume 2 is min cost)
            if ai_char.powers and (ai_char.sp >= 2 or ai_char.fp >= 2):
                 import random
                 # Priority: Control if target free, then Damage
                 control_spells = [p for p in ai_char.powers if "Entangle" in p or "Sleep" in p or "Stun" in p]
                 damage_spells = [p for p in ai_char.powers if p not in control_spells]
                 
                 chosen_spell = None
                 # Check status (assuming properties exist, or check active_effects list)
                 is_controlled = target.is_restrained or target.is_stunned or target.is_grappled
                 
                 # Mix up strategy: 70% focus on control, 30% just blast 'em
                 wants_control = (not is_controlled and control_spells and random.random() < 0.7)
                 
                 if wants_control:
                     chosen_spell = random.choice(control_spells)
                     log.append(f"[AI] Prioritizing Control: {chosen_spell}")
                 elif damage_spells:
                     chosen_spell = random.choice(damage_spells)
                     msg = "Prioritizing Damage" if is_controlled else "Mixing it up (Damage)"
                     log.append(f"[AI] {msg}: {chosen_spell}")
                 
                 if chosen_spell:
                     res = self.activate_ability(ai_char, chosen_spell, target)
                     log.extend(res)
                     casted = True
                 
            if not casted:
                # Fallback to Attack if in range
                rng = ai_char.get_attack_range()
                if new_dist <= rng:
                    log.extend(self.attack_target(ai_char, target))
                else:
                    log.append(f"[AI] Target out of range ({new_dist} > {rng}).")
            
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
        # Boundaries
        if not (0 <= tx < self.cols and 0 <= ty < self.rows):
            return False, "Out of Bounds!"

        # Calculate distance
        dist = max(abs(char.x - tx), abs(char.y - ty)) * 5 # 5ft per square
        
        # Check Status: Restrained/Grappled -> Speed 0
        if char.is_restrained or char.is_grappled:
            return False, "You are Restrained/Grappled and cannot move!"
            
        # Check Status: Prone -> Half Speed (Cost double?)
        # For now, simplistic: If Prone, movement costs double?
        # Or require "Stand Up" action?
        # Simplest: Prone = -2 Movement or similar?
        # Let's say Prone costs 2x movement.
        if char.is_prone:
            dist *= 2
            
        if dist > char.movement_remaining:
            return False, f"Not enough movement! ({char.movement_remaining} left)"
        
        # Check collision
        for c in self.combatants:
            if c.is_alive() and c != char and c.x == tx and c.y == ty:
                # BURT'S UPDATE: Collision Check with Talent Exception
                can_pass = getattr(char, "can_move_through_enemies", False)
                if not can_pass:
                    return False, "Blocked!"
                else:
                    # Logic for "Sharing Space" mechanics?
                    # For now we allow them to enter the square.
                    pass
        
        if (tx, ty) in self.walls:
            # Talent Check: Phase Walking / Ghost
            if not getattr(char, "can_phase_walk", False):
                return False, "Blocked by Wall!"
                
        char.x = tx
        char.y = ty
        char.movement_remaining -= dist
        return True, f"Moved to {tx},{ty}. ({char.movement_remaining} left)"

    def attack_target(self, attacker, target):
        # Range Check - supports both melee and ranged
        dx = abs(attacker.x - target.x)
        dy = abs(attacker.y - target.y)
        dist_sq = max(dx, dy)  # Chebyshev distance in squares
        
        # Check if weapon is ranged
        is_ranged = False
        max_range = 1  # Default melee reach
        
        if attacker.inventory:
            wpn = attacker.inventory.equipped.get("Main Hand")
            if wpn:
                # Check for ranged weapon
                if hasattr(wpn, "range_short") and wpn.range_short:
                    is_ranged = True
                    max_range = wpn.range_short  # In tiles (squares)
                elif hasattr(wpn, "tags") and "RANGE" in getattr(wpn, "tags", {}):
                    is_ranged = True
                    max_range = 6  # Default ranged = 6 tiles (30ft)
        
        # Check for reach-extending effects (melee only)
        if not is_ranged:
            for eff in attacker.active_effects:
                if "reach" in eff["name"].lower():
                    max_range = 2  # 10ft reach
        
        if dist_sq > max_range:
            range_type = "Range" if is_ranged else "Reach"
            return [f"Target out of range! (Distance: {dist_sq * 5}ft, {range_type}: {max_range * 5}ft)"]

        # Status Check: Charmed
        if attacker.is_charmed and attacker.charmed_by == target.name:
            return [f"{attacker.name} is Charmed by {target.name} and cannot attack!"]
            
        # Status Check: Frightened
        # Disadvantage on attacks (-2)
        # Status Check: Blinded
        # Disadvantage on attacks (-5 presumably? or just fail?)
        # Let's use Disadvantage = -4 (approx 2d20 keep low)

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
        attack_stat = "Might"
        skill_rank = 0
        
        if attacker.inventory:
            attack_stat = attacker.inventory.get_weapon_main_stat()
            # Get Skill Rank (e.g. "The Great Weapons")
            wpn = attacker.inventory.equipped["Main Hand"]
            if wpn and wpn.family:
                 skill_rank = attacker.get_skill_rank(wpn.family)
            if not wpn: # Unarmed
                 skill_rank = attacker.get_skill_rank("The Fist")
            
        hit_mod = attacker.get_stat_modifier(attack_stat) + skill_rank
        # Log details for clarity in debug
        # log.append(f"(Roll: d20 + {attack_stat} {hit_mod-skill_rank} + Skill {skill_rank})")

        hit_score = hit_mod + random.randint(1, 20)
        
        # STATUS MODIFIERS (Attacker)
        if attacker.is_prone: hit_score -= 2 # Prone attacking
        if attacker.is_blinded: hit_score -= 4 
        if attacker.is_restrained: hit_score -= 2
        if attacker.is_frightened: hit_score -= 2
        
        if attacker.is_invisible: 
             hit_score += 4 # Unseen attacker
             attacker.is_invisible = False # Breaks invisibility
             log.append(f"{attacker.name} appears from invisibility!")
             
        # STATUS MODIFIERS (Defender)
        # Prone defender = Advantage for attacker (+4)
        if target.is_prone: hit_score += 4 
        # Blind defender = Advantage (+4)
        if target.is_blinded: hit_score += 4
        # Stunned/Paralyzed = Auto Crit? Or massive bonus.
        if target.is_stunned or target.is_paralyzed: hit_score += 5
        
        # Defender uses AC (Base 10 + Dex/Armor Mod)
        # In D&D: AC = 10 + Mod. 
        # Here: Armor might provide base AC? 
        # For now, let's use: Def_Score = 10 + Def_Stat_Mod
        
        def_mod = target.get_stat_modifier(def_stat_name)
        
        # Add Defender Skill Rank (Armor)
        def_skill_rank = 0
        if target.inventory:
             armor = target.inventory.equipped["Armor"]
             if armor and armor.family:
                  def_skill_rank = target.get_skill_rank(armor.family)
        
        # User requested "Active Defense".
        # So Defender Rolls: d20 + Mod + Skill
        def_total_mod = def_mod + def_skill_rank
        def_roll = def_total_mod + random.randint(1, 20)
        
        # LOGIC: Check Hit
        # CLASH CHECK (Equal rolls or within 1)
        if abs(hit_score - def_roll) <= 1:
            self.clash_active = True
            # Store participants for resolution
            self.clash_participants = (attacker, target)
            self.clash_stat = attack_stat # Stat used for the clash
            
            log.append(f"CLASH TRIGGERED! ({hit_score} vs {def_roll})")
            return log

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
            "target": target,
            "tier": 1  # Default tier, updated below
        }
        
        try:
            # Lookup Data
            data_item = engine_hooks.get_ability_data(ability_name)
            
            # Get tier for damage scaling
            if data_item and data_item.get("Tier"):
                try:
                    ctx["tier"] = int(data_item.get("Tier"))
                except:
                    pass
            
            if data_item:
                # 1. Determine Cost and Resource Type
                physical_stats = ['Might', 'Reflexes', 'Finesse', 'Endurance', 'Vitality', 'Fortitude']
                attr = data_item.get('Attribute', '')
                
                # Physical stats use SP, Mental stats use FP
                res = 'SP' if attr in physical_stats else 'FP'
                
                # Cost = Tier for School abilities, else 2
                tier = data_item.get('Tier')
                if tier:
                    try:
                        val = int(tier)
                    except:
                        val = 2
                else:
                    val = 2
                
                # Check affordability
                curr = char.sp if res == 'SP' else char.fp
                if curr < val:
                    log.append(f'Not enough {res}! Need {val}, have {curr}.')
                    return log
                    
                # Consume resource
                if res == 'SP': 
                    char.sp -= val
                else: 
                    char.fp -= val
                log.append(f'Consumed {val} {res}')

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

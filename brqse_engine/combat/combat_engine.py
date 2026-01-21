from typing import List, Tuple, Dict, Any, Optional
from brqse_engine.combat.combatant import Combatant
from brqse_engine.core.dice import Dice
import brqse_engine.abilities.engine_hooks as engine_hooks
from brqse_engine.abilities.effects_registry import registry

# --- TERRAIN DATA (synced with Data/Terrain_Types.csv) ---
TERRAIN_DATA = {
    "normal": {"move_cost": 1, "damage_type": None, "damage_dice": None},
    "difficult": {"move_cost": 2, "damage_type": None, "damage_dice": None},
    "water_shallow": {"move_cost": 2, "damage_type": None, "damage_dice": None, "effect": "fire_resistance"},
    "water_deep": {"move_cost": 3, "damage_type": None, "damage_dice": None, "effect": "swim_required"},
    "ice": {"move_cost": 1, "damage_type": None, "damage_dice": None, "effect": "slip_prone"},
    "mud": {"move_cost": 2, "damage_type": None, "damage_dice": None, "effect": "grapple_disadvantage"},
    "fire": {"move_cost": 2, "damage_type": "Fire", "damage_dice": "1d6"},
    "acid": {"move_cost": 2, "damage_type": "Acid", "damage_dice": "1d8"},
    "spikes": {"move_cost": 2, "damage_type": "Piercing", "damage_dice": "1d10"},
    "darkness": {"move_cost": 1, "damage_type": None, "damage_dice": None, "effect": "blinded"},
    "high_ground": {"move_cost": 1, "damage_type": None, "damage_dice": None, "effect": "ranged_advantage"},
    "tree": {"move_cost": 99, "damage_type": None, "damage_dice": None, "effect": "cover"},
    "rubble": {"move_cost": 2, "damage_type": None, "damage_dice": None},
    "tall_grass": {"move_cost": 2, "damage_type": None, "damage_dice": None, "effect": "half_cover_prone"},
    "lava": {"move_cost": 99, "damage_type": "Fire", "damage_dice": "4d10"},
    "pit": {"move_cost": 1, "damage_type": "Bludgeoning", "damage_dice": "2d6", "effect": "fall"},
}

class Tile:
    """Represents a single tile on the combat grid."""
    def __init__(self, terrain="normal", x=0, y=0):
        self.x = x
        self.y = y
        self.terrain = terrain
        self._update_data()
    
    def _update_data(self):
        data = TERRAIN_DATA.get(self.terrain, TERRAIN_DATA["normal"])
        self.move_cost = data.get("move_cost", 1)
        self.damage_type = data.get("damage_type")
        self.damage_dice = data.get("damage_dice")
        self.effect = data.get("effect")

class CombatEngine:
    """
    Manages the flow of combat: Turn order, Movement, Actions.
    Pure logic - no direct UI calls.
    Returns 'Replay Logs' or 'Events' that the UI can render.
    """
    def __init__(self, cols=12, rows=12):
        self.cols = cols
        self.rows = rows
        self.combatants: List[Combatant] = []
        self.turn_order: List[Combatant] = []
        self.current_turn_index = 0
        self.round_counter = 1
        self.turn_order: List[Combatant] = []
        self.current_turn_index = 0
        self.round_counter = 1
        self.log_history: List[str] = []
        self.events: List[Dict[str, Any]] = [] # Structured replay events
        
        # Terrain Grid
        self.tiles = [[Tile("normal", x, y) for x in range(cols)] for y in range(rows)]
        self.walls = set()
        
        # Load Social Maneuvers
        self.social_maneuvers = {}
        self._load_social_data()
        
        # Load Trauma Tables
        self.traumas = {"Physical": [], "Mental": []}
        self._load_trauma_data()
        
        # Note: Terrain data is stored in TERRAIN_DATA constant
        # Tactical rules (Flanking/Mobbing/Cover) are in _get_attack_modifiers()

    def _load_social_data(self):
        """Loads Social_Maneuvers.csv"""
        import csv
        import os
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Data", "Social_Maneuvers.csv")
        if os.path.exists(path):
            with open(path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.social_maneuvers[row["Maneuver"]] = row

    def _load_trauma_data(self):
        """Loads Traumas.csv into Physical and Mental lists."""
        import csv
        import os
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Data", "Traumas.csv")
        if os.path.exists(path):
            with open(path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    trauma_type = row.get("Type", "Physical")
                    if trauma_type in self.traumas:
                        self.traumas[trauma_type].append(row)

    def roll_trauma(self, combatant: Combatant, trauma_type: str = "Physical") -> str:
        """Rolls on trauma table and applies injury. Returns injury name."""
        table = self.traumas.get(trauma_type, [])
        if not table:
            return None
        
        roll, _, _ = Dice.roll("1d6")
        # Find matching trauma by Roll column
        for trauma in table:
            if int(trauma.get("Roll", 0)) == roll:
                injury_name = trauma.get("Name", "Unknown Injury")
                combatant.add_injury(injury_name)
                self.log(f"TRAUMA! {combatant.name} suffers {injury_name}: {trauma.get('Effect', '')}")
                self.record_event("trauma", combatant.name, injury=injury_name, effect=trauma.get("Effect"))
                return injury_name
        
        # Fallback to first entry if roll doesn't match
        if table:
            injury_name = table[0].get("Name", "Minor Wound")
            combatant.add_injury(injury_name)
            return injury_name
        return None

    def add_combatant(self, combatant: Combatant):
        self.combatants.append(combatant)
        
    def record_event(self, event_type: str, actor: str, **kwargs):
        """Records a structured event for the frontend."""
        event = {
            "type": event_type,
            "actor": actor,
            **kwargs
        }
        self.events.append(event)

    def start_combat(self):
        """Rolls initiative and sorts turn order."""
        for c in self.combatants:
            c.roll_initiative()
            
        self.turn_order = sorted(self.combatants, key=lambda c: c.initiative, reverse=True)
        self.current_turn_index = 0
        self.round_counter = 1
        self.log(f"Combat Started! Round {self.round_counter}")
        self.record_event("info", "System", description=f"Round {self.round_counter} Begins")
        self.log(f"Turn Order: {[c.name for c in self.turn_order]}")

    def next_turn(self):
        """Advances to the next combatant."""
        self.current_turn_index += 1
        if self.current_turn_index >= len(self.turn_order):
            self.current_turn_index = 0
            self.round_counter += 1
            self.log(f"Round {self.round_counter} Begins!")
            self.record_event("info", "System", description=f"Round {self.round_counter} Begins")
            
        active = self.get_active_combatant()
        
        # Tick Effects (Phase C2)
        expired = active.tick_effects()
        if expired:
            self.log(f"{active.name}: Effects expired - {', '.join(expired)}")
            self.record_event("info", active.name, description=f"Effects expired: {expired}")
        
        # Process Conditions (Phase C3 Hardening)
        self._process_turn_start_conditions(active)
            
        # Reset Action Flags
        active.reaction_used = False
        self.log(f"{active.name}'s Turn.")
        self.record_event("info", active.name, description="Turn Starts")

    def _process_turn_start_conditions(self, combatant: Combatant):
        """
        Applies damage/effects for conditions at start of turn.
        """
        if combatant.has_condition("Bleeding"):
             dmg, _, _ = Dice.roll("1d4")
             self.log(f"{combatant.name} Bleeds for {dmg} damage.")
             combatant.take_damage(dmg)
             self.record_event("dot_damage", combatant.name, damage=dmg, effect="Bleeding")
             
        if combatant.has_condition("Poisoned"):
             dmg, _, _ = Dice.roll("1d4")
             self.log(f"{combatant.name} takes {dmg} Poison damage.")
             combatant.take_damage(dmg)
             self.record_event("dot_damage", combatant.name, damage=dmg, effect="Poisoned")
             
        if combatant.has_condition("Burning"):
             dmg, _, _ = Dice.roll("1d6")
             self.log(f"{combatant.name} Burns for {dmg} damage.")
             combatant.take_damage(dmg)
             self.record_event("dot_damage", combatant.name, damage=dmg, effect="Burning")

    def get_active_combatant(self) -> Combatant:
        if not self.turn_order: return None
        return self.turn_order[self.current_turn_index]

    def set_terrain(self, x, y, terrain_type):
        """Set terrain type at coordinates."""
        if 0 <= y < self.rows and 0 <= x < self.cols:
            self.tiles[y][x] = Tile(terrain_type, x, y)
    
    def create_wall(self, x, y):
        """Creates a wall at the specified coordinates."""
        if 0 <= x < self.cols and 0 <= y < self.rows:
            self.walls.add((x, y))

    def move_entity(self, combatant: Combatant, x: int, y: int) -> bool:
        """
        Attempts to move entity to target.
        Handles Terrain Costs and Hazards.
        """
        # 1. Bounds Check
        if not (0 <= x < self.cols and 0 <= y < self.rows):
            return False
            
        # 2. Collision Check (Walls)
        if (x, y) in self.walls:
            return False
            
        # 3. Collision Check (Other Entities)
        for c in self.combatants:
            if c.is_alive and c.x == x and c.y == y:
                return False
        
        # 4. Terrain Cost Check
        tile = self.tiles[y][x]
        cost = tile.move_cost
        
        # Checking Movement
        if hasattr(combatant.character, "movement_remaining"):
             if combatant.character.movement_remaining < cost * 5:
                 self.log(f"{combatant.name} not enough movement for {tile.terrain}.")
                 return False
             combatant.character.movement_remaining -= cost * 5
        
        # 5. Update Position
        old_x, old_y = combatant.x, combatant.y
        combatant.x = x
        combatant.y = y
        # Use dict unpacking because 'from' is a reserved keyword
        self.record_event("move", combatant.name, **{"from": [old_x, old_y], "to": [x, y]})
        
        # 6. Apply Hazard Effects
        if tile.damage_dice:
            dmg_roll, _, _ = Dice.roll(tile.damage_dice)
            self.log(f"{combatant.name} enters {tile.terrain}! Takes {dmg_roll} {tile.damage_type} damage.")
            combatant.take_damage(dmg_roll)
            self.record_event("hazard", combatant.name, damage=dmg_roll, effect=tile.terrain)
            
        return True

    def activate_ability(self, user: Combatant, ability_name: str, target: Combatant = None) -> bool:
        """
        Activates an ability/spell/skill using the effects registry.
        """
        if hasattr(user, "is_stunned") and user.is_stunned:
            self.log(f"{user.name} is Stunned and cannot act!")
            self.record_event("info", user.name, description="Stunned - Cannot Act")
            return False
            
        data = engine_hooks.get_ability_data(ability_name)
        if not data:
            self.log(f"Ability '{ability_name}' not found.")
            return False
            
        description = data.get("Effect") or data.get("Description")
        if not description:
            self.log(f"Ability '{ability_name}' has no effect description.")
            return False
            
        self.log(f"{user.name} uses {ability_name} on {target.name if target else 'Self'}!")
        self.record_event("ability", user.name, ability=ability_name, target=target.name if target else None)
        
        # Build Context
        context = {
            "attacker": user,
            "target": target,
            "engine": self,
            "log": self.log_history
        }
        
        # Execute
        try:
            return registry.resolve(description, context)
        except Exception as e:
            self.log(f"Error using {ability_name}: {e}")
            return False

    def get_adjacent_opponents(self, combatant: Combatant) -> List[Combatant]:
        """Returns list of adjacent enemies."""
        ops = []
        for c in self.combatants:
            if c != combatant and c.team != combatant.team and c.is_alive:
                if max(abs(c.x - combatant.x), abs(c.y - combatant.y)) <= 1:
                    ops.append(c)
        return ops

    def check_cover(self, attacker: Combatant, target: Combatant) -> int:
        """Returns AC bonus from cover (0, +2, or 999 for Full)."""
        # Simple line check for obstacles
        # For now, just checking adjacent walls to target in direction of attacker?
        # A true line-of-sight check is complex. 
        # Simplified: If target is next to a wall between them -> Half Cover
        return 0 # Plac horder for complex LOS

    def _get_attack_modifiers(self, attacker: Combatant, target: Combatant, is_ranged: bool) -> Tuple[bool, bool, List[str]]:
        """
        Calculates advantage/disadvantage based on Tactics AND Status Effects.
        Returns: (advantage, disadvantage, log_lines)
        """
        adv = False
        dis = False
        logs = []
        
        # --- TACTICS (Flanking/Mobbing) ---
        adj_enemies = self.get_adjacent_opponents(target)
        # Allies of the attacker engaging the target
        allies_engaging = [c for c in adj_enemies if c.team == attacker.team and c != attacker]
        
        if len(allies_engaging) >= 2: # Mobbed
            adv = True 
            logs.append("[Mobbing] Advantage.")
        
        # --- STATUS EFFECTS ---
        # 1. PRONE
        if target.has_condition("Prone"):
            if not is_ranged:
                adv = True
                logs.append("[Target Prone] Melee Advantage.")
            else:
                dis = True
                logs.append("[Target Prone] Ranged Disadvantage.")
        
        # 2. BLINDED
        if attacker.has_condition("Blinded"):
            dis = True
            logs.append("[Blinded] Attacking with Disadvantage.")
        
        if target.has_condition("Blinded"):
            adv = True
            logs.append("[Target Blinded] Advantage.")
            
        # 3. STUNNED/PARALYZED (Auto Advantage)
        if target.is_stunned:
             adv = True
             logs.append("[Target Stunned] Advantage.")
             
        # 4. RANGED VS ENGAGED
        if is_ranged:
            attacker_engaged = len(self.get_adjacent_opponents(attacker)) > 0
            if attacker_engaged:
                dis = True
                logs.append("[Engaged] Ranged Disadvantage.")
        
        # 5. MASTERY EFFECTS
        # Get attacker's weapon skill and check for mastery unlocks
        weapon = attacker.character.get_equipped_weapon()
        weapon_skill = weapon.get("Related_Skill", weapon.get("Skill", ""))
        unlocks = attacker.character.get_active_mastery_unlocks(weapon_skill)
        
        for unlock in unlocks:
            effect = unlock.get("effect", "").lower()
            name = unlock.get("name", "")
            
            # Execute: Advantage on Bloodied targets (<50% HP)
            if "advantage" in effect and ("bloodied" in effect or "<50%" in effect):
                if target.is_bloodied:
                    adv = True
                    logs.append(f"[{name}] Advantage (target Bloodied).")
            
            # Executioner: Advantage on Prone/Stunned
            if "advantage" in effect and ("prone" in effect or "stunned" in effect):
                if target.has_condition("Prone") or target.is_stunned:
                    adv = True
                    logs.append(f"[{name}] Advantage (target incapacitated).")
            
            # Backstab: Advantage when Flanking
            if "advantage" in effect and "flank" in effect:
                if len(allies_engaging) >= 1:
                    adv = True
                    logs.append(f"[{name}] Flanking Advantage.")

        return adv, dis, logs

    def execute_attack(self, attacker: Combatant, target: Combatant, weapon_stat="Might", is_ranged=False) -> Dict[str, Any]:
        """
        Calculates an attack roll and damage.
        Handles Flanking, Mobbing, Ranged Penalties, and Friendly Fire.
        """
        log_entries = []
        
        # 0. Determine Distance & Ranged Status
        dist = max(abs(attacker.x - target.x), abs(attacker.y - target.y))
        if dist > 1: is_ranged = True
        
        # 1. Get Modifiers (Tactics + Status)
        atk_advantage, atk_disadvantage, mod_logs = self._get_attack_modifiers(attacker, target, is_ranged)
        log_entries.extend(mod_logs)

        # Tactical: Flanking adds +2 if strictly Flanked (1 ally) and not Mobbed (Advantage)
        # Verify allies count again for the +2 bonus logic
        adj_enemies = self.get_adjacent_opponents(target)
        allies_engaging = [c for c in adj_enemies if c.team == attacker.team and c != attacker]
        
        # 2. Roll to Hit (With Advantage/Disadvantage Logic)
        def roll_d20(adv=False, dis=False):
            r1, _, _ = Dice.roll("1d20")
            r2, _, _ = Dice.roll("1d20")
            if adv and not dis: return max(r1, r2), " (Adv)"
            if dis and not adv: return min(r1, r2), " (Dis)"
            return r1, ""

        roll_val, roll_note = roll_d20(atk_advantage, atk_disadvantage)
        
        # Calculate Base Modifier
        mod = attacker.get_stat_mod(weapon_stat)
        
        # Add Flanking Bonus (+2) if strictly Flanked (1 ally) and not relying on Adv only
        if len(allies_engaging) == 1 and not is_ranged:
            mod += 2
            
        total_hit = roll_val + mod
        
        # 3. Determine AC
        # Base AC + Armor + Shield + Dex
        target_ac = target.get_ac()
        
        # Apply Defender Disadvantage logic from old code?
        # If target has a condition that reduces AC, apply here.
        # Def Disadvantage was mapped to Attacker Advantage in modern 5e style rules usually.
        # But if we want specific AC penalty:
        if target.has_condition("Sunder"): # Example
             target_ac -= 2
             
        # 4. Check Cover (Tactical)
        cover_bonus = self.check_cover(attacker, target)
        if cover_bonus > 10:
             log_entries.append("Target has Full Cover!")
             hit = False
             # Force miss or very high AC
             target_ac += 99 # Effectively unhittable
        elif cover_bonus > 0:
             target_ac += cover_bonus
             log_entries.append(f"[Cover] +{cover_bonus} AC")
        
        hit = total_hit >= target_ac
        critical = roll_val == 20
        miss = not hit
        
        # 5. Friendly Fire Check (Ranged Only)
        friendly_hit = None
        if is_ranged and miss: # "if they fail the attack roll"
            # Check for allies in path or adjacent to target
            # Simplified: Is there an ally of Attacker adjacent to Target?
            # "Shooting past or next to them"
            allies_near_target = []
            for c in self.combatants:
                if c != target and c.team == attacker.team and c.is_alive:
                     if max(abs(c.x - target.x), abs(c.y - target.y)) <= 1:
                         allies_near_target.append(c)
            
            if allies_near_target:
                 # 50% chance to hit ally
                 ff_roll, _, _ = Dice.roll("1d100")
                 if ff_roll <= 50:
                     friendly_hit = allies_near_target[0] # Hit the first one found
                     log_entries.append(f"FRIENDLY FIRE! Aimed at {target.name}, hit {friendly_hit.name} instead!")
                     hit = True # We hit *something*
                     target = friendly_hit # Swap target for damage calculation

        result = {
            "attacker": attacker.name,
            "target": target.name,
            "roll": roll_val,
            "total": total_hit,
            "ac": target_ac,
            "hit": hit,
            "critical": critical,
            "damage": 0,
            "log": f"{attacker.name} attacks {target.name}: {total_hit} vs AC {target_ac}. {'HIT!' if hit else 'MISS.'}"
        }
        if log_entries: result["log"] += " " + " ".join(log_entries)
        
        if hit:
            # 5. Resolve Damage
            # Fetch equipped weapon (or unarmed)
            weapon = attacker.character.get_equipped_weapon()
            dmg_dice = weapon.get("Damage", "1d4")
            
            # Roll Damage
            dmg_roll, _, _ = Dice.roll(dmg_dice)
            dmg = dmg_roll + mod
            
            if critical:
                dmg *= 2 # Simple crit rule
                result["log"] += f" CRITICAL HIT! ({dmg_dice}*2 + {mod})"
            else:
                result["log"] += f" ({dmg_dice} + {mod})"
                
            damage_took = target.take_damage(dmg) # Apply damage
            result["damage"] = dmg
            result["target_hp"] = target.current_hp
            result["log"] += f" Dealt {dmg} damage."
            if friendly_hit: result["log"] += " (Friendly Fire)"
            
            if target.current_hp == 0:
                result["log"] += f" {target.name} is DOWN!"
                self.record_event("death", target.name, x=target.x, y=target.y)
        
        self.log(result["log"])
        self.record_event("attack", attacker.name, 
            target=target.name,
            attack_roll=total_hit,
            defense_roll=target_ac,
            result="CRITICAL" if critical else "HIT" if hit else "MISS",
            damage=result["damage"]
        )
        return result

    def log(self, message: str):
        self.log_history.append(message)
        # Also record as info event for replay
        self.record_event("info", "System", description=message)

    def execute_social_maneuver(self, attacker: Combatant, target: Combatant, maneuver_name: str) -> bool:
        """
        Executes a Social Maneuver (Gaslight, Filibuster, etc).
        """
        maneuver = self.social_maneuvers.get(maneuver_name)
        if not maneuver:
             self.log(f"Unknown maneuver: {maneuver_name}")
             return False

        self.log(f"{attacker.name} uses {maneuver_name} on {target.name}!")
        
        # Parse Roll (e.g. "Logic vs Intuition")
        roll_str = maneuver.get("Roll", "None")
        if " vs " in roll_str:
             att_stat, def_stat = roll_str.split(" vs ")
             
             # Roll Off
             r1, _, _ = Dice.roll("1d20")
             r2, _, _ = Dice.roll("1d20")
             
             att_total = r1 + attacker.get_stat_mod(att_stat)
             def_total = r2 + target.get_stat_mod(def_stat)
             
             self.log(f"{attacker.name} rolls {att_stat} ({att_total}) vs {target.name}'s {def_stat} ({def_total}).")
             
             if att_total > def_total:
                 self.log(f"Success! {maneuver['Effect']}")
                 
                 effect_desc = maneuver['Effect']
                 if "Composure" in effect_desc or "Structure" in effect_desc: # Treat 'Structure' as Composure for now?
                      dmg, _, _ = Dice.roll("1d6") # Default Social Dmg
                      if "Critical" in effect_desc: dmg *= 2
                      
                      taken = target.take_social_damage(dmg)
                      self.log(f"{target.name} loses {taken} Composure. (Current: {target.current_composure})")
                      
                      if target.is_broken:
                           self.log(f"{target.name} is BROKEN! (Social Defeat)")
                           self.record_event("social_defeat", target.name)
                 
                 return True
             else:
                 self.log("Failed.")
                 return False
        
        return True

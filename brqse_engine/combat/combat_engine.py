from typing import List, Tuple, Dict, Any, Optional
from brqse_engine.combat.combatant import Combatant
from brqse_engine.core.dice import Dice
import brqse_engine.abilities.engine_hooks as engine_hooks
from brqse_engine.abilities.effects_registry import registry

# --- TERRAIN DATA ---
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
    "high_ground": {"move_cost": 1, "damage_type": None, "damage_dice": None, "effect": "ranged_bonus"},
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

    def execute_attack(self, attacker: Combatant, target: Combatant, weapon_stat="Might") -> Dict[str, Any]:
        """
        Calculates an attack roll and damage.
        Returns a result dict.
        """
        # 1. Roll to Hit
        roll_val, _, breakdown = Dice.roll("1d20")
        
        # Calculate Modifier
        mod = attacker.get_stat_mod(weapon_stat)
        total_hit = roll_val + mod
        
        # Determine AC (Reflex + 10 etc)
        # Simplified: AC = 10 + Reflex Mod + Armor
        target_ac = 10 + target.get_stat_mod("Reflexes") 
        # TODO: Add Armor bonus lookup
        
        hit = total_hit >= target_ac
        critical = roll_val == 20
        miss = not hit
        
        result = {
            "attacker": attacker.name,
            "target": target.name,
            "roll": roll_val,
            "total": total_hit,
            "ac": target_ac,
            "hit": hit,
            "critical": critical,
            "damage": 0,
            "log": f"{attacker.name} attacks {target.name}: Rolled {total_hit} vs AC {target_ac}. {'HIT!' if hit else 'MISS.'}"
        }
        
        if hit:
            # Roll Damage (Hardcoded 1d6 for now - needs Weapon lookap)
            dmg_roll, _, _ = Dice.roll("1d6") 
            dmg = dmg_roll + mod
            if critical:
                dmg *= 2 # Simple crit rule
                result["log"] += " CRITICAL HIT!"
                
            damage_took = target.take_damage(dmg) # Apply damage
            result["damage"] = dmg
            result["target_hp"] = target.current_hp
            result["log"] += f" Dealt {dmg} damage."
            
            if target.current_hp == 0:
                result["log"] += f" {target.name} is DOWN!"
        
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
        # print("[Engine]", message) # Debug logging

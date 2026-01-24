from typing import List, Tuple, Dict, Any, Optional
import random
import math
from brqse_engine.combat.combatant import Combatant
from brqse_engine.core.dice import Dice
from brqse_engine.core.constants import Conditions, Stats

# Use logic similar to mechanics.py for consistency
COVER_NONE = 0
COVER_HALF = 1
COVER_FULL = 2

class Tile:
    def __init__(self, terrain="normal", x=0, y=0):
        self.x, self.y = x, y
        self.terrain = terrain
        self.elevation = 0
        self.is_cover = False

class CombatEngine:
    def __init__(self, cols=20, rows=20, chaos_manager=None):
        self.cols, self.rows = cols, rows
        self.combatants: List[Combatant] = []
        self.tiles = [[Tile("normal", x, y) for x in range(cols)] for y in range(rows)]
        self.walls = set()
        self.chaos = chaos_manager
        self.events: List[Dict[str, Any]] = []
        self.clash_active = False
        self.clash_context = {}

    def add_combatant(self, combatant: Combatant): self.combatants.append(combatant)
    def record_event(self, event_type: str, actor: str, **kwargs): self.events.append({"type": event_type, "actor": actor, **kwargs})
    def log(self, msg: str): self.record_event("info", "System", description=msg)

    def get_combatant_at(self, x: int, y: int) -> Optional[Combatant]:
        """Returns the combatant at the given coordinates, or None."""
        for c in self.combatants:
            if c.x == x and c.y == y and c.hp > 0: return c
        return None

    def is_behind(self, attacker: Combatant, target: Combatant) -> bool:
        """Returns True if attacker is in target's rear 180° arc."""
        dx, dy = attacker.x - target.x, attacker.y - target.y
        f = getattr(target, 'facing', 'N')
        if f == "N": return dy > 0
        if f == "S": return dy < 0
        if f == "E": return dx < 0
        if f == "W": return dx > 0
        return False

    def is_flanked(self, target: Combatant) -> bool:
        """Target is flanked if two enemies are on opposite sides."""
        enemies = [c for c in self.combatants if c.team != target.team and c.hp > 0]
        for i, e1 in enumerate(enemies):
            for e2 in enemies[i+1:]:
                dx1, dy1 = e1.x - target.x, e1.y - target.y
                dx2, dy2 = e2.x - target.x, e2.y - target.y
                # Opposite logic (x and -x, or y and -y)
                if (dx1 == -dx2 and dx1 != 0 and dy1 == dy2 == 0) or \
                   (dy1 == -dy2 and dy1 != 0 and dx1 == dx2 == 0):
                    return True
        return False

    def execute_attack(self, attacker: Combatant, target: Combatant, stat: str = "Might") -> Dict[str, Any]:
        """Advantage/Disadvantage system: No numeric +X bonuses."""
        has_adv = False
        has_dis = False

        # TACTICAL ADVANTAGE (Advantage)
        if attacker.elevation > target.elevation: 
            has_adv = True; self.log(f"{attacker.name} has High Ground (Advantage)")
        if self.is_behind(attacker, target):
            has_adv = True; self.log(f"Backstab! {attacker.name} strikes from behind (Advantage)")
        if self.is_flanked(target):
            has_adv = True; self.log(f"{target.name} is Flanked! (Advantage)")

        # TACTICAL DISADVANTAGE (Disadvantage)
        if target.is_behind_cover:
            has_dis = True; self.log(f"{target.name} is in Cover (Disadvantage)")

        # ROLL RESOLUTION
        if has_adv and not has_dis: atk_roll, _, _ = Dice.roll_advantage()
        elif has_dis and not has_adv: atk_roll, _, _ = Dice.roll_disadvantage()
        else: atk_roll = random.randint(1, 20)

        # --- ABILITY HOOKS (Trigger before roll if needed, or after) ---
        from brqse_engine.abilities import engine_hooks
        ctx = {"attacker": attacker, "target": target, "engine": self, "roll": atk_roll}
        engine_hooks.apply_hooks(attacker, "ON_ATTACK", ctx)

        atk_skill_name = attacker.get_weapon_skill_name()
        atk_stat_mod = attacker.get_stat_mod(stat)
        atk_skill_rank = attacker.get_skill_rank(atk_skill_name)
        
        atk_total = atk_roll + atk_stat_mod + atk_skill_rank
        atk_total = atk_roll + atk_stat_mod + atk_skill_rank
        log_detail = f"{attacker.name} attack: {atk_roll} (d20) + {atk_stat_mod} ({stat}) + {atk_skill_rank} ({atk_skill_name}) = {atk_total} vs "
        self.log(log_detail)
        
        # DEFENSE RESOLUTION (Armor-based d20 + Skill + Stat)
        def_roll = random.randint(1, 20)
        ctx["roll"] = def_roll
        engine_hooks.apply_hooks(target, "ON_DEFEND", ctx)

        def_stat_name, def_skill_name = target.get_defense_info()
        def_stat_mod = target.get_stat_mod(def_stat_name)
        def_skill_rank = target.get_skill_rank(def_skill_name)
        
        def_total = def_roll + def_stat_mod + def_skill_rank
        log_detail += f"{def_total} ({target.name} DEF)"
        self.log(f"{target.name} defense: {def_roll} + {def_stat_mod}({def_stat_name}) + {def_skill_rank}({def_skill_name}) = {def_total}")

        margin = atk_total - def_total
        if margin == 0: return self._trigger_clash(attacker, target, stat)
        if margin < 0:
            self.record_event("attack", attacker.name, target=target.name, result="MISS", damage=0)
            return {"hit": False, "roll_total": atk_total, "log_details": log_detail}
        
        # Damage scaling based on margin
        scaling = 0.5 if margin <= 5 else 1.0 if margin <= 10 else 2.0
        dmg = int((random.randint(1, 6) + attacker.get_stat_mod(stat)) * scaling)
        target.take_damage(max(1, dmg))
        self.record_event("attack", attacker.name, target=target.name, result="HIT", damage=dmg, margin=margin)

        # --- HIT HOOKS ---
        ctx["damage"] = dmg
        engine_hooks.apply_hooks(attacker, "ON_HIT", ctx)

        return {"hit": True, "damage": dmg, "roll_total": atk_total, "log_details": log_detail}

    def _trigger_clash(self, attacker, target, stat):
        self.clash_active = True
        self.clash_context = {"attacker": attacker, "target": target, "stat": stat}
        self.record_event("clash_start", attacker.name, target=target.name, stat=stat)
        return {"hit": False, "result": "CLASH"}

    def create_wall(self, x, y): self.walls.add((x, y))

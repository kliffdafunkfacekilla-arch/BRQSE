from brqse_engine.combat.combat_engine import CombatEngine
from brqse_engine.combat.combatant import Combatant
import random

class SimpleAI:
    """
    Adapts the tactical logic for the new CombatEngine (Phase C).
    Driver for the simulation.
    """
    
    @staticmethod
    def execute_turn(me: Combatant, engine: CombatEngine):
        """
        Dispatches AI logic based on archetype.
        """
        archetype = getattr(me, "ai_archetype", "Berserker")
        
        if archetype == "Sniper":
            SimpleAI._ai_ranged_sniper(me, engine)
        elif archetype == "Soldier":
            SimpleAI._ai_tactical_soldier(me, engine)
        else: # Default Berserker
            SimpleAI._ai_melee_berserker(me, engine)

    @staticmethod
    def _get_targets(me: Combatant, engine: CombatEngine):
        """Returns sorted list of (dist, combatant) enemies."""
        targets = []
        for c in engine.combatants:
            if c.is_alive and c.team != me.team:
                dist = max(abs(me.x - c.x), abs(me.y - c.y))
                targets.append((dist, c))
        targets.sort(key=lambda x: x[0])
        return targets

    @staticmethod
    def _ai_melee_berserker(me: Combatant, engine: CombatEngine):
        """
        Strategy: Aggressive Rush.
        Effectively the 'Simple' logic but greedy for damage.
        """
        targets = SimpleAI._get_targets(me, engine)
        if not targets: return
        
        dist, target = targets[0]
        desired_range = 1
        
        # MOVE
        if dist > desired_range:
            SimpleAI._move_towards(me, target, engine, desired_range)
            # Re-check distance
            dist = max(abs(me.x - target.x), abs(me.y - target.y))
            
        # ATTACK
        if dist <= desired_range:
            engine.execute_attack(me, target, "Might")

    @staticmethod
    def _ai_ranged_sniper(me: Combatant, engine: CombatEngine):
        """
        Strategy: Kite. Maintain distance 4-8.
        """
        targets = SimpleAI._get_targets(me, engine)
        if not targets: return
        
        dist, target = targets[0]
        min_range = 3
        max_range = 8
        
        # MOVE
        if dist < min_range:
            # Too close! Run away (Invert target vector)
            SimpleAI._move_away(me, target, engine)
        elif dist > max_range:
            # Too far! Approach.
            SimpleAI._move_towards(me, target, engine, max_range)
            
        # ATTACK (Check LOS/Range)
        # Assuming we have a ranged ability or weapon.
        # For now, force 'is_ranged=True' in attack call.
        dist = max(abs(me.x - target.x), abs(me.y - target.y))
        if dist <= max_range + 2: # Grace range
            # engine.execute_attack assumes melee unless specified
            # We need to pass is_ranged=True logic if supported
            # Since execute_attack creates the log, let's use it.
            # TODO: Use specific weapon stat like 'Reflexes' or 'Awareness'
            engine.execute_attack(me, target, "Reflexes", is_ranged=True)

    @staticmethod
    def _ai_tactical_soldier(me: Combatant, engine: CombatEngine):
        """
        Strategy: Safe. Stick to allies? Use Cover?
        For now: Same as Berserker but prefers flanking?
        """
        # Placeholder: Behave like a smart Berserker
        SimpleAI._ai_melee_berserker(me, engine)

    @staticmethod
    def _move_towards(me, target, engine, desired_range):
        """Greedy pathfinding towards target."""
        # Simple random shuffle of valid moves that decrease distance
        candidates = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        random.shuffle(candidates)
        
        current_dist = max(abs(me.x - target.x), abs(me.y - target.y))
        
        for dx, dy in candidates:
            nx, ny = me.x + dx, me.y + dy
            new_dist = max(abs(nx - target.x), abs(ny - target.y))
            
            if new_dist < current_dist:
                if engine.move_entity(me, nx, ny):
                    engine.log(f"{me.name} advances.")
                    return

    @staticmethod
    def _move_away(me, target, engine):
        """Greedy pathfinding away from target."""
        candidates = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        random.shuffle(candidates)
        
        current_dist = max(abs(me.x - target.x), abs(me.y - target.y))
        
        for dx, dy in candidates:
            nx, ny = me.x + dx, me.y + dy
            new_dist = max(abs(nx - target.x), abs(ny - target.y))
            
            if new_dist > current_dist: # Determine if step increases distance
                if engine.move_entity(me, nx, ny):
                    engine.log(f"{me.name} retreats!")
                    return

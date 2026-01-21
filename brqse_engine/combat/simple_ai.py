from typing import List
from brqse_engine.combat.combat_engine import CombatEngine
from brqse_engine.combat.combatant import Combatant

class SimpleAI:
    """
    Adapts the tactical logic for the new CombatEngine (Phase C).
    Driver for the simulation.
    """
    
    @staticmethod
    def execute_turn(me: Combatant, engine: CombatEngine):
        """
        Performs a full turn for the combatant.
        1. Identify Target
        2. Move
        3. Attack
        """
        log = []
        
        # 1. Identify Target (Closest Enemy)
        targets = []
        for c in engine.combatants:
            if c.is_alive and c.team != me.team:
                dist = abs(me.x - c.x) + abs(me.y - c.y)
                targets.append((dist, c))
        
        if not targets:
            engine.log(f"{me.name} sees no enemies.")
            return

        # Sort by distance
        targets.sort(key=lambda x: x[0])
        closest_dist, target = targets[0]
        
        # 2. Strategy: Close to 1 Range
        # TODO: Check Weapon Range
        desired_range = 1
        
        if closest_dist > desired_range:
            # Move towards target
            # Simple pathfinding: X then Y
            dx = target.x - me.x
            dy = target.y - me.y
            
            step_x = 1 if dx > 0 else -1 if dx < 0 else 0
            step_y = 1 if dy > 0 else -1 if dy < 0 else 0
            
            # Try X first
            new_x = me.x + step_x
            if engine.move_entity(me, new_x, me.y):
                engine.log(f"{me.name} moves to ({me.x}, {me.y}).")
            elif engine.move_entity(me, me.x, me.y + step_y):
                 engine.log(f"{me.name} moves to ({me.x}, {me.y}).")
            else:
                 engine.log(f"{me.name} is blocked.")
                 
            # Recalculate distance
            closest_dist = abs(me.x - target.x) + abs(me.y - target.y)

        # 3. Attack if in range
        if closest_dist <= desired_range:
            # Check Weapon Stat (Default Might, check Finesse/etc if needed)
            # For now default to Might
            engine.execute_attack(me, target, "Might")

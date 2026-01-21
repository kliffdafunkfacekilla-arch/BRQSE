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
        elif archetype == "Social":
            SimpleAI._ai_social_manipulator(me, engine)
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
        Strategy: Tactical. 
        1. If not in cover/defensible: Move to nearest Cover.
        2. If in cover or no cover reachable: Attack nearest enemy (Ranged pref).
        """
        # 1. Check if currently in cover
        current_tile = engine.tiles[me.y][me.x]
        if current_tile.effect == "cover":
             # Already in cover. Attack!
             SimpleAI._ai_ranged_sniper(me, engine) # Use Sniper logic for kiting/shooting
             return

        # 2. Find Cover
        cover_tile = SimpleAI._find_best_cover(me, engine)
        if cover_tile:
             cx, cy = cover_tile
             # Move towards cover
             dist_to_cover = max(abs(me.x - cx), abs(me.y - cy))
             if dist_to_cover <= 1: # Can reach it
                 if engine.move_entity(me, cx, cy):
                     engine.log(f"{me.name} takes cover!")
                     # Try to attack after moving? (If Actions allow - Simulating standard action economy)
                     # For now, SimpleAI is 1 Action per turn. Move OR Attack usually? 
                     # Actually execute_turn does 1 thing. 
                     # Let's verify standard rules. BrqSE is usually Move+Action.
                     # But SimpleAI methods usually do one or the other.
                     # Let's assume Move takes "Movement" and we can still Attack.
                     # But _ai_ranged_sniper does logic: Move THEN Attack.
                     # We should replicate that.
                     SimpleAI._ai_ranged_sniper(me, engine)
                     return
             else:
                 # Move towards it
                 SimpleAI._move_towards(me, type('Obj', (object,), {'x': cx, 'y': cy}), engine, range=0)
                 return
        
        # Fallback: Be a Sniper (Keep distance)
        SimpleAI._ai_ranged_sniper(me, engine)

    @staticmethod
    def _find_best_cover(me: Combatant, engine: CombatEngine):
        """Returns (x, y) of nearest unoccupied cover tile."""
        best_tile = None
        min_dist = 999
        
        for r in range(engine.rows):
            for c in range(engine.cols):
                tile = engine.tiles[r][c]
                if tile.effect == "cover":
                     # Check if occupied
                     is_occupied = False
                     for comb in engine.combatants:
                         if comb.x == c and comb.y == r and comb != me:
                             is_occupied = True
                             break
                     if is_occupied: continue
                     
                     dist = max(abs(me.x - c), abs(me.y - r))
                     if dist < min_dist:
                         min_dist = dist
                         best_tile = (c, r)
        
        return best_tile

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

    @staticmethod
    def _ai_social_manipulator(me: Combatant, engine: CombatEngine):
        """
        Strategy: Social Combat.
        Uses words instead of weapons. Targets Composure.
        """
        targets = SimpleAI._get_targets(me, engine)
        if not targets: return
        
        dist, target = targets[0]
        
        # Social maneuvers work at any range (within reason)
        # Pick the best maneuver based on the situation
        maneuvers = list(engine.social_maneuvers.keys())
        if not maneuvers:
            # Fallback to physical if no maneuvers loaded
            SimpleAI._ai_melee_berserker(me, engine)
            return
        
        # Priority: If target is already damaged, use "Call Out" for crit damage
        # Otherwise use "Gaslight" to debuff
        if target.is_bloodied and "Call Out" in maneuvers:
            chosen = "Call Out"
        elif "Gaslight" in maneuvers:
            chosen = "Gaslight"
        elif "Grandstand" in maneuvers:
            chosen = "Grandstand"
        else:
            chosen = random.choice(maneuvers)
        
        # Move closer if too far (social range ~8 tiles for "shouting distance")
        if dist > 8:
            SimpleAI._move_towards(me, target, engine, desired_range=5)
        
        # Execute social maneuver
        engine.execute_social_maneuver(me, target, chosen)

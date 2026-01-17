
import random
import math

class AIDecisionEngine:
    """
    Handles tactical decision making for AI combatants.
    """
    def __init__(self):
        pass

    def evaluate_turn(self, combatant, engine):
        """
        Main entry point for AI thinking.
        Returns a list of log strings.
        """
        log = [f"[AI] {combatant.name} is thinking..."]
        
        # 1. Analyze Battlefield
        context = self.analyze_battlefield(combatant, engine)
        
        # 2. Determine Strategy (Behavior Template)
        template = combatant.data.get("AI", "Aggressive")
        
        # 3. Select Action
        action_log = self.select_action(combatant, context, template, engine)
        log.extend(action_log)
        
        return log

    def analyze_battlefield(self, me, engine):
        """
        Gathers context: visible enemies, allies, health states, clusters.
        """
        enemies = []
        allies = []
        
        # Simple Faction logic: If I am "Enemy", players are enemies.
        # Ideally combatants have a 'team' attribute. 
        # For now assuming: me.team != other.team
        my_team = getattr(me, "team", "Enemy") 
        
        for c in engine.combatants:
            if not c.is_alive(): continue
            if c == me: continue
            
            c_team = getattr(c, "team", "Player")
            dist = max(abs(me.x - c.x), abs(me.y - c.y))
            
            info = {"obj": c, "dist": dist, "hp_pct": c.hp / c.max_hp}
            
            if c_team == my_team:
                allies.append(info)
            else:
                enemies.append(info)
                
        # Find Clusters (simplified: count enemies within 2 tiles of each other)
        # This is n^2 but n is small.
        clusters = []
        for e in enemies:
            count = 0
            start_x, start_y = e["obj"].x, e["obj"].y
            for other in enemies:
                if max(abs(start_x - other["obj"].x), abs(start_y - other["obj"].y)) <= 2:
                    count += 1
            if count > 1:
                clusters.append({"center": e["obj"], "count": count})
        
        clusters.sort(key=lambda x: x["count"], reverse=True)
        
        return {
            "enemies": sorted(enemies, key=lambda x: x["dist"]), # Closest first
            "allies": sorted(allies, key=lambda x: x["hp_pct"]), # Lowest HP first
            "clusters": clusters,
            "my_hp_pct": me.hp / me.max_hp
        }

    def select_action(self, me, ctx, template, engine):
        """
        Executes the best action based on template priorities.
        """
        log = []
        
        # --- BEHAVIOR: CASTER ---
        if template == "Caster":
            # Priority 1: Survival (Self Heal)
            if ctx["my_hp_pct"] < 0.3:
                if self._try_cast_heal(me, me, engine, log): return log
                # Or Flee?
            
            # Priority 2: Support (Heal Ally)
            for ally in ctx["allies"]:
                if ally["hp_pct"] < 0.5:
                    if self._try_cast_heal(me, ally["obj"], engine, log): return log

            # Priority 3: Crowd Control (Clusters)
            if ctx["clusters"] and ctx["clusters"][0]["count"] >= 2:
                target = ctx["clusters"][0]["center"]
                if self._try_cast_aoe(me, target, engine, log): return log

            # Priority 4: Attack Closest
            if ctx["enemies"]:
                target = ctx["enemies"][0]["obj"]
                self._basic_attack_routine(me, target, engine, log)
                return log

        # --- BEHAVIOR: BRUTE / TACTICAL ---
        elif template == "Tactical":
            # Priority 1: Charge/Engage
            # TODO: Implement Skills check (Dash, Charge)
            pass
            
        # --- FALLBACK: AGGRESSIVE ---
        # Default behavior for "Aggressive" or fallback
        if ctx["enemies"]:
            target = ctx["enemies"][0]["obj"] # Closest
            self._basic_attack_routine(me, target, engine, log)
        else:
            log.append("[AI] No targets visible.")
            
        return log

    def _basic_attack_routine(self, me, target, engine, log):
        """Standard Move & Attack logic"""
        dist = max(abs(me.x - target.x), abs(me.y - target.y))
        
        # Move if needed
        if dist > 1:
            # Simple pathfinding toward target
            dx, dy = target.x - me.x, target.y - me.y
            step_x = 1 if dx > 0 else -1 if dx < 0 else 0
            step_y = 1 if dy > 0 else -1 if dy < 0 else 0
            
            # Try to move adjacent
            # TODO: Better pathfinding around walls
            new_x, new_y = me.x + step_x, me.y + step_y
            
            success, msg = engine.move_char(me, new_x, new_y)
            log.append(f"[AI] Move: {msg}")
            
            # Re-eval distance
            dist = max(abs(me.x - target.x), abs(me.y - target.y))

        # Attack if possible
        if dist <= 1:
             # Melee
             log.extend(engine.attack_target(me, target))
        else:
             # TODO: Ranged check
             log.append(f"[AI] Closing distance to {target.name}")

    def _try_cast_heal(self, me, target, engine, log):
        """
        Attempts to find and cast a healing spell.
        Returns True if successful.
        """
        # Look for "Heal" keyword in powers/spells (assuming string list for now)
        # In full system, this checks Ability objects with tags.
        # Simulating a check:
        # For now, we can inject a "Heal" spell if Species/Class allows, or check existing.
        
        # Stub: If 'Heal' is in known powers/actions
        # For prototype, let's assume 'Caster' has 'Heal'
        if "Heal" in me.powers or "Heal" in me.skills or me.data.get("Class") == "Cleric":
             # Execute Heal logic via Registry Resolve?
             # Or engine.use_ability?
             # Let's assume we invoke the effect registry pattern "Heal 1d8 HP"
             
             dist = max(abs(me.x - target.x), abs(me.y - target.y))
             if dist > 5: # Range check
                 log.append(f"[AI] Ally {target.name} too far to heal.")
                 return False
                 
             # MECHANIC: Resolve "Heal 1d8 HP" on target
             ctx = {"engine": engine, "attacker": me, "target": target, "log": log}
             from abilities.effects_registry import registry
             registry.resolve("Heal 2d6 HP", ctx) # Hardcoded spell for AI test
             log.append(f"[AI] Cast [Heal] on {target.name}!")
             return True
             
        return False

    def _try_cast_aoe(self, me, center_target, engine, log):
        """
        Attempts to cast AoE (Fireball/Spore Cloud)
        """
        # Stub check
        # Assuming "Fireball" or "Spore Cloud"
        
        dist = max(abs(me.x - center_target.x), abs(me.y - center_target.y))
        if dist > 10: return False # Out of range
        
        # Resolve Spore Cloud as test
        ctx = {"engine": engine, "attacker": me, "target": center_target, "log": log}
        from abilities.effects_registry import registry
        
        # If Plant -> Spore Cloud
        if me.data.get("Species") == "Plant" or "Spore Cloud" in me.powers:
             registry.resolve("Release spores", ctx)
             return True
        elif "Fireball" in me.powers:
             # registry.resolve("Fireball", ctx) # Need fireball handler
             pass
             
        return False

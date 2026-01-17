
import random
import math
import os
import csv

class Behavior:
    AGGRESSIVE = "AGGRESSIVE" # Rush and Attack
    RANGED = "RANGED"         # Maintain distance, kite
    CAMPER = "CAMPER"         # Hold position, attack if in range
    FLEEING = "FLEEING"       # Run away
    CASTER = "CASTER"         # Prioritize Spells, Kite
    SPELLBLADE = "SPELLBLADE" # Melee + Spells (Touch/Buffs)

class EnemyAI:
    def __init__(self, engine):
        self.engine = engine
        self.weapon_data = self._load_weapon_data()

    def _load_weapon_data(self):
        db = {}
        # Path relative to this file: ../Data/weapons_and_armor.csv
        # This file is in AI/enemy_ai.py, so ../Data is correct
        path = os.path.join(os.path.dirname(__file__), "../Data/weapons_and_armor.csv")
        if not os.path.exists(path): return db
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get("Name")
                    if not name: continue
                    
                    tags = row.get("Logic_Tags", "")
                    
                    # Parse Range
                    max_range = 1.5 # Default Melee
                    if "RANGE:" in tags:
                        for t in tags.split('|'):
                            if t.startswith("RANGE:"):
                                val = t.split(':')[1]
                                # Handle "30/120" or "15:Cone"
                                if '/' in val: 
                                    max_range = float(val.split('/')[0]) / 5.0 # Convert ft to tiles (5ft/tile)
                                elif ':' in val: # Cone
                                    max_range = float(val.split(':')[0]) / 5.0
                                else:
                                    try: max_range = float(val) / 5.0
                                    except: pass
                                break
                    elif "PROP:Reach" in tags:
                        max_range = 2.0
                        
                    db[name] = {"range": max_range, "tags": tags}
        except: pass
        return db

    def get_optimal_range(self, character):
        # Look at inventory, find weapon with max range
        best_range = 1.5
        for item in character.inventory:
            if item in self.weapon_data:
                r = self.weapon_data[item]["range"]
                if r > best_range: best_range = r
        return best_range

    def take_turn(self, character, behavior=None):
        """
        Executes turn based on behavior.
        If behavior is None, pick one based on stats/gear.
        """
        log = []
        
        # Auto-detect behavior if not set
        if not behavior:
            # Check for high mental stats or many powers?
            has_powers = len(character.powers) > 0
            opt_range = self.get_optimal_range(character)
            
            if character.hp < character.max_hp * 0.2:
                behavior = Behavior.FLEEING
            elif has_powers and opt_range > 1.5:
                behavior = Behavior.CASTER
            elif has_powers and opt_range <= 1.5:
                 behavior = Behavior.SPELLBLADE
            elif opt_range > 2.0:
                behavior = Behavior.RANGED
            else:
                behavior = Behavior.AGGRESSIVE
                
        log.append(f"[AI] {character.name} acting as {behavior}...")
        
        target = self.find_closest_hostile(character)
        if not target and behavior != Behavior.FLEEING:
            log.append(f"{character.name} waits (No targets).")
            return log

        if behavior == Behavior.AGGRESSIVE:
            self._run_aggressive(character, target, log)
        elif behavior == Behavior.RANGED:
             self._run_ranged(character, target, log)
        elif behavior == Behavior.CAMPER:
             self._run_camper(character, target, log)
        elif behavior == Behavior.FLEEING:
             self._run_fleeing(character, target, log)
        elif behavior == Behavior.CASTER:
             self._run_caster(character, target, log)
        elif behavior == Behavior.SPELLBLADE:
             self._run_spellblade(character, target, log)
             
        return log

    def decide_ability(self, char, target, aggressive=True, forced=False):
        """
        Heuristic to pick an ability to use.
        Returns capability string or None.
        forced=True means 70% chance instead of 30%.
        """
        options = []
        if char.powers: options.extend(char.powers)
        if not options: return None
        
        chance = 0.7 if forced else 0.3
        
        if random.random() < chance:
            return random.choice(options)
            
        return None

    def _run_aggressive(self, char, target, log):
        # Move to Melee (1.5)
        dist = self.get_distance(char, target)
        if dist > 1.5 and char.movement_remaining > 0:
            self.move_towards(char, target, 1.5, log)
            dist = self.get_distance(char, target) 
            
        # Try Ability First
        ability = self.decide_ability(char, target, forced=False)
        if ability:
            log.extend(self.engine.activate_ability(char, ability, target))
        elif dist <= 1.5: 
            log.extend(self.engine.attack_target(char, target))
        else:
            log.append("Target too far to attack.")

    def _run_ranged(self, char, target, log):
        opt_range = self.get_optimal_range(char)
        dist = self.get_distance(char, target)
        
        if dist > opt_range and char.movement_remaining > 0:
            self.move_towards(char, target, opt_range, log)
        elif dist < 3.0 and opt_range > 5.0 and char.movement_remaining > 0:
            self.move_away(char, target, log)
            
        dist = self.get_distance(char, target)
        
        ability = self.decide_ability(char, target, forced=False)
        if ability:
            log.extend(self.engine.activate_ability(char, ability, target))
        elif dist <= opt_range:
            log.extend(self.engine.attack_target(char, target))
        else:
            log.append("Target out of range.")

    def _run_camper(self, char, target, log):
        opt_range = self.get_optimal_range(char)
        dist = self.get_distance(char, target)
        
        ability = self.decide_ability(char, target, forced=True) # Defenders use abilities more?
        if ability and dist <= 10.0:
             log.extend(self.engine.activate_ability(char, ability, target))
        elif dist <= opt_range:
             log.extend(self.engine.attack_target(char, target))
        else:
             log.append("Holding position (Camper).")

    def _run_fleeing(self, char, target, log):
        if target:
            self.move_away(char, target, log)
        log.append("Panic!")

    def _run_caster(self, char, target, log):
        # Like Ranged, but prioritizes Abilities 100% and keeps separate range
        # Assume Spell Range ~ 6-8 tiles
        spell_range = 6.0
        dist = self.get_distance(char, target)
        
        # Kite logic
        if dist > spell_range and char.movement_remaining > 0:
            self.move_towards(char, target, spell_range, log)
        elif dist < 4.0 and char.movement_remaining > 0: # More cautious than archer
             self.move_away(char, target, log)
             
        # Always try ability
        ability = self.decide_ability(char, target, forced=True)
        if ability:
             log.extend(self.engine.activate_ability(char, ability, target))
        else:
            # Fallback to weapon
            opt_range = self.get_optimal_range(char)
            if dist <= opt_range:
                log.extend(self.engine.attack_target(char, target))
            else:
                log.append("No spells available/affordable.")

    def _run_spellblade(self, char, target, log):
        # Rusher logic, but high spell use
        dist = self.get_distance(char, target)
        if dist > 1.5 and char.movement_remaining > 0:
            self.move_towards(char, target, 1.5, log)
            dist = self.get_distance(char, target)
            
        ability = self.decide_ability(char, target, forced=True)
        if ability:
             log.extend(self.engine.activate_ability(char, ability, target))
        elif dist <= 1.5:
             log.extend(self.engine.attack_target(char, target))
        else:
             log.append("Target too far.")

    # --- Helpers ---

    def move_towards(self, char, target, target_dist, log):
        while char.movement_remaining >= 5: 
            curr_dist = self.get_distance(char, target)
            if curr_dist <= target_dist: break
            
            dx = target.x - char.x
            dy = target.y - char.y
            
            step_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
            step_y = 1 if dy > 0 else (-1 if dy < 0 else 0)
            
            if abs(dx) >= abs(dy):
                nx, ny = char.x + step_x, char.y
            else:
                nx, ny = char.x, char.y + step_y
                
            success, msg = self.engine.move_char(char, nx, ny)
            if success: pass
            else:
                if abs(dx) >= abs(dy): nx, ny = char.x, char.y + step_y
                else: nx, ny = char.x + step_x, char.y
                success, msg = self.engine.move_char(char, nx, ny)
                if not success: break 

    def move_away(self, char, target, log):
        while char.movement_remaining >= 5:
            dx = char.x - target.x 
            dy = char.y - target.y
            if dx == 0 and dy == 0: dx = 1 
            step_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
            step_y = 1 if dy > 0 else (-1 if dy < 0 else 0)
            nx, ny = char.x + step_x, char.y + step_y
            success, msg = self.engine.move_char(char, nx, ny)
            if not success: break

    def find_closest_hostile(self, character):
        others = [c for c in self.engine.combatants if c != character and c.is_alive()]
        if not others: return None
        others.sort(key=lambda t: self.get_distance(character, t))
        return others[0]

    def get_distance(self, c1, c2):
        return math.sqrt((c1.x - c2.x)**2 + (c1.y - c2.y)**2)

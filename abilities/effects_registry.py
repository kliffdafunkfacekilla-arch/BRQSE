
import re
import random

class EffectRegistry:
    def __init__(self):
        # List of (regex_pattern, handler_function)
        self.patterns = []
        self._register_defaults()

    def register_pattern(self, regex, handler):
        self.patterns.append((re.compile(regex, re.IGNORECASE), handler))

    def resolve(self, effect_desc, context):
        """
        Attempts to resolve an effect description into an action.
        context: dict containing 'attacker', 'target', 'engine', 'damage', etc.
        """
        if not effect_desc: return False
        
        handled = False
        for pattern, handler in self.patterns:
            match = pattern.search(effect_desc)
            if match:
                # Pass match groups + context to handler
                try:
                    handler(match, context)
                    handled = True
                    # Don't break immediately, some descriptions might have multiple parts? 
                    # For now, let's assume one main effect per line/desc or break if handled.
                    break 
                except Exception as e:
                    print(f"[EffectRegistry] Error handling '{effect_desc}': {e}")
        
        if not handled:
            # Fallback for logging
            # print(f"[EffectRegistry] Unhandled effect: {effect_desc}")
            pass
        return handled

    def _register_defaults(self):
        # --- DAMAGE ---
        self.register_pattern(r"Deal (\d+)?d?(\d+)? ?(\w+) Damage", self._handle_deal_damage)
        self.register_pattern(r"(\w+) Damage", self._handle_simple_damage) # e.g. "Fire Damage" implies modifying attack?
        
        # --- ATTACK MODIFIERS ---
        self.register_pattern(r"\+(\d+) to Hit", self._handle_to_hit_bonus)
        self.register_pattern(r"-(\d+) to Hit", self._handle_to_hit_penalty)
        self.register_pattern(r"Auto-Hit", self._handle_auto_hit)
        self.register_pattern(r"Auto-Crit", self._handle_auto_crit)
        self.register_pattern(r"Disadvantage", self._handle_disadvantage)
        self.register_pattern(r"Advantage", self._handle_advantage)
        
        # --- DEFENSE / RESIST ---
        self.register_pattern(r"Resistance to (\w+)", self._handle_resistance)
        self.register_pattern(r"Immune to (\w+)", self._handle_immunity)
        self.register_pattern(r"Reduce damage.*half", self._handle_halve_damage)
        
        # --- STATUS ---
        self.register_pattern(r"Prone", self._handle_prone)
        self.register_pattern(r"Grapple", self._handle_grapple)
        self.register_pattern(r"Blind", self._handle_blind)
        self.register_pattern(r"Restrained", self._handle_restrained)
        self.register_pattern(r"Stun", self._handle_stun)
        self.register_pattern(r"Paralyze", self._handle_paralyze)
        self.register_pattern(r"Poison", self._handle_poison)
        self.register_pattern(r"Fear|Frightened", self._handle_fear)
        self.register_pattern(r"Charm", self._handle_charm)
        self.register_pattern(r"Deafen", self._handle_deafen)
        
        # --- HEALING & RESOURCES ---
        self.register_pattern(r"Heal (\d+)?d?(\d+)? ?(HP)?", self._handle_heal)
        self.register_pattern(r"Regain (\d+)?d?(\d+)? ?(HP)?", self._handle_heal)
        self.register_pattern(r"Temp(?:orary)? HP", self._handle_temp_hp)
        
        # --- BUFFS / DEBUFFS ---
        self.register_pattern(r"\+(\d+) (AC|Armor Class)", self._handle_ac_buff)
        self.register_pattern(r"Increase (Might|Reflexes|Endurance|Vitality|Fortitude|Knowledge|Logic|Awareness|Intuition|Charm|Willpower|Finesse)", self._handle_stat_buff)
        self.register_pattern(r"Advantage on (.*) Checks", self._handle_skill_advantage)
        self.register_pattern(r"Immune to Critical", self._handle_crit_immunity)
        
        # --- MOVEMENT ---
        self.register_pattern(r"Push.*?(\d+)ft", self._handle_push)
        self.register_pattern(r"Knock.*?back.*?(\d+)ft", self._handle_push)
        self.register_pattern(r"Teleport.*?(\d+)ft", self._handle_teleport)
        self.register_pattern(r"Fly Speed", self._handle_fly_speed)
        self.register_pattern(r"Swim Speed", self._handle_swim_speed)
        self.register_pattern(r"Climb Speed", self._handle_climb_speed)
        
        # --- UTILITY ---
        self.register_pattern(r"Invisible|Invisibility", self._handle_invisibility)
        self.register_pattern(r"Darkvision", self._handle_darkvision)
        self.register_pattern(r"Light", self._handle_light)

        # --- COSTS ---
        self.register_pattern(r"Cost:? (\d+) (SP|FP|CMP|HP)", self._handle_cost)

        # --- USER REQUESTED MECHANICS ---
        self.register_pattern(r"Attack own Ally", self._handle_confused)
        self.register_pattern(r"Berserk \(Attack All\)", self._handle_berserk)
        self.register_pattern(r"Force Attack", self._handle_taunt)
        self.register_pattern(r"Sanctuary \(No Attack\)", self._handle_sanctuary)
        self.register_pattern(r"Attack chains", self._handle_chain_attack)
        self.register_pattern(r"Bonus to AC vs one", self._handle_temp_ac_advantage)
        self.register_pattern(r"Line attack", self._handle_line_attack)
        self.register_pattern(r"Redirect attack", self._handle_redirect)
        self.register_pattern(r"Attack every target", self._handle_aoe_attack)
        self.register_pattern(r"Line Charge", self._handle_charge)
        self.register_pattern(r"Multi-hit attack", self._handle_multihit)
        self.register_pattern(r"Rapid aging", self._handle_aging)
        self.register_pattern(r"Reflect Hit", self._handle_reflect)
        # --- COMPLEX / REACTIVE ---
        self.register_pattern(r"Move 5ft when hit", self._handle_reactive_move)
        self.register_pattern(r"Drop to 0 HP.*?Attack", self._handle_death_attack)
        self.register_pattern(r"Ignore Resistance", self._handle_ignore_resistance)
        self.register_pattern(r"Ignore.*?Armor Class", self._handle_ignore_ac_bonuses)
        self.register_pattern(r"Ignore.*?Cover", self._handle_ignore_cover)
        self.register_pattern(r"Critical Hit on.*?19", self._handle_crit_range_19)
        self.register_pattern(r"Attack two adjacent", self._handle_cleave)
        self.register_pattern(r"Reach.*?(\d+)ft", self._handle_reach)
        self.register_pattern(r"Cannot be Surprised", self._handle_alert)
        self.register_pattern(r"Immune to.*?Critical", self._handle_crit_immunity)
        
        # --- UTILITY / FLAVOR ---
        self.register_pattern(r"Grow a magical fruit", self._handle_create_item_fruit)
        self.register_pattern(r"Heavily Obscured", self._handle_obscurement)
        self.register_pattern(r"Breathe underwater", self._handle_breathe_water)
        self.register_pattern(r"Hold breath", self._handle_hold_breath)
        self.register_pattern(r"Climb Speed|Walk on walls", self._handle_climb_speed)
        self.register_pattern(r"Burrow Speed", self._handle_burrow_speed)
        self.register_pattern(r"See in Darkness", self._handle_darkvision)
        self.register_pattern(r"Tremorsense|Detect.*?location", self._handle_tremorsense)
        self.register_pattern(r"Natural Armor.*?(\d+)", self._handle_natural_armor_formula) # 13+Dex



    # --- NEW HANDLERS ---
    
    def _handle_cost(self, match, ctx):
        amt = int(match.group(1))
        res_type = match.group(2).upper()
        
        user = ctx.get("attacker")
        if not user: return # Should not happen in activation context
        
        # Check current value
        current_val = 0
        if res_type == "SP": current_val = user.sp 
        elif res_type == "FP": current_val = user.fp
        elif res_type == "CMP": current_val = user.cmp
        elif res_type == "HP": current_val = user.hp
        
        if current_val < amt:
            # FAIL activation
            # We need a way to signal failure to the engine.
            # Currently resolve() returns True if handled.
            # We might need to raise a specific exception or set a flag in context.
            if "log" in ctx: ctx["log"].append(f"Not enough {res_type}! Need {amt}.")
            raise Exception(f"Insufficient {res_type}")
            
        # Deduct
        if res_type == "SP": user.sp -= amt
        elif res_type == "FP": user.fp -= amt
        elif res_type == "CMP": user.cmp -= amt
        elif res_type == "HP": user.hp -= amt
        
        if "log" in ctx: ctx["log"].append(f"Consumed {amt} {res_type}")
    
    def _handle_heal(self, match, ctx):
        # "Heal 1d8 HP"
        print(f"DEBUG: Handle Heal Triggered with {match.groups()}")
        amt_str = match.group(1) or "1"
        die_str = match.group(2)
        
        target = ctx.get("attacker") # Usually self-heal, or target depending on context? 
        # CAREFUL: In ON_HIT, Attacker hits Target. "Heal" usually implies lifesteal OR self-buff?
        # Let's assume most effects like "Regeneration" apply to self (source of effect).
        # But a "Heal Spell" applies to Target.
        # Context is key. For now, default to applying to the entity that owns the effect?
        # But 'ctx' usually has 'attacker' and 'target'.
        # If it's a passive/active effect, 'attacker' is the user.
        
        user = ctx.get("attacker") or ctx.get("target")
        if not user: return

        heal = 0
        if die_str:
            num = int(amt_str)
            sides = int(die_str)
            heal = sum(random.randint(1, sides) for _ in range(num))
        else:
            heal = int(amt_str) if amt_str else 0
            
        user.hp = min(user.hp + heal, user.max_hp)
        if "log" in ctx: ctx["log"].append(f"Healed {heal} HP!")

    def _handle_temp_hp(self, match, ctx):
        # Simplified: just add to HP for now, or track separately
        user = ctx.get("attacker")
        if user:
            if "log" in ctx: ctx["log"].append("Gained Temp HP!")

    def _handle_stun(self, match, ctx):
        t = ctx.get("target")
        if t: 
            t.is_stunned = True # Need to add to Combatant
            if "log" in ctx: ctx["log"].append(f"{t.name} Stunned!")
            
    def _handle_paralyze(self, match, ctx):
        t = ctx.get("target")
        if t: 
            t.is_paralyzed = True
            if "log" in ctx: ctx["log"].append(f"{t.name} Paralyzed!")

    def _handle_poison(self, match, ctx):
        t = ctx.get("target")
        if t: 
            t.is_poisoned = True
            if "log" in ctx: ctx["log"].append(f"{t.name} Poisoned!")

    def _handle_fear(self, match, ctx):
        t = ctx.get("target")
        if t: 
            t.is_frightened = True
            if "log" in ctx: ctx["log"].append(f"{t.name} Frightened!")

    def _handle_charm(self, match, ctx):
        t = ctx.get("target")
        if t: 
            t.is_charmed = True
            if "log" in ctx: ctx["log"].append(f"{t.name} Charmed!")

    def _handle_deafen(self, match, ctx):
        t = ctx.get("target")
        if t: 
            t.is_deafened = True
            if "log" in ctx: ctx["log"].append(f"{t.name} Deafened!")

    def _handle_ac_buff(self, match, ctx):
        amt = int(match.group(1))
        # Need to know if this is a PASSIVE (permanent) or ON_DEFEND (temporary)
        # If context has 'incoming_attack', it's likely reactive.
        if "def_total" in ctx: # If we exposed def_total in mechanics context... we didn't yet.
             # mechanics.py calculates def_total internally.
             # We might need to modify 'def_mod' in ctx if we added it?
             # Currently mechanics.py doesn't expose def_mod in ctx.
             pass
        # Passive AC check?
        t = ctx.get("target") or ctx.get("attacker")
        if t:
            if "log" in ctx: ctx["log"].append(f"AC +{amt}")

    def _handle_stat_buff(self, match, ctx):
        stat = match.group(1)
        # Assuming passive upgrade?
        # This is tough without a proper "Apply Passives" phase or permanent modification.
        pass

    def _handle_skill_advantage(self, match, ctx):
        skill = match.group(1)
        if "log" in ctx: ctx["log"].append(f"Advantage on {skill}")

    def _handle_crit_immunity(self, match, ctx):
        if "is_crit" in ctx:
            ctx["is_crit"] = False
            if "log" in ctx: ctx["log"].append("Crit Negated!")

    def _handle_push(self, match, ctx):
        dist_ft = int(match.group(1))
        squares = dist_ft // 5
        target = ctx.get("target")
        attacker = ctx.get("attacker")
        
        if target and attacker and squares > 0:
            # Simple push away from attacker
            dx = target.x - attacker.x
            dy = target.y - attacker.y
            # Norm
            if dx == 0 and dy == 0: return 
            
            # Simple direction (cardinal/diagonal)
            dir_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
            dir_y = 1 if dy > 0 else (-1 if dy < 0 else 0)
            
            target.x += dir_x * squares
            target.y += dir_y * squares
            if "log" in ctx: ctx["log"].append(f"Pushed {dist_ft}ft!")

    def _handle_teleport(self, match, ctx):
        dist = int(match.group(1))
        # Needs UI interaction to pick spot? 
        # For now just log it as ability available.
        if "log" in ctx: ctx["log"].append(f"Can Teleport {dist}ft")

    def _handle_fly_speed(self, match, ctx):
        if "log" in ctx: ctx["log"].append("Has Fly Speed")

    def _handle_swim_speed(self, match, ctx):
        if "log" in ctx: ctx["log"].append("Has Swim Speed")

    def _handle_climb_speed(self, match, ctx):
        if "log" in ctx: ctx["log"].append("Has Climb Speed")

    def _handle_invisibility(self, match, ctx):
        user = ctx.get("attacker")
        if user:
            user.is_invisible = True
            if "log" in ctx: ctx["log"].append("Became Invisible!")

    def _handle_darkvision(self, match, ctx):
        pass # Passive
        
    def _handle_light(self, match, ctx):
        if "log" in ctx: ctx["log"].append("Emits Light")
        
    # --- USER DEFINED HANDLERS ---
    
    def _handle_confused(self, match, ctx):
        # "Attack own Ally"
        # Since we don't have AI states fully exposed in 'ctx', we log it.
        # But if we had a flag on the combatant, the AI decision loop could use it.
        target = ctx.get("target")
        if target:
            target.is_confused = True
            if "log" in ctx: ctx["log"].append(f"{target.name} is Confused (Attacks Ally)!")

    def _handle_berserk(self, match, ctx):
        target = ctx.get("target")
        if target:
            target.is_berserk = True
            if "log" in ctx: ctx["log"].append(f"{target.name} went Berserk!")

    def _handle_taunt(self, match, ctx):
        # "Force Attack" - Taunt
        target = ctx.get("target") # The victim of the taunt
        caster = ctx.get("attacker") # The one casting it
        if target and caster:
            target.taunted_by = caster # Store reference? Or Name
            if "log" in ctx: ctx["log"].append(f"{target.name} Taunted by {caster.name}!")

    def _handle_sanctuary(self, match, ctx):
        # "Sanctuary (No Attack)"
        # Apply to target (or self if buff)
        user = ctx.get("attacker") 
        if user:
            user.is_sanctuary = True
            if "log" in ctx: ctx["log"].append(f"{user.name} has Sanctuary!")

    def _handle_chain_attack(self, match, ctx):
        if "log" in ctx: ctx["log"].append("Effect: Chain Lightning (Not fully impl)")

    def _handle_temp_ac_advantage(self, match, ctx):
        # "Bonus to AC vs one attack" -> Advantage on Defense
        # Mechanics supports "advantage" in ctx, but that's usually for the ATTACKER.
        # Defending with advantage?
        # Mechanics.py: def_roll = random.randint(1, 20) ...
        # We need to set a flag in context like "defense_advantage"
        ctx["defense_advantage"] = True 
        if "log" in ctx: ctx["log"].append("Defensive Advantage!")

    def _handle_line_attack(self, match, ctx):
        if "log" in ctx: ctx["log"].append("Effect: Line Attack (Needs Geometry)")

    def _handle_redirect(self, match, ctx):
         if "log" in ctx: ctx["log"].append("Effect: Redirect Attack")

    def _handle_aoe_attack(self, match, ctx):
        if "log" in ctx: ctx["log"].append("Effect: Attack All Enemies")

    def _handle_charge(self, match, ctx):
        if "log" in ctx: ctx["log"].append("Effect: Line Charge")

    def _handle_multihit(self, match, ctx):
        # "Multi-hit attack"
        # This usually means rolling attack multiple times.
        # The engine calls 'attack_target' ONCE.
        # To do this correctly, 'mechanics.py' needs to support a loop or we call it recursively?
        # Recursion is dangerous here.
        if "log" in ctx: ctx["log"].append("Effect: Multi-Hit")

    def _handle_aging(self, match, ctx):
        # "Rapid aging... massive CMP dmg, -2 to 2 stats"
        target = ctx.get("target")
        if target:
            dmg = 10 # "Massive"
            target.cmp -= dmg
            # Stats (assuming permanent for session or track temp malus)
            # For now, just log the stat drop
            if "log" in ctx: ctx["log"].append(f"{target.name} Aged! -10 CMP, Stats Reduced.")

    def _handle_reflect(self, match, ctx):
        # "Reflect Hit to attacker"
        # Triggered on ON_DEFEND usually?
        attacker = ctx.get("attacker") # The one attacking the reflector
        # defender = ctx.get("target") # The reflector (who has this effect)
        # Wait, if this is a PASSIVE on the defender, then `ctx['target']` is the defender.
        # And `ctx['attacker']` is the enemy.
        # We want to deal damage back to `attacker`.
        dmg = ctx.get("incoming_damage", 0)
        if attacker and dmg > 0:
            attacker.hp -= dmg # Reflect full amount?
            if "log" in ctx: ctx["log"].append(f"Reflected {dmg} damage to {attacker.name}!")
            # Should we negate incoming? Usually reflect implies negation too or thorns?
            # "Reflect Hit" suggests bouncing it back.
            ctx["incoming_damage"] = 0 # Negate incoming

    def _handle_deflect_missile(self, match, ctx):
        # "Deflect Ranged Attack"
        # Check if attack is ranged?
        # We don't have 'is_ranged' in ctx yet, but we can assume checks elsewhere.
        # If triggered, we negate damage.
        ctx["incoming_damage"] = 0
        if "log" in ctx: ctx["log"].append("Ranged Attack Deflected!")    
    # --- NEW REACTIVE HANDLERS ---

    def _handle_reactive_move(self, match, ctx):
        # "Move 5ft when hit"
        # Triggered on ON_HIT or ON_DEFEND?
        # If I am the target, and I get hit...
        # allow me to move 5ft (1 square)
        # We can't pause for input easily, so let's just log it or auto-move away?
        if "log" in ctx: ctx["log"].append("Reaction: Can Move 5ft!")
        
    def _handle_death_attack(self, match, ctx):
        # "If you drop to 0 HP, make one immediate Stinger attack"
        # Checked on damage application? 
        # engine_hooks needs to trigger on "ON_DEATH" or check HP after hit.
        target = ctx.get("target")
        if target and target.hp <= 0:
            if "log" in ctx: ctx["log"].append("Death Trigger: Immediate Attack!")
            
    def _handle_ignore_resistance(self, match, ctx):
        ctx["ignore_resistance"] = True
        if "log" in ctx: ctx["log"].append("Ignores Resistance")

    def _handle_ignore_ac_bonuses(self, match, ctx):
        if "log" in ctx: ctx["log"].append("Ignores Shield/Armor Bonuses")
        # In mechanics, this would reduce target's effective AC

    def _handle_ignore_cover(self, match, ctx):
        ctx["ignore_cover"] = True
        if "log" in ctx: ctx["log"].append("Ignores Cover")

    def _handle_crit_range_19(self, match, ctx):
        ctx["crit_threshold"] = 19
        if "log" in ctx: ctx["log"].append("Crit on 19-20")

    def _handle_cleave(self, match, ctx):
        if "log" in ctx: ctx["log"].append("Effect: Attack Adjacent (Cleave)")

    def _handle_reach(self, match, ctx):
        reach = int(match.group(1))
        # Should modify attacker's reach property check in mechanics
        if "log" in ctx: ctx["log"].append(f"Reach {reach}ft")

    def _handle_alert(self, match, ctx):
        user = ctx.get("attacker") # Or target depending on who has the trait
        if user:
             user.cannot_be_surprised = True
             if "log" in ctx: ctx["log"].append("Alert: Cannot be Surprised")

    def _handle_create_item_fruit(self, match, ctx):
        if "log" in ctx: ctx["log"].append("Created Magical Fruit (Item)")

    def _handle_obscurement(self, match, ctx):
        if "log" in ctx: ctx["log"].append("Created Heavily Obscured Area (Fog)")

    def _handle_breathe_water(self, match, ctx):
        if "log" in ctx: ctx["log"].append("Can Breathe Underwater")

    def _handle_hold_breath(self, match, ctx):
         if "log" in ctx: ctx["log"].append("Can Hold Breath Long Time")

    def _handle_burrow_speed(self, match, ctx):
         if "log" in ctx: ctx["log"].append("Has Burrow Speed")

    def _handle_tremorsense(self, match, ctx):
         if "log" in ctx: ctx["log"].append("Has Tremorsense/Radar")

    def _handle_natural_armor_formula(self, match, ctx):
        # "Base Armor Class is 13 + Dex"
        # Complex to implement dynamically without a stat recalc phase.
        # Just log for now.
        base = int(match.group(1))
        if "log" in ctx: ctx["log"].append(f"Natural Armor Base {base}")
        
    def _handle_deal_damage(self, match, ctx):
        # Ex: Deal 1d6 Fire Damage
        amt_str = match.group(1) or "1" # Default count
        die_str = match.group(2) or "1" # Default sides/flat
        dmg_type = match.group(3)
        
        # This usually triggers in an ON_HIT context or ACTIVE context
        target = ctx.get("target")
        attacker = ctx.get("attacker")
        
        if target and attacker:
            # Calculate logic
            dmg = 0
            if match.group(2): # It was dice (XdY)
                num = int(amt_str)
                sides = int(die_str)
                dmg = sum(random.randint(1, sides) for _ in range(num))
            else: # It was flat? roughly
                dmg = int(amt_str) if amt_str else 0
                
            # Apply
            if "log" in ctx: ctx["log"].append(f"Effect ({dmg_type}): {dmg} damage to {target.name}!")
            else: ctx['engine'].log.append(f"Effect ({dmg_type}): {dmg} damage to {target.name}!")
            target.hp -= dmg
            
    def _handle_simple_damage(self, match, ctx):
        # Ex: "Fire Damage" (e.g. "Your attack deals Fire Damage")
        # In ON_ATTACK or ON_HIT, this might convert damage type
        dtype = match.group(1)
        if "damage_type" in ctx:
            ctx["damage_type"] = dtype
            
    def _handle_to_hit_bonus(self, match, ctx):
        bonus = int(match.group(1))
        if "attack_roll" in ctx:
            ctx["attack_roll"] += bonus
            ctx["log"].append(f"Effect: +{bonus} to Hit")

    def _handle_to_hit_penalty(self, match, ctx):
        malus = int(match.group(1))
        if "attack_roll" in ctx:
            ctx["attack_roll"] -= malus
            ctx["log"].append(f"Effect: -{malus} to Hit")
            
    def _handle_auto_hit(self, match, ctx):
        ctx["auto_hit"] = True
        ctx["log"].append("Effect: Auto-Hit!")

    def _handle_auto_crit(self, match, ctx):
        ctx["is_crit"] = True
        ctx["log"].append("Effect: Critical Hit!")

    def _handle_disadvantage(self, match, ctx):
        # Logic depends on system implementing adv/disadv
        ctx["disadvantage"] = True
        ctx["log"].append("Effect: Disadvantage Applied")

    def _handle_advantage(self, match, ctx):
        ctx["advantage"] = True
        ctx["log"].append("Effect: Advantage Applied")

    def _handle_resistance(self, match, ctx):
        dtype = match.group(1)
        # Should add to target's temp resistance list or modify incoming damage
        if "incoming_damage" in ctx and ctx.get("damage_type") == dtype:
            ctx["incoming_damage"] //= 2
            ctx["log"].append(f"Resisted {dtype}! Dmg Halved.")

    def _handle_immunity(self, match, ctx):
        dtype = match.group(1)
        if "incoming_damage" in ctx and ctx.get("damage_type") == dtype:
            ctx["incoming_damage"] = 0
            ctx["log"].append(f"Immune to {dtype}!")

    def _handle_halve_damage(self, match, ctx):
        if "incoming_damage" in ctx:
            ctx["incoming_damage"] //= 2
            ctx["log"].append("Damage Halved!")

    def _handle_prone(self, match, ctx):
        target = ctx.get("target")
        if target:
            target.is_prone = True # Requires wrapper/attribute on Combatant
            ctx["log"].append(f"{target.name} knocked Prone!")

    def _handle_grapple(self, match, ctx):
        target = ctx.get("target")
        if target:
            target.is_grappled = True
            ctx["log"].append(f"{target.name} Grappled!")

    def _handle_blind(self, match, ctx):
        target = ctx.get("target")
        if target:
            target.is_blinded = True
            ctx["log"].append(f"{target.name} Blinded!")
            
    def _handle_restrained(self, match, ctx):
        target = ctx.get("target")
        if target:
            target.is_restrained = True
            ctx["log"].append(f"{target.name} Restrained!")

# Singleton instance for easy access
registry = EffectRegistry()

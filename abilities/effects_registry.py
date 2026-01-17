
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
        self.register_pattern(r"\+(\d+)d(\d+) to Hit", self._handle_die_hit_bonus)
        self.register_pattern(r"-(\d+)d(\d+) to Hit", self._handle_die_hit_penalty)
        self.register_pattern(r"Damage Reduction.*?(\d+)", self._handle_damage_reduction)
        
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
        
        # --- SAVE EFFECTS ---
        self.register_pattern(r"save.*?or.*?(Prone|Frightened|Charmed|Blinded|Paralyzed|Poisoned|Stunned|Restrained|Deafened)", self._handle_save_condition)
        self.register_pattern(r"save.*?or.*?pushed.*?(\d+)ft", self._handle_save_push)
        self.register_pattern(r"save.*?or.*?half damage", self._handle_save_half_damage)
        self.register_pattern(r"save.*?or.*?(\d+)d?(\d+)? damage", self._handle_save_damage)
        
        # --- AOE / MULTI-TARGET ---
        self.register_pattern(r"(\d+)ft (cone|line|radius|sphere)", self._handle_aoe_shape)
        self.register_pattern(r"all (enemies|creatures|allies) (within|in) (\d+)ft", self._handle_aoe_targets)
        
        # --- SUMMON / CREATE ---
        self.register_pattern(r"summon|call|conjure", self._handle_summon)
        self.register_pattern(r"create (wall|barrier|cover)", self._handle_create_terrain)

        # ============================================
        # SCHOOL OF FLUX EFFECTS
        # ============================================
        
        # --- FLUX: PHASING & ETHEREAL ---
        self.register_pattern(r"Ethereal|No Phys(?:ical)? Dmg", self._handle_ethereal)
        self.register_pattern(r"[Pp]hase|[Pp]hasing", self._handle_phase)
        self.register_pattern(r"Walk through.*?(wall|solid)", self._handle_phase_walk)
        self.register_pattern(r"Amorphous|Immune Crits.*?Grap", self._handle_amorphous)
        
        # --- FLUX: DISPLACEMENT ---
        self.register_pattern(r"appear 5ft from|Displacement|Mirror Image", self._handle_displacement)
        
        # --- FLUX: DISINTEGRATE & DAMAGE ---
        self.register_pattern(r"Disintegrate", self._handle_disintegrate)
        self.register_pattern(r"Damage over Time|DoT|Bleed", self._handle_dot)
        self.register_pattern(r"Cut off|Sever.*?(limb|appendage)", self._handle_sever_limb)
        self.register_pattern(r"Compress.*?space|Gravity well|Pull enemies", self._handle_compress_space)
        
        # --- FLUX: ESCAPE & MOVEMENT ---
        self.register_pattern(r"Escape.*?(bindings|grapple|restraints)", self._handle_escape_grapple)
        self.register_pattern(r"Find path|Pathfinding", self._handle_find_path)
        
        # --- FLUX: ITEM MANIPULATION ---
        self.register_pattern(r"Force drop|Disarm", self._handle_disarm)
        self.register_pattern(r"Grab.*?(weapon|item|projectile)|Snatch|Catch.*?thrown", self._handle_snatch_projectile)
        self.register_pattern(r"Steal.*?(equipped|item)|Pickpocket", self._handle_steal_item)
        self.register_pattern(r"Switch.*?items|Swap.*?items", self._handle_switch_items)
        
        # --- FLUX: ARMOR PENETRATION ---
        self.register_pattern(r"Ignore.*?Armor|Ignore AR|Bypass Armor", self._handle_ignore_armor)
        self.register_pattern(r"Precision.*?knock.*?down", self._handle_precision_knockdown)
        self.register_pattern(r"Reduce.*?melee damage", self._handle_reduce_melee_damage)
        
        # --- FLUX: UTILITY ---
        self.register_pattern(r"Open.*?mechanism|Pick lock|Unlock", self._handle_open_mechanism)
        self.register_pattern(r"Clean.*?poison|Purify", self._handle_purify_liquid)
        self.register_pattern(r"Un-mix|Separate compound", self._handle_unmix_potion)

        # ============================================
        # ON_ATTACK REACTIVE EFFECTS
        # ============================================
        
        # --- ATTACK TRIGGERS ---
        self.register_pattern(r"crit(?:ical)? (?:hit )?range.*?19", self._handle_crit_range_19)
        self.register_pattern(r"attack.*?two adjacent|attack.*?2 adjacent", self._handle_attack_adjacent)
        self.register_pattern(r"flanking.*?attack|sting.*?flanking", self._handle_flanking_attack)
        self.register_pattern(r"enemy moves within.*?(\d+)ft.*?attack", self._handle_opportunity_attack)
        self.register_pattern(r"bonus.*?(\d+).*?Attack Rolls?.*?allies", self._handle_rally_allies)
        self.register_pattern(r"no penalt(?:y|ies).*?moving.*?Ranged", self._handle_mobile_shooter)
        self.register_pattern(r"piercing.*?19|crit.*?19.*?pierc", self._handle_piercing_crit)
        self.register_pattern(r"behind you.*?reflex attack", self._handle_tail_attack)
        self.register_pattern(r"shield.*?ally.*?overhead|shield.*?rain", self._handle_shield_ally)
        self.register_pattern(r"water.*?attack.*?not pushed|remain upright", self._handle_water_stability)
        
        # --- ON_HIT EFFECTS ---
        self.register_pattern(r"Magic Missile|Auto hit", self._handle_auto_hit)
        self.register_pattern(r"Damage scales.*?Speed", self._handle_speed_damage)
        self.register_pattern(r"Quick.*?low.*?damage|quick attack", self._handle_quick_attack)
        self.register_pattern(r"Enemy hits self|reflect.*?self", self._handle_self_hit)
        self.register_pattern(r"Miss hits Ally|miss.*?ally", self._handle_miss_ally)
        self.register_pattern(r"Auto-Damage|No Roll", self._handle_auto_damage)
        self.register_pattern(r"Weak Point|crit bonus", self._handle_weak_point)
        self.register_pattern(r"True Strike|Bonus to Hit", self._handle_true_strike)
        self.register_pattern(r"cannot be healed.*?non-magical|unhealable", self._handle_unhealable_wound)
        self.register_pattern(r"unarmed.*?head.*?shoved|headbutt.*?push", self._handle_headbutt)

        # ============================================
        # SCHOOL OF OMEN EFFECTS (Luck/Fate Magic)
        # ============================================
        
        # --- OMEN: LUCK MODIFIERS ---
        self.register_pattern(r"Jinx|bad luck", self._handle_jinx)
        self.register_pattern(r"Bless|good luck", self._handle_bless)
        self.register_pattern(r"Curse|Disadvantage on Rolls", self._handle_curse)
        self.register_pattern(r"Fate|Advantage on Rolls", self._handle_fate)
        self.register_pattern(r"Reroll 1s|Lucky", self._handle_lucky)
        self.register_pattern(r"Force Reroll|Take Low", self._handle_force_reroll)
        
        # --- OMEN: MISHAPS ---
        self.register_pattern(r"Trip|Cause Prone.*?Bad Luck", self._handle_luck_trip)
        self.register_pattern(r"Weapon Failure|Jam", self._handle_weapon_jam)
        self.register_pattern(r"Fumble|drops? item", self._handle_fumble)
        self.register_pattern(r"Backfire|Enemy hits self", self._handle_backfire)
        self.register_pattern(r"Ricochet|Miss hits Ally", self._handle_ricochet)
        
        # --- OMEN: FATE MANIPULATION ---
        self.register_pattern(r"Calamity|Crit Fail", self._handle_calamity)
        self.register_pattern(r"Miracle|Survive.*?1HP", self._handle_miracle)
        self.register_pattern(r"Doom|Instant Kill", self._handle_doom)
        self.register_pattern(r"Divine|Auto-Save", self._handle_divine_save)
        self.register_pattern(r"Favor|Auto.*?Natural 20", self._handle_auto_nat20)
        self.register_pattern(r"Karma|Reflect Hit", self._handle_karma)
        
        # --- OMEN: UTILITY ---
        self.register_pattern(r"Coin Flip|50/50|Guess", self._handle_coin_flip)
        self.register_pattern(r"Locate Object|Find", self._handle_locate)
        self.register_pattern(r"Danger Sense|Hunch", self._handle_danger_sense)
        self.register_pattern(r"Best Route|Path", self._handle_best_route)
        self.register_pattern(r"Random Buff|Gamble", self._handle_gamble)
        self.register_pattern(r"Find Loot|Serendipity", self._handle_serendipity)
        self.register_pattern(r"Talk to Dead|Spirit", self._handle_speak_dead)
        self.register_pattern(r"Hint.*?Future|Augury", self._handle_augury)
        self.register_pattern(r"Force.*?Roll|Destiny", self._handle_destiny)

        # ============================================
        # SCHOOL OF VITA EFFECTS (Life/Death Magic)
        # ============================================
        
        # --- VITA: HEALING ---
        self.register_pattern(r"Heal HP every turn|Regenerat", self._handle_regeneration)
        self.register_pattern(r"Heal minor wounds|Minor Heal", self._handle_minor_heal)
        self.register_pattern(r"Stasis Heal|Full recovery", self._handle_full_heal)
        self.register_pattern(r"Stop Bleeding|Clot", self._handle_stop_bleed)
        self.register_pattern(r"Cure Disease|Immunity", self._handle_cure_disease)
        self.register_pattern(r"Cure Poison|Antidote", self._handle_cure_poison)
        
        # --- VITA: LIFE MANIPULATION ---
        self.register_pattern(r"Lifesteal|Heal for Dmg|Drain Life", self._handle_lifesteal)
        self.register_pattern(r"Life Bond|Share HP", self._handle_life_bond)
        self.register_pattern(r"Auto-Life|on death", self._handle_auto_life)
        self.register_pattern(r"Resurrect|Revive|Bring back", self._handle_resurrect)
        self.register_pattern(r"Eat minion.*?heal|Consume ally", self._handle_consume_ally)
        
        # --- VITA: DEBUFFS & DAMAGE ---
        self.register_pattern(r"Inflict Disease|Plague", self._handle_inflict_disease)
        self.register_pattern(r"Necrotic damage|Wither", self._handle_necrotic)
        self.register_pattern(r"Drain Stat|Weaken", self._handle_stat_drain)
        self.register_pattern(r"Massive.*?DoT|Rot", self._handle_massive_dot)
        self.register_pattern(r"Spreading.*?infection|Contagion", self._handle_contagion)
        self.register_pattern(r"Kill creature type|Bane", self._handle_creature_bane)
        
        # --- VITA: BODY MODIFICATION ---
        self.register_pattern(r"Enlarge|Grow.*?size", self._handle_enlarge)
        self.register_pattern(r"Grow Gills|Grow Claws|Grow Wings", self._handle_grow_appendage)
        self.register_pattern(r"Natural Armor|skin.*?armor", self._handle_natural_armor)
        self.register_pattern(r"Turn into bugs|Swarm form", self._handle_swarm_form)
        self.register_pattern(r"Grow spare body|Clone", self._handle_clone)
        
        # --- VITA: UTILITY ---
        self.register_pattern(r"Animate.*?(Plant|Tree)|Awaken", self._handle_animate_plant)
        self.register_pattern(r"Create.*?Lifeform|Spawn", self._handle_create_life)
        self.register_pattern(r"Detect Life|Life Radar", self._handle_detect_life)
        self.register_pattern(r"Vines.*?restrict|Entangle", self._handle_vines)    # --- NEW HANDLERS ---
    
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
            duration = ctx.get("effect_duration", 1)
            if hasattr(t, "apply_effect"):
                t.apply_effect("Stunned", duration)
            else:
                t.is_stunned = True
            if "log" in ctx: ctx["log"].append(f"{t.name} Stunned for {duration} round(s)!")
            
    def _handle_paralyze(self, match, ctx):
        t = ctx.get("target")
        if t: 
            duration = ctx.get("effect_duration", 1)
            if hasattr(t, "apply_effect"):
                t.apply_effect("Paralyzed", duration)
            else:
                t.is_paralyzed = True
            if "log" in ctx: ctx["log"].append(f"{t.name} Paralyzed for {duration} round(s)!")

    def _handle_poison(self, match, ctx):
        t = ctx.get("target")
        if t: 
            duration = ctx.get("effect_duration", 3) # Poison lasts longer typically
            if hasattr(t, "apply_effect"):
                t.apply_effect("Poisoned", duration)
            else:
                t.is_poisoned = True
            if "log" in ctx: ctx["log"].append(f"{t.name} Poisoned for {duration} round(s)!")

    def _handle_fear(self, match, ctx):
        t = ctx.get("target")
        if t: 
            duration = ctx.get("effect_duration", 1)
            if hasattr(t, "apply_effect"):
                t.apply_effect("Frightened", duration)
            else:
                t.is_frightened = True
            if "log" in ctx: ctx["log"].append(f"{t.name} Frightened for {duration} round(s)!")

    def _handle_charm(self, match, ctx):
        t = ctx.get("target")
        if t: 
            duration = ctx.get("effect_duration", 1)
            if hasattr(t, "apply_effect"):
                t.apply_effect("Charmed", duration)
            else:
                t.is_charmed = True
            if "log" in ctx: ctx["log"].append(f"{t.name} Charmed for {duration} round(s)!")

    def _handle_deafen(self, match, ctx):
        t = ctx.get("target")
        if t: 
            duration = ctx.get("effect_duration", 1)
            if hasattr(t, "apply_effect"):
                t.apply_effect("Deafened", duration)
            else:
                t.is_deafened = True
            if "log" in ctx: ctx["log"].append(f"{t.name} Deafened for {duration} round(s)!")

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
        user = ctx.get("attacker") or ctx.get("target")
        if user:
            user.has_fly_speed = True
            if "log" in ctx: ctx["log"].append("Has Fly Speed")

    def _handle_swim_speed(self, match, ctx):
        user = ctx.get("attacker") or ctx.get("target")
        if user:
            user.has_swim_speed = True
            if "log" in ctx: ctx["log"].append("Has Swim Speed")

    def _handle_climb_speed(self, match, ctx):
        user = ctx.get("attacker") or ctx.get("target")
        if user:
            user.has_climb_speed = True
            if "log" in ctx: ctx["log"].append("Has Climb Speed")
    
    def _handle_burrow_speed(self, match, ctx):
        user = ctx.get("attacker") or ctx.get("target")
        if user:
            user.has_burrow_speed = True
            if "log" in ctx: ctx["log"].append("Has Burrow Speed")

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
        """Chain Lightning - hit primary target, then chain to nearest"""
        engine = ctx.get("engine")
        attacker = ctx.get("attacker")
        primary = ctx.get("target")
        if not engine or not attacker or not primary: return
        
        # Deal damage to primary (already done by main attack)
        # Find next nearest enemy and deal reduced damage
        chain_dmg = ctx.get("incoming_damage", 5) // 2  # Half damage to chain
        
        nearest = None
        min_dist = 999
        for c in engine.combatants:
            if c == attacker or c == primary or not c.is_alive(): continue
            dx = abs(c.x - primary.x)
            dy = abs(c.y - primary.y)
            dist = max(dx, dy)
            if dist < min_dist and dist <= 2:  # 10ft chain range
                min_dist = dist
                nearest = c
        
        if nearest:
            nearest.hp -= chain_dmg
            if "log" in ctx: ctx["log"].append(f"Chain hit {nearest.name} for {chain_dmg}!")
        else:
            if "log" in ctx: ctx["log"].append("Chain ends (no nearby target)")

    def _handle_temp_ac_advantage(self, match, ctx):
        ctx["defense_advantage"] = True 
        if "log" in ctx: ctx["log"].append("Defensive Advantage!")

    def _handle_line_attack(self, match, ctx):
        """Line attack - hit all enemies in a line from caster"""
        engine = ctx.get("engine")
        attacker = ctx.get("attacker")
        target = ctx.get("target")
        if not engine or not attacker: return
        
        # Get direction from attacker to target
        if target:
            dx = 1 if target.x > attacker.x else (-1 if target.x < attacker.x else 0)
            dy = 1 if target.y > attacker.y else (-1 if target.y < attacker.y else 0)
        else:
            dx, dy = 0, 1  # Default forward
        
        # Check all cells in line up to 6 squares (30ft)
        line_targets = []
        for i in range(1, 7):
            check_x = attacker.x + dx * i
            check_y = attacker.y + dy * i
            for c in engine.combatants:
                if c.x == check_x and c.y == check_y and c.is_alive() and c != attacker:
                    line_targets.append(c)
        
        ctx["aoe_targets"] = line_targets
        if "log" in ctx: ctx["log"].append(f"Line attack hits {len(line_targets)} targets!")

    def _handle_redirect(self, match, ctx):
        """Redirect attack to adjacent ally"""
        engine = ctx.get("engine")
        target = ctx.get("target")  # Original target
        if not engine or not target: return
        
        # Find adjacent ally to redirect to
        for c in engine.combatants:
            if c == target or not c.is_alive(): continue
            dx = abs(c.x - target.x)
            dy = abs(c.y - target.y)
            if max(dx, dy) <= 1:
                ctx["target"] = c  # Redirect!
                if "log" in ctx: ctx["log"].append(f"Attack redirected to {c.name}!")
                return
        
        if "log" in ctx: ctx["log"].append("No adjacent target to redirect to")

    def _handle_aoe_attack(self, match, ctx):
        """Attack every enemy instantly"""
        engine = ctx.get("engine")
        attacker = ctx.get("attacker")
        if not engine or not attacker: return
        
        base_dmg = ctx.get("incoming_damage", 3)
        hit_count = 0
        
        for c in engine.combatants:
            if c == attacker or not c.is_alive(): continue
            c.hp -= base_dmg
            hit_count += 1
        
        if "log" in ctx: ctx["log"].append(f"AOE Attack! Hit {hit_count} enemies for {base_dmg} each!")

    def _handle_charge(self, match, ctx):
        """Line charge - move in straight line and attack first enemy hit"""
        engine = ctx.get("engine")
        attacker = ctx.get("attacker")
        target = ctx.get("target")
        if not engine or not attacker: return
        
        # Direction to target
        if target:
            dx = 1 if target.x > attacker.x else (-1 if target.x < attacker.x else 0)
            dy = 1 if target.y > attacker.y else (-1 if target.y < attacker.y else 0)
        else:
            dx, dy = 0, 1
        
        # Move up to 6 squares, stop when hitting enemy
        charge_dist = 0
        for i in range(1, 7):
            new_x = attacker.x + dx * i
            new_y = attacker.y + dy * i
            
            # Check for collision
            hit_enemy = None
            for c in engine.combatants:
                if c.x == new_x and c.y == new_y and c.is_alive() and c != attacker:
                    hit_enemy = c
                    break
            
            if hit_enemy:
                # Stop here or one square before
                attacker.x = new_x - dx
                attacker.y = new_y - dy
                charge_dist = i - 1
                charge_dmg = 5 + charge_dist  # Bonus damage from momentum
                hit_enemy.hp -= charge_dmg
                if "log" in ctx: ctx["log"].append(f"Charge! Moved {charge_dist*5}ft, hit {hit_enemy.name} for {charge_dmg}!")
                return
            else:
                charge_dist = i
        
        # No enemy hit, just move
        attacker.x = attacker.x + dx * charge_dist
        attacker.y = attacker.y + dy * charge_dist
        if "log" in ctx: ctx["log"].append(f"Charge! Moved {charge_dist*5}ft (no enemy hit)")

    def _handle_multihit(self, match, ctx):
        """Multi-hit attack - roll attack multiple times with reduced damage"""
        engine = ctx.get("engine")
        attacker = ctx.get("attacker")
        target = ctx.get("target")
        if not engine or not attacker or not target: return
        
        num_hits = 3  # Default 3 hits
        dmg_per_hit = 2  # Low damage per hit
        total_dmg = 0
        
        for i in range(num_hits):
            # Each hit has chance to miss
            hit_roll = random.randint(1, 20) + attacker.get_stat("Might")
            def_val = 10 + target.get_stat("Reflexes")
            if hit_roll >= def_val:
                target.hp -= dmg_per_hit
                total_dmg += dmg_per_hit
        
        if "log" in ctx: ctx["log"].append(f"Multi-hit! {num_hits} attacks, {total_dmg} total damage!")

    def _handle_aging(self, match, ctx):
        """Rapid aging - massive CMP damage and stat reduction"""
        target = ctx.get("target")
        if not target: return
        
        cmp_dmg = 10
        target.cmp = max(0, getattr(target, 'cmp', 10) - cmp_dmg)
        
        # Reduce 2 random stats by 2
        stat_names = ["Might", "Reflexes", "Endurance", "Vitality", "Willpower", "Charm"]
        import random
        reduced = random.sample(stat_names, 2)
        for stat in reduced:
            if stat in target.stats:
                target.stats[stat] = max(0, target.stats[stat] - 2)
        
        if "log" in ctx: ctx["log"].append(f"{target.name} Aged! -{cmp_dmg} CMP, -{2} to {reduced[0]} and {reduced[1]}")

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
        base = int(match.group(1))
        if "log" in ctx: ctx["log"].append(f"Natural Armor Base {base}")
    
    # --- SAVE EFFECT HANDLERS ---
    
    def _handle_save_condition(self, match, ctx):
        """Handle 'save or (Condition)' - only apply if save failed"""
        if ctx.get("save_success"): return # Saved, no effect
        
        condition = match.group(1).lower()
        target = ctx.get("target")
        if not target: return
        
        # Check for duration in the original effect description
        # e.g. "Frightened for 1 round" or "Poisoned for 1 minute"
        duration = 1 # Default 1 round
        effect_desc = ctx.get("effect_desc", "")
        
        import re
        dur_match = re.search(r"for (\d+) (round|minute|turn|hour)", effect_desc, re.IGNORECASE)
        if dur_match:
            num = int(dur_match.group(1))
            unit = dur_match.group(2).lower()
            if unit == "minute":
                duration = num * 10 # 10 rounds per minute
            elif unit == "hour":
                duration = num * 600
            else:
                duration = num
        
        # Use apply_effect if available
        if hasattr(target, "apply_effect"):
            target.apply_effect(condition.capitalize(), duration)
            if "log" in ctx: ctx["log"].append(f"{target.name} is {condition.capitalize()} for {duration} rounds!")
        else:
            # Fallback to direct flag
            condition_map = {
                "prone": "is_prone", "frightened": "is_frightened",
                "charmed": "is_charmed", "blinded": "is_blinded",
                "paralyzed": "is_paralyzed", "poisoned": "is_poisoned",
                "stunned": "is_stunned", "restrained": "is_restrained",
                "deafened": "is_deafened"
            }
            attr = condition_map.get(condition)
            if attr and hasattr(target, attr):
                setattr(target, attr, True)
                if "log" in ctx: ctx["log"].append(f"{target.name} is {condition.capitalize()}!")

    def _handle_save_push(self, match, ctx):
        """Handle 'save or pushed Xft'"""
        if ctx.get("save_success"): return
        
        dist_ft = int(match.group(1))
        # Reuse existing push handler logic
        target = ctx.get("target")
        attacker = ctx.get("attacker")
        if target and attacker:
            squares = dist_ft // 5
            dx = target.x - attacker.x
            dy = target.y - attacker.y
            if dx == 0 and dy == 0: return
            dir_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
            dir_y = 1 if dy > 0 else (-1 if dy < 0 else 0)
            target.x += dir_x * squares
            target.y += dir_y * squares
            if "log" in ctx: ctx["log"].append(f"Pushed {dist_ft}ft!")

    def _handle_save_half_damage(self, match, ctx):
        """Handle 'save or half damage' - if saved, halve incoming"""
        if ctx.get("save_success") and "incoming_damage" in ctx:
            ctx["incoming_damage"] //= 2
            if "log" in ctx: ctx["log"].append("Saved! Damage Halved.")

    def _handle_save_damage(self, match, ctx):
        """Handle 'save or Xd? damage' - if failed, apply damage"""
        if ctx.get("save_success"): return
        
        amt_str = match.group(1) or "1"
        die_str = match.group(2)
        target = ctx.get("target")
        if not target: return
        
        dmg = 0
        if die_str:
            num = int(amt_str)
            sides = int(die_str)
            dmg = sum(random.randint(1, sides) for _ in range(num))
        else:
            dmg = int(amt_str) if amt_str else 0
        
        target.hp -= dmg
        if "log" in ctx: ctx["log"].append(f"Save Failed! {dmg} damage!")
    
    # --- AOE HANDLERS ---
    
    def _handle_aoe_shape(self, match, ctx):
        """Handle 'Xft cone/line/radius/sphere' - find all targets in range"""
        size = int(match.group(1))
        shape = match.group(2).lower()
        ctx["aoe_size"] = size
        ctx["aoe_shape"] = shape
        
        # Get all combatants in range from engine
        engine = ctx.get("engine")
        caster = ctx.get("attacker")
        if not engine or not caster: return
        
        squares = size // 5
        targets_hit = []
        
        for c in engine.combatants:
            if c == caster or not c.is_alive(): continue
            dx = abs(c.x - caster.x)
            dy = abs(c.y - caster.y)
            dist = max(dx, dy)
            
            if shape in ["radius", "sphere"]:
                if dist <= squares:
                    targets_hit.append(c)
            elif shape == "cone":
                # Simple cone: within range and in front (y > caster.y for example)
                if dist <= squares:
                    targets_hit.append(c)
            elif shape == "line":
                # Simple line: same row or column
                if (dx == 0 or dy == 0) and dist <= squares:
                    targets_hit.append(c)
        
        ctx["aoe_targets"] = targets_hit
        if "log" in ctx: ctx["log"].append(f"AOE {size}ft {shape}: Hit {len(targets_hit)} targets")

    def _handle_aoe_targets(self, match, ctx):
        """Handle 'all enemies/creatures/allies within Xft' - apply effect to each"""
        target_type = match.group(1).lower()
        dist = int(match.group(3))
        
        engine = ctx.get("engine")
        caster = ctx.get("attacker")
        if not engine or not caster: return
        
        squares = dist // 5
        targets = []
        
        for c in engine.combatants:
            if not c.is_alive(): continue
            dx = abs(c.x - caster.x)
            dy = abs(c.y - caster.y)
            if max(dx, dy) > squares: continue
            
            # Filter by type
            if target_type == "enemies" and c != caster:
                targets.append(c)
            elif target_type == "allies" and c != caster:
                # Would need faction system, for now assume all non-caster
                targets.append(c)
            elif target_type == "creatures":
                targets.append(c)
        
        ctx["aoe_targets"] = targets
        if "log" in ctx: ctx["log"].append(f"Targets: {len(targets)} {target_type} within {dist}ft")

    def _handle_summon(self, match, ctx):
        """Handle 'summon/call/conjure' - spawn a new combatant"""
        engine = ctx.get("engine")
        caster = ctx.get("attacker")
        if not engine or not caster: return
        
        # Create a basic summon near caster
        # In a full system, this would lookup summon data
        summon_data = {
            "Name": "Summoned Creature",
            "Stats": {"Might": 5, "Reflexes": 5, "Endurance": 5},
            "Derived": {"HP": 10, "Speed": 30}
        }
        
        # Find empty spot adjacent to caster
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0: continue
                tx, ty = caster.x + dx, caster.y + dy
                occupied = any(c.x == tx and c.y == ty and c.is_alive() for c in engine.combatants)
                if not occupied:
                    # Import dynamically to avoid circular import
                    import importlib.util
                    import sys
                    import os
                    mech_path = os.path.join(os.path.dirname(__file__), "../combat simulator/mechanics.py")
                    spec = importlib.util.spec_from_file_location("mechanics", mech_path)
                    mechanics = importlib.util.module_from_spec(spec)
                    if "mechanics" not in sys.modules:
                        spec.loader.exec_module(mechanics)
                    else:
                        mechanics = sys.modules["mechanics"]
                    
                    summon = mechanics.Combatant("dummy.json")
                    summon.name = summon_data["Name"]
                    summon.stats = summon_data["Stats"]
                    summon.derived = summon_data["Derived"]
                    summon.hp = summon.derived.get("HP", 10)
                    summon.max_hp = summon.hp
                    engine.add_combatant(summon, tx, ty)
                    if "log" in ctx: ctx["log"].append(f"Summoned {summon.name} at ({tx},{ty})!")
                    return
        
        if "log" in ctx: ctx["log"].append("Summon failed: No space!")

    def _handle_create_terrain(self, match, ctx):
        """Handle 'create wall/barrier/cover' - mark grid cells"""
        terrain_type = match.group(1).lower()
        engine = ctx.get("engine")
        caster = ctx.get("attacker")
        if not engine or not caster: return
        
        # Create terrain in front of caster
        tx, ty = caster.x, caster.y + 1
        
        # Store terrain in engine (add terrain list if not exists)
        if not hasattr(engine, "terrain"):
            engine.terrain = []
        
        engine.terrain.append({
            "type": terrain_type,
            "x": tx,
            "y": ty,
            "blocks_movement": terrain_type == "wall",
            "provides_cover": terrain_type in ["barrier", "cover"]
        })
        
        if "log" in ctx: ctx["log"].append(f"Created {terrain_type} at ({tx},{ty})!")

    def _handle_die_hit_bonus(self, match, ctx):
        """Handle '+1d4 to Hit' etc."""
        num = int(match.group(1))
        sides = int(match.group(2))
        bonus = sum(random.randint(1, sides) for _ in range(num))
        if "attack_roll" in ctx:
            ctx["attack_roll"] += bonus
        if "log" in ctx: ctx["log"].append(f"+{num}d{sides} to Hit ({bonus})")

    def _handle_die_hit_penalty(self, match, ctx):
        """Handle '-1d4 to Hit' etc."""
        num = int(match.group(1))
        sides = int(match.group(2))
        malus = sum(random.randint(1, sides) for _ in range(num))
        if "attack_roll" in ctx:
            ctx["attack_roll"] -= malus
        if "log" in ctx: ctx["log"].append(f"-{num}d{sides} to Hit ({malus})")

    def _handle_damage_reduction(self, match, ctx):
        """Handle 'Damage Reduction X'"""
        dr = int(match.group(1))
        if "incoming_damage" in ctx:
            ctx["incoming_damage"] = max(0, ctx["incoming_damage"] - dr)
        if "log" in ctx: ctx["log"].append(f"Damage Reduced by {dr}")
        
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

    # ============================================
    # SCHOOL OF FLUX HANDLERS
    # ============================================
    
    def _handle_ethereal(self, match, ctx):
        """Become Ethereal - immune to physical damage"""
        user = ctx.get("attacker") or ctx.get("target")
        if user:
            user.is_ethereal = True if hasattr(user, 'is_ethereal') else None
            duration = ctx.get("effect_duration", 1)
            if hasattr(user, "apply_effect"):
                user.apply_effect("Ethereal", duration)
            if "log" in ctx: ctx["log"].append(f"{user.name} becomes Ethereal! (Immune to Physical)")
    
    def _handle_phase(self, match, ctx):
        """Phase through matter temporarily"""
        user = ctx.get("attacker")
        target = ctx.get("target")
        
        # If targeting ally, apply to them
        apply_to = target if target else user
        if apply_to:
            apply_to.is_phasing = True if hasattr(apply_to, 'is_phasing') else None
            if hasattr(apply_to, "apply_effect"):
                apply_to.apply_effect("Phasing", 1)
            if "log" in ctx: ctx["log"].append(f"{apply_to.name} is Phasing!")
    
    def _handle_phase_walk(self, match, ctx):
        """Walk through solid walls"""
        user = ctx.get("attacker")
        if user:
            # Allow movement through obstacles for 1 turn
            user.can_phase_walk = True
            if "log" in ctx: ctx["log"].append(f"{user.name} can walk through walls!")
    
    def _handle_amorphous(self, match, ctx):
        """Amorphous form - immune to crits and grapple"""
        user = ctx.get("attacker") or ctx.get("target")
        if user:
            user.is_amorphous = True if hasattr(user, 'is_amorphous') else None
            # Also grants crit immunity
            if "is_crit" in ctx:
                ctx["is_crit"] = False
            # Cannot be grappled
            user.is_grapple_immune = True
            if "log" in ctx: ctx["log"].append(f"{user.name} becomes Amorphous! (Immune to Crits & Grapple)")
    
    def _handle_displacement(self, match, ctx):
        """Displacement - appear 5ft from actual position, attacks have disadvantage"""
        user = ctx.get("attacker") or ctx.get("target")
        if user:
            user.has_displacement = True
            # Enemies have disadvantage when attacking
            if "log" in ctx: ctx["log"].append(f"{user.name} is displaced! (Attackers have Disadvantage)")
    
    def _handle_disintegrate(self, match, ctx):
        """Disintegrate - massive damage, kills outright if HP drops to 0"""
        target = ctx.get("target")
        attacker = ctx.get("attacker")
        if target and attacker:
            # Massive damage: 10d6 force
            dmg = sum(random.randint(1, 6) for _ in range(10))
            target.hp -= dmg
            
            # If this kills them, they turn to dust (can't be revived normally)
            if target.hp <= 0:
                target.is_disintegrated = True
                if "log" in ctx: ctx["log"].append(f"{target.name} DISINTEGRATED! ({dmg} force damage) - reduced to dust!")
            else:
                if "log" in ctx: ctx["log"].append(f"Disintegrate deals {dmg} force damage to {target.name}!")
    
    def _handle_dot(self, match, ctx):
        """Damage over Time / Bleed effect"""
        target = ctx.get("target")
        if target:
            # Apply bleeding effect - 1d4 damage per turn for 3 turns
            if hasattr(target, "apply_effect"):
                target.apply_effect("Bleeding", duration=3, on_expire="is_bleeding")
            target.is_bleeding = True
            target.bleed_damage = random.randint(1, 4)  # Store DoT amount
            if "log" in ctx: ctx["log"].append(f"{target.name} is Bleeding! ({target.bleed_damage}/turn for 3 rounds)")
    
    def _handle_sever_limb(self, match, ctx):
        """Cut off a limb - permanent debuff"""
        target = ctx.get("target")
        if target:
            limbs = ["arm", "leg", "tail", "wing"]
            severed = random.choice(limbs)
            
            # Apply permanent penalty
            if severed == "arm":
                if "Might" in target.stats:
                    target.stats["Might"] = max(0, target.stats["Might"] - 4)
            elif severed == "leg":
                if hasattr(target, "movement"):
                    target.movement = max(5, target.movement - 10)
            
            target.hp -= 5  # Trauma damage
            if "log" in ctx: ctx["log"].append(f"{target.name}'s {severed} severed! Permanent debuff applied.")
    
    def _handle_compress_space(self, match, ctx):
        """Compress space to a point - pulls all nearby enemies toward caster"""
        engine = ctx.get("engine")
        caster = ctx.get("attacker")
        if not engine or not caster: return
        
        pull_range = 4  # 20ft
        pulled = 0
        
        for c in engine.combatants:
            if c == caster or not c.is_alive(): continue
            dx = abs(c.x - caster.x)
            dy = abs(c.y - caster.y)
            dist = max(dx, dy)
            
            if dist <= pull_range and dist > 1:
                # Pull 2 squares toward caster
                dir_x = -1 if c.x > caster.x else (1 if c.x < caster.x else 0)
                dir_y = -1 if c.y > caster.y else (1 if c.y < caster.y else 0)
                c.x += dir_x * 2
                c.y += dir_y * 2
                pulled += 1
        
        if "log" in ctx: ctx["log"].append(f"Space compressed! {pulled} enemies pulled toward {caster.name}!")
    
    def _handle_escape_grapple(self, match, ctx):
        """Escape grapple/bindings/restraints automatically"""
        user = ctx.get("attacker") or ctx.get("target")
        if user:
            user.is_grappled = False
            user.is_restrained = False
            if "log" in ctx: ctx["log"].append(f"{user.name} escapes restraints!")
    
    def _handle_find_path(self, match, ctx):
        """Magically find path to any location"""
        if "log" in ctx: ctx["log"].append("Path revealed! (Pathfinding active)")
    
    def _handle_disarm(self, match, ctx):
        """Force target to drop held item"""
        target = ctx.get("target")
        if target:
            # Remove first weapon from inventory
            if hasattr(target, "inventory") and target.inventory:
                dropped = target.inventory.pop(0) if target.inventory else "nothing"
                if "log" in ctx: ctx["log"].append(f"{target.name} drops {dropped}!")
            else:
                if "log" in ctx: ctx["log"].append(f"{target.name} disarmed!")
    
    def _handle_snatch_projectile(self, match, ctx):
        """Catch a thrown weapon/projectile"""
        if "incoming_damage" in ctx:
            ctx["incoming_damage"] = 0
        if "log" in ctx: ctx["log"].append("Projectile snatched from air! No damage.")
    
    def _handle_steal_item(self, match, ctx):
        """Steal equipped item from target"""
        target = ctx.get("target")
        attacker = ctx.get("attacker")
        if target and attacker:
            if hasattr(target, "inventory") and target.inventory:
                stolen = target.inventory.pop(0)
                if hasattr(attacker, "inventory"):
                    attacker.inventory.append(stolen)
                if "log" in ctx: ctx["log"].append(f"{attacker.name} steals {stolen} from {target.name}!")
            else:
                if "log" in ctx: ctx["log"].append(f"{target.name} has nothing to steal!")
    
    def _handle_switch_items(self, match, ctx):
        """Swap held items with target"""
        target = ctx.get("target")
        attacker = ctx.get("attacker")
        if target and attacker and hasattr(target, "inventory") and hasattr(attacker, "inventory"):
            # Swap first items
            if target.inventory and attacker.inventory:
                target.inventory[0], attacker.inventory[0] = attacker.inventory[0], target.inventory[0]
                if "log" in ctx: ctx["log"].append(f"Items swapped between {attacker.name} and {target.name}!")
    
    def _handle_ignore_armor(self, match, ctx):
        """Ignore target's armor (attack bypasses AC)"""
        ctx["ignore_armor"] = True
        ctx["auto_hit"] = True  # Effectively auto-hits since armor is ignored
        if "log" in ctx: ctx["log"].append("Attack ignores armor!")
    
    def _handle_precision_knockdown(self, match, ctx):
        """Precision strike to knock target prone"""
        target = ctx.get("target")
        if target:
            target.is_prone = True
            if "log" in ctx: ctx["log"].append(f"Precision hit! {target.name} knocked Prone!")
    
    def _handle_reduce_melee_damage(self, match, ctx):
        """Reduce incoming melee damage"""
        if "incoming_damage" in ctx:
            reduction = ctx["incoming_damage"] // 2
            ctx["incoming_damage"] = ctx["incoming_damage"] - reduction
            if "log" in ctx: ctx["log"].append(f"Melee damage reduced by {reduction}!")
    
    def _handle_open_mechanism(self, match, ctx):
        """Open simple mechanism/lock"""
        if "log" in ctx: ctx["log"].append("Mechanism unlocked!")
    
    def _handle_purify_liquid(self, match, ctx):
        """Clean poison/toxin from liquid"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.is_poisoned = False
            if hasattr(target, "active_effects"):
                target.active_effects = [e for e in target.active_effects if "poison" not in e.get("name", "").lower()]
            if "log" in ctx: ctx["log"].append(f"Poison purified from {target.name}!")
    
    def _handle_unmix_potion(self, match, ctx):
        """Separate compound/potion into components"""
        if "log" in ctx: ctx["log"].append("Compound separated into base components!")

    # ============================================
    # ON_ATTACK REACTIVE HANDLERS
    # ============================================
    
    def _handle_attack_adjacent(self, match, ctx):
        """Attack two adjacent enemies with one roll"""
        engine = ctx.get("engine")
        attacker = ctx.get("attacker")
        primary = ctx.get("target")
        if not engine or not attacker or not primary: return
        
        # Find another enemy adjacent to primary
        for c in engine.combatants:
            if c == attacker or c == primary or not c.is_alive(): continue
            dx = abs(c.x - primary.x)
            dy = abs(c.y - primary.y)
            if max(dx, dy) <= 1:
                # Hit this one too with same damage
                dmg = ctx.get("incoming_damage", 5)
                c.hp -= dmg
                if "log" in ctx: ctx["log"].append(f"Cleave! {c.name} takes {dmg} damage!")
                return
    
    def _handle_flanking_attack(self, match, ctx):
        """Bonus attack against flanking enemy"""
        engine = ctx.get("engine")
        attacker = ctx.get("attacker")
        if not engine or not attacker: return
        
        # Find enemy adjacent and "behind" attacker
        for c in engine.combatants:
            if c == attacker or not c.is_alive(): continue
            # Check if flanking (opposite side of another ally)
            dx = c.x - attacker.x
            dy = c.y - attacker.y
            if max(abs(dx), abs(dy)) <= 1:
                # Quick sting attack
                sting_dmg = 3
                c.hp -= sting_dmg
                if "log" in ctx: ctx["log"].append(f"Flanking sting! {c.name} takes {sting_dmg}!")
                return

    def _handle_opportunity_attack(self, match, ctx):
        """Opportunity attack when enemy enters range"""
        range_ft = int(match.group(1)) if match.group(1) else 5
        ctx["opportunity_range"] = range_ft
        if "log" in ctx: ctx["log"].append(f"Ready: Opportunity attack within {range_ft}ft")

    def _handle_rally_allies(self, match, ctx):
        """Give allies bonus to attack rolls"""
        bonus = int(match.group(1)) if match.group(1) else 1
        engine = ctx.get("engine")
        attacker = ctx.get("attacker")
        if not engine or not attacker: return
        
        # Apply buff to all allies within 30ft (6 squares)
        for c in engine.combatants:
            if c == attacker or not c.is_alive(): continue
            dx = abs(c.x - attacker.x)
            dy = abs(c.y - attacker.y)
            if max(dx, dy) <= 6:
                if hasattr(c, "apply_effect"):
                    c.apply_effect("RallyBonus", duration=1)
                if "log" in ctx: ctx["log"].append(f"{c.name} gains +{bonus} to Attack!")

    def _handle_mobile_shooter(self, match, ctx):
        """No penalty to ranged attacks while moving"""
        ctx["mobile_shooter"] = True
        if "log" in ctx: ctx["log"].append("Mobile Shooter: No movement penalty to ranged")

    def _handle_piercing_crit(self, match, ctx):
        """Crit range 19-20 on piercing attacks"""
        ctx["crit_threshold"] = 19
        if "log" in ctx: ctx["log"].append("Piercing Crit: 19-20!")

    def _handle_tail_attack(self, match, ctx):
        """Reflex attack against enemy behind"""
        engine = ctx.get("engine")
        attacker = ctx.get("attacker")
        if not engine or not attacker: return
        
        # Check for enemy directly behind (y - 1)
        for c in engine.combatants:
            if c == attacker or not c.is_alive(): continue
            if c.x == attacker.x and c.y == attacker.y - 1:
                tail_dmg = 4
                c.hp -= tail_dmg
                if "log" in ctx: ctx["log"].append(f"Tail swipe! {c.name} takes {tail_dmg}!")
                return

    def _handle_shield_ally(self, match, ctx):
        """Shield adjacent ally from overhead attacks"""
        if "log" in ctx: ctx["log"].append("Shielding adjacent ally from overhead attacks")

    def _handle_water_stability(self, match, ctx):
        """Remain stable against water attacks"""
        ctx["water_immune_push"] = True
        if "log" in ctx: ctx["log"].append("Water Stability: Cannot be pushed by water")

    def _handle_speed_damage(self, match, ctx):
        """Damage scales with Speed stat"""
        attacker = ctx.get("attacker")
        if attacker:
            speed = attacker.derived.get("Speed", 30) // 5
            if "incoming_damage" in ctx:
                ctx["incoming_damage"] += speed
            if "log" in ctx: ctx["log"].append(f"Speed Bonus: +{speed} damage!")

    def _handle_quick_attack(self, match, ctx):
        """Quick low-damage attack"""
        target = ctx.get("target")
        if target:
            dmg = 2
            target.hp -= dmg
            if "log" in ctx: ctx["log"].append(f"Quick strike! {dmg} damage!")

    def _handle_self_hit(self, match, ctx):
        """Enemy damages self instead"""
        attacker = ctx.get("attacker")  # The enemy attacking
        dmg = ctx.get("incoming_damage", 5)
        if attacker:
            attacker.hp -= dmg
            ctx["incoming_damage"] = 0  # Cancel original damage
            if "log" in ctx: ctx["log"].append(f"Reflected! {attacker.name} hits self for {dmg}!")

    def _handle_miss_ally(self, match, ctx):
        """Miss redirects to ally"""
        engine = ctx.get("engine")
        target = ctx.get("target")
        if not engine or not target: return
        
        # Find adjacent ally
        for c in engine.combatants:
            if c == target or not c.is_alive(): continue
            dx = abs(c.x - target.x)
            dy = abs(c.y - target.y)
            if max(dx, dy) <= 1:
                dmg = ctx.get("incoming_damage", 3)
                c.hp -= dmg
                if "log" in ctx: ctx["log"].append(f"Miss hits {c.name} instead for {dmg}!")
                return

    def _handle_auto_damage(self, match, ctx):
        """Automatic damage (no roll needed)"""
        target = ctx.get("target")
        if target:
            dmg = 5  # Fixed damage
            target.hp -= dmg
            ctx["auto_hit"] = True
            if "log" in ctx: ctx["log"].append(f"Auto-damage: {dmg}!")

    def _handle_weak_point(self, match, ctx):
        """Hit weak point for automatic crit"""
        ctx["is_crit"] = True
        if "incoming_damage" in ctx:
            ctx["incoming_damage"] *= 2
        if "log" in ctx: ctx["log"].append("Weak Point! Critical hit!")

    def _handle_true_strike(self, match, ctx):
        """Bonus to hit on next attack"""
        if "attack_roll" in ctx:
            ctx["attack_roll"] += 5
        if "log" in ctx: ctx["log"].append("True Strike: +5 to hit!")

    def _handle_unhealable_wound(self, match, ctx):
        """Wound cannot be healed by non-magical means"""
        target = ctx.get("target")
        if target:
            if hasattr(target, "apply_effect"):
                target.apply_effect("Unhealable", duration=600)  # 1 hour
            if "log" in ctx: ctx["log"].append(f"{target.name} has an unhealable wound!")

    def _handle_headbutt(self, match, ctx):
        """Headbutt pushes target back 5ft"""
        target = ctx.get("target")
        attacker = ctx.get("attacker")
        if target and attacker:
            dmg = 3
            target.hp -= dmg
            # Push 5ft (1 square)
            dx = target.x - attacker.x
            dy = target.y - attacker.y
            if dx != 0: dx = 1 if dx > 0 else -1
            if dy != 0: dy = 1 if dy > 0 else -1
            target.x += dx
            target.y += dy
            if "log" in ctx: ctx["log"].append(f"Headbutt! {target.name} takes {dmg} and pushed!")

    # ============================================
    # SCHOOL OF OMEN HANDLERS (Luck/Fate Magic)
    # ============================================
    
    def _handle_jinx(self, match, ctx):
        """Apply -1d4 to target's next roll"""
        target = ctx.get("target")
        if target:
            malus = random.randint(1, 4)
            if "attack_roll" in ctx:
                ctx["attack_roll"] -= malus
            if hasattr(target, "apply_effect"):
                target.apply_effect("Jinxed", duration=1)
            if "log" in ctx: ctx["log"].append(f"Jinxed! -{malus} to next roll!")

    def _handle_bless(self, match, ctx):
        """Apply +1d4 to ally's next roll"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            bonus = random.randint(1, 4)
            if "attack_roll" in ctx:
                ctx["attack_roll"] += bonus
            if hasattr(target, "apply_effect"):
                target.apply_effect("Blessed", duration=1)
            if "log" in ctx: ctx["log"].append(f"Blessed! +{bonus} to next roll!")

    def _handle_curse(self, match, ctx):
        """Apply Disadvantage on all rolls"""
        target = ctx.get("target")
        if target:
            ctx["disadvantage"] = True
            if hasattr(target, "apply_effect"):
                target.apply_effect("Cursed", duration=3)
            if "log" in ctx: ctx["log"].append(f"{target.name} is Cursed! Disadvantage on rolls!")

    def _handle_fate(self, match, ctx):
        """Apply Advantage on all rolls"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            ctx["advantage"] = True
            if hasattr(target, "apply_effect"):
                target.apply_effect("Fated", duration=3)
            if "log" in ctx: ctx["log"].append(f"{target.name} is Fated! Advantage on rolls!")

    def _handle_lucky(self, match, ctx):
        """Reroll any 1s"""
        ctx["reroll_ones"] = True
        if "log" in ctx: ctx["log"].append("Lucky! Reroll 1s!")

    def _handle_force_reroll(self, match, ctx):
        """Force enemy to reroll, take lower"""
        target = ctx.get("target")
        if target:
            ctx["force_reroll_low"] = True
            if "log" in ctx: ctx["log"].append(f"{target.name} must reroll and take lower!")

    def _handle_luck_trip(self, match, ctx):
        """Bad luck causes target to trip"""
        target = ctx.get("target")
        if target:
            target.is_prone = True
            if "log" in ctx: ctx["log"].append(f"Bad luck! {target.name} trips and falls Prone!")

    def _handle_weapon_jam(self, match, ctx):
        """Cause weapon to jam/fail"""
        target = ctx.get("target")
        if target:
            if hasattr(target, "apply_effect"):
                target.apply_effect("WeaponJammed", duration=1)
            if "log" in ctx: ctx["log"].append(f"{target.name}'s weapon jams!")

    def _handle_fumble(self, match, ctx):
        """Cause target to drop held item"""
        target = ctx.get("target")
        if target and hasattr(target, "inventory") and target.inventory:
            dropped = target.inventory.pop(0)
            if "log" in ctx: ctx["log"].append(f"{target.name} fumbles and drops {dropped}!")
        elif "log" in ctx:
            ctx["log"].append("Fumble! (No item to drop)")

    def _handle_backfire(self, match, ctx):
        """Enemy hits self instead of target"""
        attacker = ctx.get("attacker")
        dmg = ctx.get("incoming_damage", 5)
        if attacker:
            attacker.hp -= dmg
            ctx["incoming_damage"] = 0
            if "log" in ctx: ctx["log"].append(f"Backfire! {attacker.name} hits self for {dmg}!")

    def _handle_ricochet(self, match, ctx):
        """Miss ricochets to hit ally"""
        # Same as miss_ally but thematic for Omen
        engine = ctx.get("engine")
        attacker = ctx.get("attacker")
        if not engine or not attacker: return
        
        for c in engine.combatants:
            if c == attacker or not c.is_alive(): continue
            dx = abs(c.x - attacker.x)
            dy = abs(c.y - attacker.y)
            if max(dx, dy) <= 2:
                dmg = ctx.get("incoming_damage", 4)
                c.hp -= dmg
                if "log" in ctx: ctx["log"].append(f"Ricochet! {c.name} hit for {dmg}!")
                return

    def _handle_calamity(self, match, ctx):
        """Force critical failure on target"""
        target = ctx.get("target")
        if target:
            ctx["force_crit_fail"] = True
            if "attack_roll" in ctx:
                ctx["attack_roll"] = 1  # Natural 1
            if "log" in ctx: ctx["log"].append(f"Calamity! {target.name} critically fails!")

    def _handle_miracle(self, match, ctx):
        """Survive lethal damage with 1 HP"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            if hasattr(target, "apply_effect"):
                target.apply_effect("Miracle", duration=1)
            # Set flag that will be checked before death
            ctx["miracle_save"] = True
            if "log" in ctx: ctx["log"].append(f"{target.name} invokes Miracle! Will survive with 1 HP!")

    def _handle_doom(self, match, ctx):
        """Instant kill (powerful effect)"""
        target = ctx.get("target")
        if target:
            target.hp = 0
            if "log" in ctx: ctx["log"].append(f"DOOM! {target.name} is instantly slain!")

    def _handle_divine_save(self, match, ctx):
        """Automatically succeed on save"""
        ctx["save_success"] = True
        ctx["auto_save"] = True
        if "log" in ctx: ctx["log"].append("Divine intervention! Auto-save success!")

    def _handle_auto_nat20(self, match, ctx):
        """Automatically roll Natural 20"""
        ctx["attack_roll"] = 20
        ctx["is_crit"] = True
        ctx["auto_hit"] = True
        if "log" in ctx: ctx["log"].append("Divine Favor! Natural 20!")

    def _handle_karma(self, match, ctx):
        """Reflect damage back to attacker"""
        attacker = ctx.get("attacker")
        dmg = ctx.get("incoming_damage", 5)
        if attacker and dmg > 0:
            attacker.hp -= dmg
            if "log" in ctx: ctx["log"].append(f"Karma! {attacker.name} takes {dmg} reflected damage!")

    def _handle_coin_flip(self, match, ctx):
        """50/50 chance for good or bad outcome"""
        result = random.choice(["Heads", "Tails"])
        ctx["coin_result"] = result
        if "log" in ctx: ctx["log"].append(f"Coin Flip: {result}!")

    def _handle_locate(self, match, ctx):
        """Locate an object"""
        if "log" in ctx: ctx["log"].append("Object located! (Direction known)")

    def _handle_danger_sense(self, match, ctx):
        """Sense incoming danger"""
        attacker = ctx.get("attacker")
        if attacker:
            if hasattr(attacker, "apply_effect"):
                attacker.apply_effect("DangerSense", duration=10)
            ctx["cannot_be_surprised"] = True
            if "log" in ctx: ctx["log"].append("Danger Sense active! Cannot be surprised!")

    def _handle_best_route(self, match, ctx):
        """Find best path/route"""
        if "log" in ctx: ctx["log"].append("Best route revealed!")

    def _handle_gamble(self, match, ctx):
        """Random buff effect"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            buffs = ["Blessed", "Fated", "Lucky", "Hasted", "Strengthened"]
            chosen = random.choice(buffs)
            if hasattr(target, "apply_effect"):
                target.apply_effect(chosen, duration=3)
            if "log" in ctx: ctx["log"].append(f"Gamble! {target.name} gains {chosen}!")

    def _handle_serendipity(self, match, ctx):
        """Find useful loot"""
        attacker = ctx.get("attacker")
        if attacker and hasattr(attacker, "inventory"):
            loot = random.choice(["Healing Potion", "Gold Coins", "Magic Scroll", "Lucky Charm"])
            attacker.inventory.append(loot)
            if "log" in ctx: ctx["log"].append(f"Serendipity! Found {loot}!")

    def _handle_speak_dead(self, match, ctx):
        """Communicate with deceased"""
        if "log" in ctx: ctx["log"].append("Spirit contacted! You may ask 3 questions...")

    def _handle_augury(self, match, ctx):
        """Hint about future outcome"""
        outcomes = ["Weal (Good)", "Woe (Bad)", "Both", "Neither"]
        result = random.choice(outcomes)
        if "log" in ctx: ctx["log"].append(f"Augury reveals: {result}")

    def _handle_destiny(self, match, ctx):
        """Force a specific roll result"""
        # Set next roll to a specific value
        forced = random.randint(10, 20)  # Generally favorable
        ctx["forced_roll"] = forced
        if "attack_roll" in ctx:
            ctx["attack_roll"] = forced
        if "log" in ctx: ctx["log"].append(f"Destiny! Next roll forced to {forced}!")

# Singleton instance for easy access
registry = EffectRegistry()

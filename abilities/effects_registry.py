
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
        self.register_pattern(r"Magic Missile", self._handle_magic_missile)
        
        # Status Effects
        self.register_pattern(r"\(Burn\)", self._handle_apply_burning)
        self.register_pattern(r"Apply Burning", self._handle_apply_burning)
        self.register_pattern(r"Freeze", self._handle_apply_frozen)
        self.register_pattern(r"Apply Frozen", self._handle_apply_frozen)
        self.register_pattern(r"Stagger", self._handle_apply_staggered)
        self.register_pattern(r"Apply Staggered", self._handle_apply_staggered)
        self.register_pattern(r"Apply Bleeding", self._handle_apply_bleeding)
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
        self.register_pattern(r"(?<!Cure )Poison", self._handle_poison)
        self.register_pattern(r"Fear|Frightened", self._handle_fear)
        self.register_pattern(r"Charm", self._handle_charm)
        self.register_pattern(r"Deafen", self._handle_deafen)
        
        # --- HEALING & RESOURCES ---
        self.register_pattern(r"Heal (?!HP every|minor)(\d+)?d?(\d+)? ?(HP)?", self._handle_heal)
        self.register_pattern(r"Regain (\d+)?d?(\d+)? ?(HP)?", self._handle_heal)
        self.register_pattern(r"(?<!Stasis )Temp(?:orary)? HP", self._handle_temp_hp)
        
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
        self.register_pattern(r"(?<!Explosion of )(?<!Massive )(?<!Holy )Light", self._handle_light)

        # --- COSTS ---
        self.register_pattern(r"Cost:? (\d+) (SP|FP|CMP|HP)", self._handle_cost)

        # --- TALENTS (Custom Logic) ---
        self.register_pattern(r"damage_bonus_vs_armor\((\d+)\)", self._handle_damage_vs_armor)
        self.register_pattern(r"knockback", self._handle_knockback_talent)
        self.register_pattern(r"projectile_pierce\((\d+)\)", self._handle_pierce_talent)
        self.register_pattern(r"sunder", self._handle_sunder_talent)


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
        self.register_pattern(r"Damage over Time|(?<!Massive )(?<!Rapid )DoT|(?<!Stop )Bleed", self._handle_dot)
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
        self.register_pattern(r"Vines.*?restrict|Entangle", self._handle_vines)

        # ============================================
        # SCHOOL OF LUX EFFECTS (Light/Vision Magic)
        # ============================================
        
        # --- LUX: DAMAGE & OFFENSE ---
        self.register_pattern(r"Laser.*?Damage|(?<!Solar )Beam", self._handle_laser)
        self.register_pattern(r"Massive Light Damage|Nova", self._handle_nova)
        self.register_pattern(r"Split Beam|Multi-hit", self._handle_split_beam)
        self.register_pattern(r"Burn Undead|Holy Damage", self._handle_burn_undead)
        self.register_pattern(r"Explosion of Light|Flashbang", self._handle_light_explosion)
        self.register_pattern(r"Heat Metal|Burn(ing)?", self._handle_heat_metal)
        
        # --- LUX: VISION & DETECTION ---
        self.register_pattern(r"See Invisible|Truesight", self._handle_see_invis)
        self.register_pattern(r"See Through Walls|X-Ray", self._handle_xray)
        self.register_pattern(r"See in Darkness|Darkvision", self._handle_darkvision)
        self.register_pattern(r"Know Location|GPS", self._handle_gps)
        self.register_pattern(r"Postcognition|See Past", self._handle_postcognition)
        self.register_pattern(r"Remote Viewing|Scry", self._handle_scry)
        self.register_pattern(r"Bonus Perception|Enhanced Vision", self._handle_bonus_perception)
        
        # --- LUX: DEBUFFS (BLIND/DAZZLE) ---
        self.register_pattern(r"Blind foe|Blindness", self._handle_blindness)
        self.register_pattern(r"Permanent Blindness", self._handle_perm_blind)
        self.register_pattern(r"Dazzle|Visual Noise", self._handle_dazzle)
        self.register_pattern(r"Block Sight Line|Obscure", self._handle_block_sight)
        
        # --- LUX: ILLUSION & STEALTH ---
        self.register_pattern(r"Turn Invisible|Invisibility", self._handle_invisibility)
        self.register_pattern(r"Alter Self|Disguise", self._handle_disguise)
        self.register_pattern(r"Blend with surroundings|Camouflage", self._handle_camo)
        self.register_pattern(r"Hologram|Illusion|Decoy", self._handle_illusion)
        self.register_pattern(r"Major Image|Fake Terrain", self._handle_major_image)
        self.register_pattern(r"Hidden from Reality", self._handle_hidden_reality)

        # ============================================
        # SPECIES SKILLS (REGISTRATIONS)
        # ============================================
        self.register_pattern(r"Gore|Charge attack|moves 20ft.*?damage", self._handle_gore_charge)
        self.register_pattern(r"Lunge|Reach increases|Long Arms", self._handle_lunge_reach)
        self.register_pattern(r"Inject Venom|Poison bite|Envenom", self._handle_venom_injection)
        self.register_pattern(r"Trample|Run over|move through", self._handle_trample)
        self.register_pattern(r"Wall Crawler|Walk on walls|Spider climb", self._handle_wall_walk)
        self.register_pattern(r"Tremorsense|Detect vibration", self._handle_tremorsense)
        self.register_pattern(r"Advantage to maintain a grapple|Grapple Bonus", self._handle_grapple_bonus)
        self.register_pattern(r"Cone Attack|Fire cone|Breath weapon", self._handle_cone_attack)
        self.register_pattern(r"Bleed damage|Bleeding", self._handle_bleed_dot)
        self.register_pattern(r"Ignore.*?Cover", self._handle_ignore_cover)
        self.register_pattern(r"Auto-Grapple|Grapple on hit", self._handle_auto_grapple)

        # --- SPECIES: MOVEMENT ---
        self.register_pattern(r"Swim Speed|Propel|Paddle", self._handle_swim_speed)
        self.register_pattern(r"Fly Speed|Soar|Fragile Speed", self._handle_fly_speed)
        self.register_pattern(r"Burrow Speed|Earth Glide", self._handle_burrow_speed)
        self.register_pattern(r"Climb Speed|Climber", self._handle_climb_speed)
        self.register_pattern(r"Move through.*?space|Squeeze|Compact", self._handle_squeeze)
        
        # --- SPECIES: SENSES ---
        self.register_pattern(r"Bio-Sense|Heartbeat detection", self._handle_biosense)
        self.register_pattern(r"Thermal Sight|Heat detection", self._handle_thermal_sight)
        self.register_pattern(r"Omni-Vision|Peripheral Sight|Cannot be Flanked", self._handle_omnivision)
        self.register_pattern(r"Eavesdrop|Hearing", self._handle_enhanced_hearing)
        
        # --- SPECIES: DEFENSE ---
        self.register_pattern(r"Anchor|Rooted|Dig In|Cannot be moved", self._handle_immovable)
        self.register_pattern(r"Slippery|Slick Escape|Friction", self._handle_slippery)
        self.register_pattern(r"Withdraw|Shell|Turtle", self._handle_withdraw)
        
        # --- SPECIES: OFFENSE ---
        self.register_pattern(r"Web Shot|Sticky Net", self._handle_web_shot)
        self.register_pattern(r"Spore Cloud|Release spores", self._handle_spore_cloud)
        self.register_pattern(r"Tail Sweep|Spin attack", self._handle_tail_sweep)
        self.register_pattern(r"Gust|Wind line", self._handle_gust)
        self.register_pattern(r"Solar Beam|Dazzling beam", self._handle_solar_beam)
        self.register_pattern(r"Lockjaw|Hooked teeth", self._handle_lockjaw)
        
        # --- SPECIES: UTILITY ---
        self.register_pattern(r"Goodberry|Grow fruit", self._handle_goodberry)
        self.register_pattern(r"Mimicry|Imitate voice", self._handle_mimicry)
        self.register_pattern(r"Breathe underwater|Amphibious|Respire", self._handle_water_breathing)

        # ============================================
        # SCHOOL OF ORDO PATTERNS
        # ============================================
        self.register_pattern(r"Stop target movement|Halt", self._handle_halt_movement)
        self.register_pattern(r"Stand up|Stand", self._handle_stand_up)
        self.register_pattern(r"Keep a door.*?shut|Hold", self._handle_hold_door)
        self.register_pattern(r"Create an obstacle|Trip", self._handle_trip)
        self.register_pattern(r"Natural Armor bonus|Skin", self._handle_natural_armor_buff)
        self.register_pattern(r"Ignore hunger|Sustain", self._handle_ignore_needs)
        self.register_pattern(r"Create (wall|barrier|cover|structure|hut|bunker)", self._handle_create_wall)
        self.register_pattern(r"Become immovable|Anchor", self._handle_anchor)
        self.register_pattern(r"Stop decay|Preserve", self._handle_ignore_needs)
        self.register_pattern(r"Turn target to stone|Petrify", self._handle_petrify)
        self.register_pattern(r"Gain Temporary HP|Reinforce", self._handle_temp_hp_buff)
        self.register_pattern(r"Bury target|Entomb", self._handle_create_wall)
        self.register_pattern(r"Take damage meant for an ally|Absorb", self._handle_absorb_damage)
        self.register_pattern(r"Unopenable|Arcane Lock", self._handle_hold_door)
        self.register_pattern(r"Freeze target in time|Stasis", self._handle_stasis)
        self.register_pattern(r"Return damage|Reflect", self._handle_reflect_damage)
        self.register_pattern(r"Feign Death|Statue", self._handle_feign_death)
        self.register_pattern(r"Stop target's heart|Arrest", self._handle_stop_heart)
        self.register_pattern(r"Take 0 Damage|Immunity", self._handle_invulnerability)
        self.register_pattern(r"Run forever|Stamina", self._handle_infinite_stamina)
        self.register_pattern(r"Make target fragile|Crystallize", self._handle_shatter)
        self.register_pattern(r"Invulnerable Structure|Fortress|Monolith", self._handle_fortress)
        self.register_pattern(r"End Time|Stop", self._handle_time_stop)
        self.register_pattern(r"Cannot die|Eternal", self._handle_immortality)
        self.register_pattern(r"Create new land|Foundation", self._handle_create_land)

        # ============================================
        # SCHOOL OF NEXUS PATTERNS
        # ============================================
        self.register_pattern(r"Deal Fire Damage|Heat|Burn", self._handle_fire_damage)
        self.register_pattern(r"Bonus AC|Harden", self._handle_harden_skin)
        self.register_pattern(r"Mold clay|Shape", self._handle_shape_matter)
        self.register_pattern(r"Deal Cold Damage|Chill", self._handle_cold_damage)
        self.register_pattern(r"Resist Elements|Insulate", self._handle_resist_elements)
        self.register_pattern(r"Weld metal|Fuse", self._handle_fuse_matter)
        self.register_pattern(r"Deal Lightning Damage|Shock", self._handle_lightning_damage)
        self.register_pattern(r"Absorb Shock|Ground", self._handle_absorb_shock)
        self.register_pattern(r"Weaken metal|Rust", self._handle_rust)
        self.register_pattern(r"Skin becomes Iron|Plate", self._handle_harden_skin)
        self.register_pattern(r"Fix broken item|Repair", self._handle_repair)
        self.register_pattern(r"Deal Acid Damage|Melt", self._handle_acid_damage)
        self.register_pattern(r"Extinguish fires|Cool", self._handle_extinguish)
        self.register_pattern(r"Create weapon|Forge", self._handle_forge)
        self.register_pattern(r"Deal Sonic Damage|Shatter", self._handle_sonic_damage)
        self.register_pattern(r"Skin becomes Diamond", self._handle_harden_skin)
        self.register_pattern(r"Change material|Transmute", self._handle_transmute)
        self.register_pattern(r"Deal Force Damage|Explode", self._handle_force_damage)
        self.register_pattern(r"Bounce Physical|Rubber", self._handle_bounce_physical)
        self.register_pattern(r"Turn solid to liquid|Liquify", self._handle_liquify)
        self.register_pattern(r"Turn solid to gas|Vaporize|Gas", self._handle_mist_form)
        self.register_pattern(r"Reflect Ray|Mirror", self._handle_reflect_ray)
        self.register_pattern(r"Nuclear Damage|Fission", self._handle_nuclear_damage)
        self.register_pattern(r"Absorb All Damage|Void", self._handle_absorb_all)
        self.register_pattern(r"Lead to Gold|Gold", self._handle_create_gold)
        self.register_pattern(r"Disintegrate Matter|Unmake", self._handle_disintegrate_matter)
        self.register_pattern(r"Indestructible", self._handle_indestructible)
        self.register_pattern(r"Create Matter", self._handle_create_matter)

        # ============================================
        # SCHOOL OF MASS PATTERNS (Force)
        # ============================================
        self.register_pattern(r"Shove target away|Knockback", self._handle_push)
        self.register_pattern(r"Ignore Knockback|Brace|Heavy", self._handle_immovable)
        self.register_pattern(r"Reduce the weight|Lift|Levitate|Float", self._handle_levitate)
        self.register_pattern(r"Increase weight|Burden", self._handle_heavy_gravity)
        self.register_pattern(r"Fling enemy|Launch", self._handle_launch)
        self.register_pattern(r"Spider Climb|Shift gravity", self._handle_climb_speed)
        self.register_pattern(r"Reduce incoming Physical|Dense", self._handle_dense_skin)
        self.register_pattern(r"Constrict|Squeeze|Crush", self._handle_crush_grapple)
        self.register_pattern(r"Create a vacuum|Implode|Black Hole", self._handle_black_hole)
        self.register_pattern(r"Delete matter|Erase", self._handle_erase_matter)
        self.register_pattern(r"True Flight|Control Gravity", self._handle_fly_speed)
        self.register_pattern(r"Flip gravity|Reverse", self._handle_reverse_gravity)
        self.register_pattern(r"Shield of debris|Orbit|Force Field", self._handle_force_field)
        self.register_pattern(r"Stop all momentum|Nullify", self._handle_halt_movement)

        # ============================================
        # SCHOOL OF ANUMIS PATTERNS (Arcane)
        # ============================================
        self.register_pattern(r"Magic Missile|Bolt|Auto hit", self._handle_magic_missile)
        self.register_pattern(r"Counter|Stop spell", self._handle_counterspell)
        self.register_pattern(r"End active spell|Dispel", self._handle_counterspell)
        self.register_pattern(r"Create Dead Magic|Antimagic", self._handle_antimagic)
        self.register_pattern(r"Send to another plane|Banish", self._handle_banish)
        self.register_pattern(r"Planar Travel|Gate", self._handle_teleport_gate)
        self.register_pattern(r"Learn item|Identify", self._handle_identify)
        self.register_pattern(r"Nondetection|Mask", self._handle_nondetection)
        self.register_pattern(r"Prevent Casting|Silence", self._handle_silence)
        self.register_pattern(r"Speak any language|Tongues", self._handle_tongues)
        self.register_pattern(r"Block Teleportation|Anchor", self._handle_anchor_space)
        self.register_pattern(r"Alter Reality|Wish", self._handle_wish)
        self.register_pattern(r"Drain Magic slots|Source", self._handle_drain_magic)
        self.register_pattern(r"Magic Armor|Shield", self._handle_ac_buff)

        # ============================================
        # SCHOOL OF RATIO PATTERNS (Logic)
        # ============================================
        self.register_pattern(r"Calculate|Predict", self._handle_calculate_defense)
        self.register_pattern(r"True Strike|Bonus to Hit", self._handle_true_strike)
        self.register_pattern(r"Hit Weak Point|Fracture", self._handle_hit_weak_point)
        self.register_pattern(r"Create Automaton|Construct", self._handle_create_construct)
        self.register_pattern(r"Logic Trap|Pattern|Loop", self._handle_trap_logic)
        self.register_pattern(r"Debuff Enemy Armor|Deconstruct", self._handle_deconstruct_armor)
        self.register_pattern(r"Auto-Damage|Algorithm", self._handle_auto_damage)
        self.register_pattern(r"Split Damage|Divide", self._handle_split_damage)
        self.register_pattern(r"Change Physics Constant|Rewrite", self._handle_rewrite_physics)
        self.register_pattern(r"Delete Entity|Zero", self._handle_delete_entity)

        # ============================================
        # SCHOOL OF AURA PATTERNS (Spirit)
        # ============================================
        self.register_pattern(r"Psychic Damage|Mock", self._handle_psychic_damage)
        self.register_pattern(r"End Rage|Calm", self._handle_calm_emotions)
        self.register_pattern(r"Empathy Link|Bond", self._handle_empathy_link)
        self.register_pattern(r"Cause Fleeing|Fear|Terror", self._handle_flee_fear)
        self.register_pattern(r"Hesitate|Doubt|Despair", self._handle_hesitate)
        self.register_pattern(r"Attack All|Enrage|Berserk", self._handle_enrage)
        self.register_pattern(r"Befriend|Charm|Love|Permanent Thrall", self._handle_dominate_charm)
        self.register_pattern(r"Buff HP|Heroism|Inspire", self._handle_inspire)
        self.register_pattern(r"Break Mind|Insanity|Shatter", self._handle_insanity)
        self.register_pattern(r"Zone of Peace|Sanctuary", self._handle_sanctuary)

        # ============================================
        # SCHOOL OF LEX PATTERNS (Willpower)
        # ============================================
        self.register_pattern(r"Stop movement|Halt|Kneel|Command", self._handle_command_halt)
        self.register_pattern(r"Unlock \(Command\)|Open", self._handle_open_mechanism)
        self.register_pattern(r"Resist Pain|Ignore", self._handle_ignore_needs)
        self.register_pattern(r"Block Path|Deny|Forbid", self._handle_block_path_mental)
        self.register_pattern(r"Prevent Lying|Zone of Truth", self._handle_prevent_lying)
        self.register_pattern(r"Force Speech|Speak", self._handle_force_speech)
        self.register_pattern(r"Psychic Damage|Pain", self._handle_psychic_damage)
        self.register_pattern(r"Contract|Bond|Oath", self._handle_oath_bond)
        self.register_pattern(r"Mind Control|Dominate", self._handle_dominate_charm)
        self.register_pattern(r"Banishment|Exile", self._handle_banishment)
        self.register_pattern(r"Power Word Kill|Kill", self._handle_power_word_kill)
        self.register_pattern(r"New Physics Law|Law", self._handle_new_law)
        self.register_pattern(r"Mass Awe|Legend", self._handle_mass_awe)

        # ============================================
        # SCHOOL OF MOTUS PATTERNS (Speed/Sonic)
        # ============================================
        self.register_pattern(r"Quick low-damage|Snap", self._handle_quick_attack)
        self.register_pattern(r"Reaction AC bonus|Duck", self._handle_reaction_ac)
        self.register_pattern(r"5ft Shift|Step|Dash|Haste", self._handle_dash)
        self.register_pattern(r"Multi-hit attack|Barrage", self._handle_multihit_barrage)
        self.register_pattern(r"Move through enemy|Weave", self._handle_phase_move)
        self.register_pattern(r"Teleport 10ft|Leap|Warp|Blink", self._handle_teleport_leap)
        self.register_pattern(r"Snatch arrow|Catch", self._handle_snatch_missile)
        self.register_pattern(r"Line Charge|Blitz", self._handle_charge)
        self.register_pattern(r"Damage scales with Speed|Impact", self._handle_speed_damage)
        self.register_pattern(r"Create decoy|Afterimage", self._handle_decoy_clones)
        self.register_pattern(r"Repeat last action|Loop", self._handle_repeat_action)
        self.register_pattern(r"Rapid aging|Age", self._handle_rapid_aging)
        self.register_pattern(r"Undo recent damage|Rewind", self._handle_rewind_damage)
        self.register_pattern(r"Create travel gate|Portal", self._handle_teleport_gate)
        self.register_pattern(r"Delay enemy turn|Lag", self._handle_delay_turn)
        self.register_pattern(r"Phase out of reality|Stutter", self._handle_phase_reality)
        self.register_pattern(r"Exist twice|Paradox", self._handle_double_turn)
        self.register_pattern(r"Restart the combat|Reset", self._handle_reset_round)
        self.register_pattern(r"Predict exact future|Timeline", self._handle_predict_future)
        self.register_pattern(r"Attack every target|Infinite", self._handle_infinite_attack)
        self.register_pattern(r"Non-Existence|Gone", self._handle_indestructible)
        self.register_pattern(r"Reload Save|Retcon|Reality", self._handle_retcon_save)
    
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
        attacker = ctx.get("attacker")
        if engine and attacker:
           # Spawn adjacent
           name = match.group(0).split(' ')[1] if ' ' in match.group(0) else "Summon"
           minion = engine.spawn_minion(name, attacker.x + 1, attacker.y)
           if "log" in ctx: ctx["log"].append(f"{minion.name} Summoned!")

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
        # Ex: Deal 1d6 Fire Damage OR Deal Fire Damage (no dice = use tier scaling)
        # Uses Power_Power.csv for tier-based damage scaling
        amt_str = match.group(1)
        die_str = match.group(2)
        dmg_type = match.group(3)
        
        target = ctx.get("target")
        attacker = ctx.get("attacker")
        
        if target and attacker:
            dmg = 0
            
            if amt_str and die_str:  # Explicit dice like "2d6"
                num = int(amt_str)
                sides = int(die_str)
                dmg = sum(random.randint(1, sides) for _ in range(num))
            elif amt_str:  # Flat damage like "5"
                dmg = int(amt_str)
            else:
                # No dice specified - use tier scaling from Power_Power.csv
                tier = ctx.get("tier", 1)
                
                # Get damage dice from DataLoader
                from .data_loader import DataLoader
                loader = DataLoader()
                dice_str = loader.get_tier_damage(tier)  # e.g. "2d6"
                
                # Parse and roll dice
                if "d" in dice_str:
                    parts = dice_str.lower().split("d")
                    num = int(parts[0]) if parts[0] else 1
                    sides = int(parts[1]) if len(parts) > 1 else 6
                    dmg = sum(random.randint(1, sides) for _ in range(num))
                else:
                    dmg = int(dice_str) if dice_str.isdigit() else 1
                
                # Add stat modifier
                stat_val = attacker.data.get("Stats", {}).get("Might", 10)
                mod = (stat_val - 10) // 2
                dmg += mod
                
            dmg = max(1, dmg)  # Minimum 1 damage
            
            # Apply damage directly to target HP
            target.hp -= dmg
            if "log" in ctx: 
                ctx["log"].append(f"{dmg} {dmg_type} damage to {target.name}!")
            
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

    def _handle_apply_burning(self, match, ctx):
        if "target" in ctx and ctx["target"]:
            # Set flag and apply timed effect to clear it
            ctx["target"].is_burning = True
            ctx["target"].apply_effect("Burning", duration=3, on_expire="is_burning")
            if "log" in ctx: ctx["log"].append(f"{ctx['target'].name} is BURNING!")

    def _handle_apply_frozen(self, match, ctx):
        if "target" in ctx and ctx["target"]:
            ctx["target"].is_frozen = True
            ctx["target"].apply_effect("Frozen", duration=1, on_expire="is_frozen")
            if "log" in ctx: ctx["log"].append(f"{ctx['target'].name} is FROZEN!")

    def _handle_apply_staggered(self, match, ctx):
        if "target" in ctx and ctx["target"]:
            ctx["target"].is_staggered = True
            ctx["target"].apply_effect("Staggered", duration=1, on_expire="is_staggered")
            if "log" in ctx: ctx["log"].append(f"{ctx['target'].name} is STAGGERED!")

    def _handle_apply_bleeding(self, match, ctx):
        if "target" in ctx and ctx["target"]:
            ctx["target"].is_bleeding = True
            ctx["target"].apply_effect("Bleeding", duration=3, on_expire="is_bleeding")
            if "log" in ctx: ctx["log"].append(f"{ctx['target'].name} is BLEEDING!")

    def _handle_magic_missile(self, match, ctx):
        """
        Magic Missile - auto-hit arcane damage spell.
        Deals tier-based damage automatically without attack roll.
        """
        target = ctx.get("target")
        attacker = ctx.get("attacker")
        
        if target and attacker:
            import random
            tier = ctx.get("tier", 2)  # Default tier 2 for Bolt
            
            # Get damage from Power_Power.csv
            from .data_loader import DataLoader
            loader = DataLoader()
            dice_str = loader.get_tier_damage(tier)
            
            # Parse and roll dice
            dmg = 0
            if "d" in dice_str.lower():
                parts = dice_str.lower().split("d")
                num = int(parts[0]) if parts[0] else 1
                sides = int(parts[1]) if len(parts) > 1 else 6
                dmg = sum(random.randint(1, sides) for _ in range(num))
            else:
                dmg = int(dice_str) if dice_str.isdigit() else 2
            
            # Add stat modifier (Knowledge for arcane)
            stat_val = attacker.data.get("Stats", {}).get("Knowledge", 10)
            mod = (stat_val - 10) // 2
            dmg = max(1, dmg + mod)
            
            # Apply damage - auto hit, no attack roll needed
            target.hp -= dmg
            if "log" in ctx:
                ctx["log"].append(f"{dmg} Arcane damage to {target.name}! (Auto-hit)")

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
    # SCHOOL OF NEXUS HANDLERS
    # ============================================

    def _handle_fire_damage(self, match, ctx):
        """Deal Fire Damage"""
        ctx["damage_type"] = "Fire"
        if "log" in ctx: ctx["log"].append("Damage Type: Fire")

    def _handle_cold_damage(self, match, ctx):
        """Deal Cold Damage"""
        ctx["damage_type"] = "Cold"
        # Chance to slow/freeze?
        if "log" in ctx: ctx["log"].append("Damage Type: Cold")

    def _handle_lightning_damage(self, match, ctx):
        """Deal Lightning Damage"""
        ctx["damage_type"] = "Lightning"
        if "log" in ctx: ctx["log"].append("Damage Type: Lightning")

    def _handle_acid_damage(self, match, ctx):
        """Deal Acid Damage"""
        ctx["damage_type"] = "Acid"
        if "log" in ctx: ctx["log"].append("Damage Type: Acid")

    def _handle_sonic_damage(self, match, ctx):
        """Deal Sonic Damage"""
        ctx["damage_type"] = "Sonic"
        if "log" in ctx: ctx["log"].append("Damage Type: Sonic")

    def _handle_force_damage(self, match, ctx):
        """Deal Force Damage"""
        ctx["damage_type"] = "Force"
        if "log" in ctx: ctx["log"].append("Damage Type: Force")

    def _handle_nuclear_damage(self, match, ctx):
        """Deal Nuclear/Radiation Damage"""
        ctx["damage_type"] = "Nuclear"
        ctx["is_crit"] = True # Nukes hurt
        if "log" in ctx: ctx["log"].append("NUCLEAR DAMAGE!")

    def _handle_harden_skin(self, match, ctx):
        """Bonus AC / Iron Skin"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            bonus = 2
            if "Diamond" in match.group(0): bonus = 5
            if hasattr(target, "apply_effect"):
                target.apply_effect("HardenedSkin", duration=3)
            if "log" in ctx: ctx["log"].append(f"{target.name}'s skin hardens! (+{bonus} AC)")

    def _handle_resist_elements(self, match, ctx):
        """Resist Elemental Damage"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.active_effects.append({"name": "ResistFire", "duration": 3})
            target.active_effects.append({"name": "ResistCold", "duration": 3})
            target.active_effects.append({"name": "ResistLightning", "duration": 3})
            if "log" in ctx: ctx["log"].append(f"{target.name} gains Elemental Resistance.")

    def _handle_absorb_shock(self, match, ctx):
        """Absorb Lightning/Shock"""
        if "log" in ctx: ctx["log"].append("Shock Absorption active.")

    def _handle_extinguish(self, match, ctx):
        """Put out fires"""
        if "log" in ctx: ctx["log"].append("Fires extinguished.")

    def _handle_bounce_physical(self, match, ctx):
        """Reflect/Bounce physical attacks"""
        ctx["reflect_physical"] = True
        if "log" in ctx: ctx["log"].append("Rubber Skin! Physical attacks bounce off.")

    def _handle_reflect_ray(self, match, ctx):
        """Reflect Ray spells"""
        ctx["reflect_rays"] = True
        if "log" in ctx: ctx["log"].append("Mirror Shield! Rays reflected.")

    def _handle_absorb_all(self, match, ctx):
        """Absorb all damage types (Void)"""
        ctx["damage_immunity"] = True
        if "log" in ctx: ctx["log"].append("Void Form! All damage absorbed.")

    def _handle_indestructible(self, match, ctx):
        """Cannot be hurt"""
        ctx["invulnerable"] = True
        if "log" in ctx: ctx["log"].append("Indestructible!")

    def _handle_mist_form(self, match, ctx):
        """Turn to Gas/Mist"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.is_ethereal = True # Close enough
            if hasattr(target, "apply_effect"):
                target.apply_effect("MistForm", duration=3)
            if "log" in ctx: ctx["log"].append(f"{target.name} turns into Mist!")

    def _handle_shape_matter(self, match, ctx):
        """Mold stone/wood"""
        if "log" in ctx: ctx["log"].append("Matter shaped.")

    def _handle_fuse_matter(self, match, ctx):
        """Weld/Fuse"""
        if "log" in ctx: ctx["log"].append("Materials fused.")

    def _handle_rust(self, match, ctx):
        """Rust metal"""
        target = ctx.get("target")
        if target:
            if "log" in ctx: ctx["log"].append(f"{target.name}'s gear rusts!")

    def _handle_repair(self, match, ctx):
        """Repair item"""
        if "log" in ctx: ctx["log"].append("Item repaired.")

    def _handle_forge(self, match, ctx):
        """Create weapon"""
        if "log" in ctx: ctx["log"].append("Weapon forged from raw materials.")

    def _handle_transmute(self, match, ctx):
        """Change material"""
        if "log" in ctx: ctx["log"].append("Material transmuted.")

    def _handle_liquify(self, match, ctx):
        """Turn solid to liquid"""
        if "log" in ctx: ctx["log"].append("Solid liquified.")

    def _handle_create_gold(self, match, ctx):
        """Leaf into Gold"""
        if "log" in ctx: ctx["log"].append("Gold created!")

    def _handle_disintegrate_matter(self, match, ctx):
        """Destroy object"""
        if "log" in ctx: ctx["log"].append("Matter disintegrated.")

    def _handle_create_matter(self, match, ctx):
        """Create object from nothing"""
        if "log" in ctx: ctx["log"].append("Matter created.")

    def _handle_create_matter(self, match, ctx):
        """Create object from nothing"""
        if "log" in ctx: ctx["log"].append("Matter created.")

    # ============================================
    # SCHOOL OF ORDO HANDLERS
    # ============================================

    def _handle_halt_movement(self, match, ctx):
        """Stop Movement"""
        target = ctx.get("target")
        if target:
            target.movement_remaining = 0
            if hasattr(target, "apply_effect"):
                target.apply_effect("Halted", duration=1)
            if "log" in ctx: ctx["log"].append(f"{target.name} Halted! (0 Move)")

    def _handle_stand_up(self, match, ctx):
        """Stand from Prone"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.is_prone = False
            if "log" in ctx: ctx["log"].append(f"{target.name} Stands Up.")

    def _handle_hold_door(self, match, ctx):
        """Hold Door/Object"""
        if "log" in ctx: ctx["log"].append("Door held shut.")

    def _handle_trip(self, match, ctx):
        """Trip target"""
        target = ctx.get("target")
        if target:
            target.is_prone = True
            if "log" in ctx: ctx["log"].append(f"{target.name} Tripped!")

    def _handle_natural_armor_buff(self, match, ctx):
        """Natural Armor Buff"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            if "log" in ctx: ctx["log"].append(f"{target.name} gains Natural Armor.")

    def _handle_ignore_needs(self, match, ctx):
        """Ignore Hunger/Fatigue"""
        if "log" in ctx: ctx["log"].append("Needs ignored (Sustain).")

    def _handle_create_wall(self, match, ctx):
        """Create Wall/Cage/Barricade"""
        engine = ctx.get("engine")
        target = ctx.get("target")
        attacker = ctx.get("attacker")
        if engine:
            # If target exists, cage THEM. If not, wall adjacent to Attacker.
            x, y = (target.x, target.y) if target else (attacker.x + 1, attacker.y) if attacker else (0,0)
            if engine.create_wall(x, y):
                if "log" in ctx: ctx["log"].append(f"Structure created at {x},{y} (Wall/Cage).")
            else:
                if "log" in ctx: ctx["log"].append("Failed to create structure (Blocked).")

    def _handle_anchor(self, match, ctx):
        """Become Immovable"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            if "log" in ctx: ctx["log"].append(f"{target.name} is Anchored (Immovable).")

    def _handle_petrify(self, match, ctx):
        """Turn to Stone"""
        target = ctx.get("target")
        if target:
            target.is_petrified = True
            if hasattr(target, "apply_effect"):
                target.apply_effect("Petrified", duration=3)
            if "log" in ctx: ctx["log"].append(f"{target.name} is Petrified!")

    def _handle_temp_hp_buff(self, match, ctx):
        """Gain Temp HP"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            amt = random.randint(5, 10)
            if "log" in ctx: ctx["log"].append(f"{target.name} gains {amt} Temp HP.")

    def _handle_absorb_damage(self, match, ctx):
        """Take damage for ally"""
        if "log" in ctx: ctx["log"].append("Damage absorbed for ally.")

    def _handle_stasis(self, match, ctx):
        """Freeze in time"""
        target = ctx.get("target")
        if target:
            target.is_stunned = True # Closest mechanic
            if hasattr(target, "apply_effect"):
                target.apply_effect("Stasis", duration=1)
            if "log" in ctx: ctx["log"].append(f"{target.name} in Stasis!")

    def _handle_reflect_damage(self, match, ctx):
        """Return damage"""
        if "log" in ctx: ctx["log"].append("Damage reflected!")

    def _handle_feign_death(self, match, ctx):
        """Statue/Feign Death"""
        if "log" in ctx: ctx["log"].append("Feigning Death.")

    def _handle_stop_heart(self, match, ctx):
        """Arrest/Stop Heart"""
        target = ctx.get("target")
        if target:
            # Massive damage or save vs death
            dmg = 20
            target.hp = max(0, target.hp - dmg)
            if "log" in ctx: ctx["log"].append(f"{target.name}'s Heart Stopped! ({dmg} dmg)")

    def _handle_invulnerability(self, match, ctx):
        """Immunity/Invincible"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            if hasattr(target, "apply_effect"):
                target.apply_effect("Invulnerable", duration=1)
            if "log" in ctx: ctx["log"].append(f"{target.name} is Invulnerable!")

    def _handle_infinite_stamina(self, match, ctx):
        """Run forever"""
        if "log" in ctx: ctx["log"].append("Infinite Stamina.")

    def _handle_shatter(self, match, ctx):
        """Crystallize/Shatter"""
        target = ctx.get("target")
        if target:
            # Multiplier on next hit?
            if "log" in ctx: ctx["log"].append(f"{target.name} Crystallized (Fragile)!")

    def _handle_fortress(self, match, ctx):
        """Create Fortress/Monolith"""
        if "log" in ctx: ctx["log"].append("Fortress created.")

    def _handle_time_stop(self, match, ctx):
        """Stop Time (End Time)"""
        if "log" in ctx: ctx["log"].append("TIME STOPPED!")

    def _handle_immortality(self, match, ctx):
        """Eternal/Cannot Die"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.cannot_die = True
            if "log" in ctx: ctx["log"].append(f"{target.name} is Eternal (Cannot Die)!")

    def _handle_create_land(self, match, ctx):
        """Create Land"""
        if "log" in ctx: ctx["log"].append("Land created.")

    # ============================================
    # SCHOOL OF MASS HANDLERS (Force/Gravity)
    # ============================================

    def _handle_gravity_well(self, match, ctx):
        """Pull/Gravity Well"""
        # Mechanically similar to Pull/Restrain
        if "log" in ctx: ctx["log"].append("Gravity Well! Enemies pulled/slowed.")

    def _handle_levitate(self, match, ctx):
        """Float/Levitate"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.has_fly_speed = True # Effective flight/hover
            if "log" in ctx: ctx["log"].append(f"{target.name} Levitates.")

    def _handle_heavy_gravity(self, match, ctx):
        """Burden/Heavy"""
        target = ctx.get("target")
        if target:
            target.movement_remaining = max(0, target.movement_remaining - 15)
            if "log" in ctx: ctx["log"].append(f"{target.name} is Heavy (Slowed).")

    def _handle_launch(self, match, ctx):
        """Fling/Launch"""
        # Big push
        target = ctx.get("target")
        if target:
             # Logic to push far?
             if "log" in ctx: ctx["log"].append(f"{target.name} Launched into the air!")

    def _handle_crush_grapple(self, match, ctx):
        """Crush/Constrict"""
        target = ctx.get("target")
        if target:
            target.is_grappled = True
            target.is_restrained = True
            dmg = random.randint(1,8)
            target.hp -= dmg
            if "log" in ctx: ctx["log"].append(f"{target.name} Crushed! ({dmg} dmg + Restrained)")

    def _handle_reverse_gravity(self, match, ctx):
        """Reverse Gravity"""
        # Everyone falls up?
        if "log" in ctx: ctx["log"].append("Gravity Reversed! Targets fall upward.")

    def _handle_black_hole(self, match, ctx):
        """Black Hole/Implode"""
        # Massive damage + pull
        ctx["damage_type"] = "Force"
        ctx["is_crit"] = True
        if "log" in ctx: ctx["log"].append("Black Hole created! Massive Force damage.")

    def _handle_force_field(self, match, ctx):
        """Shield/Field/Orbit"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.active_effects.append({"name": "ForceField", "duration": 3})
            if "log" in ctx: ctx["log"].append(f"{target.name} protected by Force Field.")

    def _handle_erase_matter(self, match, ctx):
        """Erase/Delete"""
        # Instakill possibility?
        if "log" in ctx: ctx["log"].append("Matter Erased from existence.")

    def _handle_dense_skin(self, match, ctx):
        """Dense/Reduce Phys Dmg"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            if "log" in ctx: ctx["log"].append(f"{target.name} becomes Dense (Phys Resist).")

    # ============================================
    # SCHOOL OF ANUMIS HANDLERS (Arcane)
    # ============================================

    def _handle_apply_burning(self, match, ctx):
        if "target" in ctx and ctx["target"]:
            # Set flag and apply timed effect to clear it
            ctx["target"].is_burning = True
            ctx["target"].apply_effect("Burning", duration=3, on_expire="is_burning")
            if "log" in ctx: ctx["log"].append(f"{ctx['target'].name} is BURNING!")

    def _handle_apply_frozen(self, match, ctx):
        if "target" in ctx and ctx["target"]:
            ctx["target"].is_frozen = True
            ctx["target"].apply_effect("Frozen", duration=1, on_expire="is_frozen")
            if "log" in ctx: ctx["log"].append(f"{ctx['target'].name} is FROZEN!")

    def _handle_apply_staggered(self, match, ctx):
        if "target" in ctx and ctx["target"]:
            ctx["target"].is_staggered = True
            ctx["target"].apply_effect("Staggered", duration=1, on_expire="is_staggered")
            if "log" in ctx: ctx["log"].append(f"{ctx['target'].name} is STAGGERED!")

    def _handle_apply_bleeding(self, match, ctx):
        if "target" in ctx and ctx["target"]:
            ctx["target"].is_bleeding = True
            ctx["target"].apply_effect("Bleeding", duration=3, on_expire="is_bleeding")
            if "log" in ctx: ctx["log"].append(f"{ctx['target'].name} is BLEEDING!")

    def _handle_magic_missile(self, match, ctx):
        """Bolt/Auto-Hit"""
        ctx["auto_hit"] = True 
        ctx["damage_type"] = "Force"
        if "log" in ctx: ctx["log"].append("Magic Missile (Auto-Hit Force).")

    def _handle_counterspell(self, match, ctx):
        """Counter/Dispel"""
        # Hard to impelment without a stack, but we can log unique effect
        if "log" in ctx: ctx["log"].append("Spell Countered/Dispelled!")

    def _handle_antimagic(self, match, ctx):
        """Antimagic Zone"""
        if "log" in ctx: ctx["log"].append("Antimagic Zone created.")

    def _handle_banish(self, match, ctx):
        """Banish/Exile"""
        target = ctx.get("target")
        if target:
            # Remove from combat temporarily? 
            # For now, Stun + Invis?
            target.is_stunned = True
            target.is_invisible = True
            if "log" in ctx: ctx["log"].append(f"{target.name} Banished to another plane!")

    def _handle_teleport_gate(self, match, ctx):
        """Gate/Teleport"""
        if "log" in ctx: ctx["log"].append("Teleportation Gate opened.")

    def _handle_nondetection(self, match, ctx):
        """Mask/Anti-Scry"""
        if "log" in ctx: ctx["log"].append("Nondetection active.")

    def _handle_silence(self, match, ctx):
        """Silence/Prevent Casting"""
        target = ctx.get("target")
        if target:
            target.active_effects.append({"name": "Silenced", "duration": 3})
            if "log" in ctx: ctx["log"].append(f"{target.name} Silenced!")

    def _handle_tongues(self, match, ctx):
        """Speak any language"""
        if "log" in ctx: ctx["log"].append("Tongues active.")

    def _handle_identify(self, match, ctx):
        """Identify item"""
        if "log" in ctx: ctx["log"].append("Item Identified.")

    def _handle_anchor_space(self, match, ctx):
        """Block Teleport"""
        if "log" in ctx: ctx["log"].append("Space Anchored (No Teleport).")

    def _handle_wish(self, match, ctx):
        """Alter Reality"""
        if "log" in ctx: ctx["log"].append("WISH GRANTED (Reality Altered).")

    def _handle_drain_magic(self, match, ctx):
        """Source/Drain Slots"""
        target = ctx.get("target")
        if target:
            target.fp = max(0, target.fp - 10)
            target.sp = max(0, target.sp - 1)
            if "log" in ctx: ctx["log"].append(f"{target.name} drained of Magic!")

    # ============================================
    # SCHOOL OF RATIO HANDLERS (Logic/Shock)
    # ============================================

    def _handle_calculate_defense(self, match, ctx):
        """Calculate/Predict"""
        # Int/Logic to Defense
        if "log" in ctx: ctx["log"].append("Calculating Defense vector.")

    def _handle_hit_weak_point(self, match, ctx):
        """Fracture/Weak Point"""
        ctx["is_crit"] = True
        if "log" in ctx: ctx["log"].append("Weak Point struck! (Critical)")

    def _handle_create_construct(self, match, ctx):
        """Construct/Automaton"""
        engine = ctx.get("engine")
        attacker = ctx.get("attacker")
        if engine and attacker:
             minion = engine.spawn_minion("Automaton", attacker.x + 1, attacker.y)
             if "log" in ctx: ctx["log"].append(f"Automaton Constructed at {minion.x},{minion.y}.")

    def _handle_trap_logic(self, match, ctx):
        """Pattern/Trap"""
        if "log" in ctx: ctx["log"].append("Logic Trap set.")

    def _handle_deconstruct_armor(self, match, ctx):
        """Deconstruct/Debuff Armor"""
        target = ctx.get("target")
        if target:
            # We don't have explicit AR yet, but usually it's Damage Reduction
            if "log" in ctx: ctx["log"].append(f"{target.name}'s Armor Deconstructed.")

    def _handle_auto_damage(self, match, ctx):
        """Algorithm/Auto-Damage"""
        # Guaranteed damage
        ctx["auto_hit"] = True
        if "log" in ctx: ctx["log"].append("Algorithm execution: Auto-Damage.")

    def _handle_split_damage(self, match, ctx):
        """Divide/Split"""
        if "log" in ctx: ctx["log"].append("Damage Divided among foes.")

    def _handle_rewrite_physics(self, match, ctx):
        """Rewrite/Change Constant"""
        if "log" in ctx: ctx["log"].append("Physics Constants Rewritten.")

    def _handle_delete_entity(self, match, ctx):
        """Zero/Delete"""
        target = ctx.get("target")
        if target:
            target.hp = 0
            target.is_dead = True
            if "log" in ctx: ctx["log"].append(f"{target.name} DELETED by Ratio.")

    # ============================================
    # SCHOOL OF AURA HANDLERS (Spirit/Charm)
    # ============================================

    def _handle_psychic_damage(self, match, ctx):
        """Mock/Pain"""
        ctx["damage_type"] = "Psychic"
        if "log" in ctx: ctx["log"].append("Psychic Damage dealt.")

    def _handle_calm_emotions(self, match, ctx):
        """Calm/Peace"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            # Remove Rage?
            if "log" in ctx: ctx["log"].append(f"{target.name} Calmed.")

    def _handle_empathy_link(self, match, ctx):
        """Bond/Link"""
        if "log" in ctx: ctx["log"].append("Empathy Link established.")

    def _handle_flee_fear(self, match, ctx):
        """Fear/Terror"""
        target = ctx.get("target")
        if target:
            target.is_frightened = True
            if hasattr(target, "apply_effect"):
                target.apply_effect("Frightened", duration=3)
            if "log" in ctx: ctx["log"].append(f"{target.name} Fess in Terror!")

    def _handle_hesitate(self, match, ctx):
        """Doubt/Hesitate"""
        target = ctx.get("target")
        if target:
            target.is_stunned = True # Skip turn basically
            if "log" in ctx: ctx["log"].append(f"{target.name} Hesitates (Skip Turn).")

    def _handle_enrage(self, match, ctx):
        """Enrage/Berserk"""
        target = ctx.get("target")
        if target:
             # Force attack nearest
             if "log" in ctx: ctx["log"].append(f"{target.name} Enraged!")

    def _handle_dominate_charm(self, match, ctx):
        """Charm/Dominate/Thrall"""
        target = ctx.get("target")
        if target:
            target.is_charmed = True
            if hasattr(target, "apply_effect"):
                target.apply_effect("Charmed", duration=3)
            if "log" in ctx: ctx["log"].append(f"{target.name} is Dominated.")

    def _handle_inspire(self, match, ctx):
        """Inspire/Heroism"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            # Buff?
            if "log" in ctx: ctx["log"].append(f"{target.name} Inspired!")

    def _handle_insanity(self, match, ctx):
        """Shatter Mind"""
        if "log" in ctx: ctx["log"].append("Mind Shattered (Insanity).")

    # ============================================
    # SCHOOL OF LEX HANDLERS (Psychic/Willpower)
    # ============================================

    def _handle_command_halt(self, match, ctx):
        """Halt/Drop/Kneel"""
        target = ctx.get("target")
        if target:
            cmd = match.group(0).lower()
            if "halt" in cmd: target.movement_remaining = 0
            if "kneel" in cmd: target.is_prone = True
            if "drop" in cmd: pass # Disarm logic
            if "log" in ctx: ctx["log"].append(f"Command: {cmd.title()}!")

    def _handle_prevent_lying(self, match, ctx):
        """Truth/Zone"""
        if "log" in ctx: ctx["log"].append("Zone of Truth active.")

    def _handle_block_path_mental(self, match, ctx):
        """Deny/Forbid"""
        if "log" in ctx: ctx["log"].append("Path Blocked (Mental).")

    def _handle_force_speech(self, match, ctx):
        """Speak/Confess"""
        if "log" in ctx: ctx["log"].append("Forced Speech.")

    def _handle_oath_bond(self, match, ctx):
        """Oath/Contract"""
        if "log" in ctx: ctx["log"].append("Magical Oath bound.")

    def _handle_power_word_kill(self, match, ctx):
        """Kill"""
        target = ctx.get("target")
        if target:
            if target.hp < 100: # Classic thresh?
                target.hp = 0
                target.is_dead = True
                if "log" in ctx: ctx["log"].append("POWER WORD KILL!")
            else:
                 if "log" in ctx: ctx["log"].append("Power Word Kill failed (HP too high).")

    def _handle_banishment(self, match, ctx):
        """Exile"""
        # Same as Anumis Banish essentially
        if "log" in ctx: ctx["log"].append("Banished (Exile).")

    def _handle_mass_awe(self, match, ctx):
        """Legend/Awe"""
        if "log" in ctx: ctx["log"].append("Mass Awe effect.")

    def _handle_new_law(self, match, ctx):
        """Law/Decree"""
        if "log" in ctx: ctx["log"].append("New Law Decreed.")

    # ============================================
    # SCHOOL OF MOTUS HANDLERS (Speed/Sonic)
    # ============================================

    def _handle_dash(self, match, ctx):
        """Step/Dash/Haste"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.movement_remaining += 30
            if "log" in ctx: ctx["log"].append(f"{target.name} Dashes (+30ft Move).")

    def _handle_reaction_ac(self, match, ctx):
        """Duck/Reaction Bonus"""
        if "log" in ctx: ctx["log"].append("Reaction AC Bonus active.")

    def _handle_multihit_barrage(self, match, ctx):
        """Barrage/Multi-hit"""
        if "log" in ctx: ctx["log"].append("Multi-hit Barrage!")

    def _handle_phase_move(self, match, ctx):
        """Weave/Phase Move"""
        # Move through enemies
        if "log" in ctx: ctx["log"].append("Weaving through enemies.")

    def _handle_teleport_leap(self, match, ctx):
        """Leap/Warp/Blink"""
        # 10ft or 60ft
        if "log" in ctx: ctx["log"].append("Teleport/Warp.")

    def _handle_sonic_vibrate(self, match, ctx):
        """Vibrate/Sonic Dmg bypass"""
        ctx["damage_type"] = "Sonic"
        ctx["ignore_armor"] = True
        if "log" in ctx: ctx["log"].append("Sonic Vibration (Bypass Armor).")

    def _handle_snatch_missile(self, match, ctx):
        """Catch/Snatch"""
        if "log" in ctx: ctx["log"].append("Missile Snatched!")

    def _handle_decoy_clones(self, match, ctx):
        """Afterimage/Mirror"""
        if "log" in ctx: ctx["log"].append("Decoy Clones created.")

    def _handle_repeat_action(self, match, ctx):
        """Loop/Repeat"""
        if "log" in ctx: ctx["log"].append("Action Looped (Repeat).")

    def _handle_rapid_aging(self, match, ctx):
        """Age"""
        target = ctx.get("target")
        if target:
            target.stats["Might"] = max(1, target.stats["Might"] - 2)
            if "log" in ctx: ctx["log"].append(f"{target.name} Aged Rapidly (-Might).")

    def _handle_rewind_damage(self, match, ctx):
        """Rewind/Undo"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.hp += 10 # Mock undo
            if "log" in ctx: ctx["log"].append("Time Rewound (HP Restored).")

    def _handle_delay_turn(self, match, ctx):
        """Lag/Delay"""
        if "log" in ctx: ctx["log"].append("Enemy Turn Delayed (Lag).")

    def _handle_phase_reality(self, match, ctx):
        """Stutter/Phase Out"""
        if "log" in ctx: ctx["log"].append("Phased out of Reality.")

    def _handle_double_turn(self, match, ctx):
        """Paradox/Double Turn"""
        if "log" in ctx: ctx["log"].append("PARADOX: Double Turn!")

    def _handle_reset_round(self, match, ctx):
        """Reset Round"""
        if "log" in ctx: ctx["log"].append("Combat Round RESET.")

    def _handle_predict_future(self, match, ctx):
        """Timeline/Predict"""
        if "log" in ctx: ctx["log"].append("Future Predicted.")

    def _handle_infinite_attack(self, match, ctx):
        """Infinite/Attack All"""
        # AoE everything
        if "log" in ctx: ctx["log"].append("Infinite Attack (All Targets).")

    def _handle_retcon_save(self, match, ctx):
        """Reality/Reload Save"""
        if "log" in ctx: ctx["log"].append("Reality Retconned (Reload Save).")
    
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

    # ============================================
    # SCHOOL OF MASS HANDLERS (Gravity/Force)
    # ============================================

    def _handle_push(self, match, ctx):
        """Push target away"""
        target = ctx.get("target")
        attacker = ctx.get("attacker")
        if target and attacker:
            dx = target.x - attacker.x
            dy = target.y - attacker.y
            dist = 1
            if "Launch" in match.group(0): dist = 6 # 30ft
            
            # Normalize direction
            if dx != 0: dx = 1 if dx > 0 else -1
            if dy != 0: dy = 1 if dy > 0 else -1
            
            target.x += dx * dist
            target.y += dy * dist
            if "log" in ctx: ctx["log"].append(f"{target.name} Pushed {dist*5}ft away!")

    def _handle_pull(self, match, ctx):
        """Pull target closer"""
        target = ctx.get("target")
        attacker = ctx.get("attacker")
        if target and attacker:
            dx = attacker.x - target.x
            dy = attacker.y - target.y
            # Move towards attacker 1 square
            if dx != 0: dx = 1 if dx > 0 else -1
            if dy != 0: dy = 1 if dy > 0 else -1
            target.x += dx
            target.y += dy
            if "log" in ctx: ctx["log"].append(f"{target.name} Pulled closer!")

    def _handle_levitate(self, match, ctx):
        """Float/Levitate"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.is_flying = True
            if "log" in ctx: ctx["log"].append(f"{target.name} begins to Levitate.")

    def _handle_fly(self, match, ctx):
        """True Flight"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.has_fly_speed = True
            if "log" in ctx: ctx["log"].append(f"{target.name} gains Flight!")

    def _handle_jump_boost(self, match, ctx):
        """Boost jump"""
        if "log" in ctx: ctx["log"].append("Jump height/distance boosted.")

    def _handle_climb(self, match, ctx):
        """Spider Climb"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.has_climb_speed = True
            if "log" in ctx: ctx["log"].append(f"{target.name} gains Spider Climb.")

    def _handle_slow_fall(self, match, ctx):
        """Feather Fall"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            if "log" in ctx: ctx["log"].append(f"{target.name} falls slowly (Feather Fall).")

    def _handle_slam(self, match, ctx):
        """Knock Prone"""
        target = ctx.get("target")
        if target:
            target.is_prone = True
            if "log" in ctx: ctx["log"].append(f"{target.name} Slammed Prone!")

    def _handle_burden(self, match, ctx):
        """Increase weight / Slow"""
        target = ctx.get("target")
        if target:
            target.movement //= 2
            if "log" in ctx: ctx["log"].append(f"{target.name} is Burdened (Half Speed).")

    def _handle_crush(self, match, ctx):
        """Constrict/Grapple"""
        target = ctx.get("target")
        if target:
            target.is_grappled = True
            dmg = random.randint(1, 6)
            target.hp -= dmg
            if "log" in ctx: ctx["log"].append(f"{target.name} Crushed for {dmg} damage!")

    def _handle_flatten(self, match, ctx):
        """Compress to 2D"""
        target = ctx.get("target")
        if target:
            target.is_prone = True
            target.is_restrained = True
            if "log" in ctx: ctx["log"].append(f"{target.name} Flattened! (Prone + Restrained)")

    def _handle_nullify_momentum(self, match, ctx):
        """Stop momentum"""
        target = ctx.get("target")
        if target:
            target.movement_remaining = 0
            if "log" in ctx: ctx["log"].append(f"{target.name}'s momentum Stopped!")

    def _handle_antigravity(self, match, ctx):
        """Anti-Gravity Field"""
        if "log" in ctx: ctx["log"].append("Anti-Gravity Field active! Everyone floats.")

    def _handle_flip_gravity(self, match, ctx):
        """Reverse Gravity"""
        if "log" in ctx: ctx["log"].append("Gravity Reversed! Falling up!")

    def _handle_implode(self, match, ctx):
        """Vacuum / Implosion"""
        target = ctx.get("target")
        if target:
            dmg = 20 # Massive
            target.hp -= dmg
            if "log" in ctx: ctx["log"].append(f"Implosion! {target.name} takes {dmg} force damage!")

    def _handle_meteor(self, match, ctx):
        """Orbital Strike"""
        ctx["damage_type"] = "Force"
        ctx["aoe_shape"] = "radius"
        ctx["aoe_size"] = 20
        if "log" in ctx: ctx["log"].append("METEOR STRIKE! 20ft Radius.")

    def _handle_black_hole(self, match, ctx):
        """Consume light and matter"""
        if "log" in ctx: ctx["log"].append("Black Hole created! Consuming area...")

    def _handle_erase(self, match, ctx):
        """Delete matter"""
        target = ctx.get("target")
        if target:
            target.hp = 0
            if "log" in ctx: ctx["log"].append(f"{target.name} Erased from existence!")

    def _handle_breach(self, match, ctx):
        """Destroy cover"""
        if "log" in ctx: ctx["log"].append("Cover/Walls Breached!")

    def _handle_brace(self, match, ctx):
        """Ignore Knockback"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.immune_prone = True
            target.immune_push = True
            if "log" in ctx: ctx["log"].append(f"{target.name} Braced.")

    def _handle_catch_projectile(self, match, ctx):
        """Stop projectile"""
        if "log" in ctx: ctx["log"].append("Projectile Caught/Stopped.")

    def _handle_repel_projectiles(self, match, ctx):
        """Deflect arrows"""
        ctx["deflect_missiles"] = True
        if "log" in ctx: ctx["log"].append("Repelling projectiles.")

    def _handle_dense_skin(self, match, ctx):
        """Reduce Physical Damage"""
        ctx["damage_reduction_phys"] = 5
        if "log" in ctx: ctx["log"].append("Dense Form: Physical DR 5.")

    def _handle_orbit_shield(self, match, ctx):
        """Debris Shield"""
        if "log" in ctx: ctx["log"].append("Orbiting Debris Shield active (+AC).")

    def _handle_event_horizon(self, match, ctx):
        """Absorb magic projectiles"""
        if "log" in ctx: ctx["log"].append("Event Horizon: Absorbing projectiles.")

    def _handle_invincible(self, match, ctx):
        """Infinite Mass"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.invulnerable = True
            target.movement = 0 # Infinite mass cannot move?
            if "log" in ctx: ctx["log"].append(f"{target.name} becomes Invincible (but Immobile)!")

    # ============================================
    # SCHOOL OF MOTUS HANDLERS (Motion/Speed)
    # ============================================

    def _handle_step(self, match, ctx):
        """5ft Shift"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            # Logic handled in movement engine mostly, but could set a flag
            if "log" in ctx: ctx["log"].append(f"{target.name} shifts 5ft (No OA).")

    def _handle_dash(self, match, ctx):
        """Bonus Move action"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.movement_remaining += target.speed
            if "log" in ctx: ctx["log"].append(f"{target.name} Dashes! (+{target.speed}ft move)")

    def _handle_teleport(self, match, ctx):
        """Teleportation"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            # Actual teleport requires coordinates, for now just log/flag
            if "log" in ctx: ctx["log"].append(f"{target.name} Teleports!")

    def _handle_haste(self, match, ctx):
        """Increase Speed"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            if hasattr(target, "apply_effect"):
                target.apply_effect("Haste", duration=3)
            if "log" in ctx: ctx["log"].append(f"{target.name} is Hasted! (Double Speed)")

    def _handle_portal(self, match, ctx):
        """Create Portal"""
        if "log" in ctx: ctx["log"].append("Portal opened.")

    def _handle_weave(self, match, ctx):
        """Move through enemies"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.can_move_through_enemies = True
            if "log" in ctx: ctx["log"].append(f"{target.name} Weaves through enemies.")
    
    # Alias for squeeze
    def _handle_squeeze(self, match, ctx):
        self._handle_weave(match, ctx)

    def _handle_snap_hit(self, match, ctx):
        """Quick low damage hit"""
        ctx["damage_bonus"] = -2 
        ctx["attack_roll"] += 2 # Easier to hit, less damage?
        if "log" in ctx: ctx["log"].append("Snap attack! (+Hit, -Dmg)")

    def _handle_barrage(self, match, ctx):
        """Multi-hit attack"""
        # Multi-hit logic usually handled by engine checking specific flag or resolving multiple times
        # Here we flag it
        ctx["multi_hit_count"] = 3
        if "log" in ctx: ctx["log"].append("Barrage! 3 strikes.")

    def _handle_spin_attack(self, match, ctx):
        """AOE around self"""
        ctx["aoe_shape"] = "radius"
        ctx["aoe_size"] = 5
        if "log" in ctx: ctx["log"].append("Spin Attack! Hitting adjacent enemies.")

    def _handle_blitz(self, match, ctx):
        """Line Charge"""
        ctx["is_charge"] = True
        ctx["aoe_shape"] = "line"
        ctx["aoe_size"] = 30 # 30ft line
        if "log" in ctx: ctx["log"].append("Blitz Charge!")

    def _handle_impact(self, match, ctx):
        """Damage scales with Speed"""
        attacker = ctx.get("attacker")
        if attacker:
            speed_dmg = attacker.speed // 5
            if "incoming_damage" in ctx:
                ctx["incoming_damage"] += speed_dmg
            if "log" in ctx: ctx["log"].append(f"Impact! +{speed_dmg} damage from Speed.")

    def _handle_infinite_attack(self, match, ctx):
        """Attack every target"""
        ctx["aoe_shape"] = "radius"
        ctx["aoe_size"] = 100 # Hit everything
        if "log" in ctx: ctx["log"].append("Infinite Strike! Hitting ALL targets.")

    def _handle_duck(self, match, ctx):
        """Reaction AC bonus"""
        if "log" in ctx: ctx["log"].append("Duck! AC Bonus.")

    def _handle_evasion(self, match, ctx):
        """Dodge AOE"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.has_evasion = True
            if "log" in ctx: ctx["log"].append(f"{target.name} gains Evasion.")

    def _handle_afterimage(self, match, ctx):
        """Decoy clones"""
        if "log" in ctx: ctx["log"].append("Afterimages created (Disadvantage to be hit).")

    def _handle_stutter(self, match, ctx):
        """Phase out"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.is_ethereal = True
            if "log" in ctx: ctx["log"].append(f"{target.name} Stutters out of reality.")

    def _handle_gone(self, match, ctx):
        """Non-existence"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.is_hidden = True
            target.invulnerable = True
            target.is_invisible = True
            if "log" in ctx: ctx["log"].append(f"{target.name} is Gone!")

    def _handle_loop(self, match, ctx):
        """Repeat last action"""
        if "log" in ctx: ctx["log"].append("Time Loop! Action repeated.")

    # _handle_aging already implemented in user edits

    def _handle_rewind(self, match, ctx):
        """Undo damage"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            # Complex to track exact recent damage, just heal significantly
            heal = 20
            target.hp = min(target.hp + heal, target.max_hp)
            if "log" in ctx: ctx["log"].append(f"Rewind! {target.name} heals {heal} HP.")

    def _handle_lag(self, match, ctx):
        """Delay enemy"""
        target = ctx.get("target")
        if target:
            target.initiative -= 5
            if "log" in ctx: ctx["log"].append(f"{target.name} Lagged! Initiative dropped.")

    def _handle_time_stop(self, match, ctx):
        """Time Stop"""
        if "log" in ctx: ctx["log"].append("TIME STOP! Extra turns taken.")

    def _handle_paradox(self, match, ctx):
        """Exist twice"""
        if "log" in ctx: ctx["log"].append("Paradox! You exist twice (Double Actions).")

    def _handle_reset_round(self, match, ctx):
        """Restart round"""
        if "log" in ctx: ctx["log"].append("Timeline Reset! Round restarts.")

    def _handle_timeline(self, match, ctx):
        """Predict future"""
        if "log" in ctx: ctx["log"].append("Timeline viewed. Future known.")

    # ============================================
    # SCHOOL OF VITA HANDLERS
    # ============================================

    def _handle_regeneration(self, match, ctx):
        """Heal HP every turn"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            if hasattr(target, "apply_effect"):
                target.apply_effect("Regeneration", duration=5) # Default 5 rounds
            if "log" in ctx: ctx["log"].append(f"{target.name} gains Regeneration!")

    def _handle_minor_heal(self, match, ctx):
        """Heal small amount"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            heal = random.randint(1, 8) + 2
            target.hp = min(target.hp + heal, target.max_hp)
            if "log" in ctx: ctx["log"].append(f"{target.name} heals {heal} HP (Minor)!")

    def _handle_full_heal(self, match, ctx):
        """Full HP recovery"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            healed = target.max_hp - target.hp
            target.hp = target.max_hp
            if "log" in ctx: ctx["log"].append(f"{target.name} fully healed ({healed} HP)!")

    def _handle_stop_bleed(self, match, ctx):
        """Cure bleeding"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.is_bleeding = False
            # Remove effect if present in active_effects
            if hasattr(target, "active_effects"):
                target.active_effects = [e for e in target.active_effects if "bleed" not in e.get("name", "").lower()]
            if "log" in ctx: ctx["log"].append(f"{target.name}'s bleeding stops.")

    def _handle_cure_disease(self, match, ctx):
        """Cure disease/immunity"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.is_diseased = False
            if hasattr(target, "active_effects"):
                target.active_effects = [e for e in target.active_effects if "disease" not in e.get("name", "").lower()]
            if "log" in ctx: ctx["log"].append(f"{target.name} cured of disease!")

    def _handle_cure_poison(self, match, ctx):
        """Cure poison"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.is_poisoned = False
            if hasattr(target, "active_effects"):
                target.active_effects = [e for e in target.active_effects if "poison" not in e.get("name", "").lower()]
            if "log" in ctx: ctx["log"].append(f"{target.name} cured of poison!")

    def _handle_lifesteal(self, match, ctx):
        """Heal for damage dealt"""
        dmg = ctx.get("incoming_damage", 0) 
        attacker = ctx.get("attacker")
        if attacker and dmg > 0:
            heal = dmg // 2
            attacker.hp = min(attacker.hp + heal, attacker.max_hp)
            if "log" in ctx: ctx["log"].append(f"{attacker.name} drains {heal} HP!")

    def _handle_life_bond(self, match, ctx):
        """Split damage with ally"""
        target = ctx.get("target")
        if target and "log" in ctx: ctx["log"].append(f"{target.name} is Life Bonded (Splits Damage)!")

    def _handle_auto_life(self, match, ctx):
        """Auto-revive on death"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.has_auto_life = True
            if "log" in ctx: ctx["log"].append(f"{target.name} gains Auto-Life!")

    def _handle_resurrect(self, match, ctx):
        """Bring back dead target"""
        target = ctx.get("target")
        if target and not target.is_alive():
            target.hp = target.max_hp // 2
            if "log" in ctx: ctx["log"].append(f"{target.name} Resurrected with {target.hp} HP!")
        elif target and "log" in ctx:
             ctx["log"].append(f"{target.name} is not dead!")

    def _handle_consume_ally(self, match, ctx):
        """Eat minion to heal"""
        target = ctx.get("target") # The minion
        attacker = ctx.get("attacker")
        if target and attacker:
            heal = target.hp
            target.hp = 0 # Kill minion
            attacker.hp = min(attacker.hp + heal, attacker.max_hp)
            if "log" in ctx: ctx["log"].append(f"{attacker.name} consumes {target.name} to heal {heal} HP!")

    def _handle_inflict_disease(self, match, ctx):
        """Inflict disease debuff"""
        target = ctx.get("target")
        if target:
            target.is_diseased = True
            if "log" in ctx: ctx["log"].append(f"{target.name} infected with Disease!")

    def _handle_necrotic(self, match, ctx):
        """Deal necrotic damage"""
        if "log" in ctx: ctx["log"].append("Damage type: Necrotic")
        ctx["damage_type"] = "Necrotic"

    def _handle_stat_drain(self, match, ctx):
        """Drain random stat"""
        target = ctx.get("target")
        if target:
            stats = ["Might", "Reflexes", "Endurance"]
            stat = random.choice(stats)
            if stat in target.stats:
                target.stats[stat] = max(0, target.stats[stat] - 2)
                if "log" in ctx: ctx["log"].append(f"{target.name}'s {stat} drained by 2!")

    def _handle_massive_dot(self, match, ctx):
        """Strong DoT (Rot)"""
        target = ctx.get("target")
        if target:
             if hasattr(target, "apply_effect"):
                 target.apply_effect("Rot", duration=3)
             target.is_rotting = True
             if "log" in ctx: ctx["log"].append(f"{target.name} is Rotting! (High DoT)")

    def _handle_contagion(self, match, ctx):
        """Spreading infection"""
        target = ctx.get("target")
        if target:
            target.is_contagious = True
            if "log" in ctx: ctx["log"].append(f"{target.name} is Contagious!")

    def _handle_creature_bane(self, match, ctx):
        """Bonus dmg vs creature type"""
        if "log" in ctx: ctx["log"].append("Bane active (Bonus vs Type)")

    def _handle_enlarge(self, match, ctx):
        """Grow in size"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.size_category = "Large"
            if "Might" in target.stats: target.stats["Might"] += 4
            if "log" in ctx: ctx["log"].append(f"{target.name} Enlarges! (+4 Might)")

    def _handle_grow_appendage(self, match, ctx):
        """Grow wings/claws etc"""
        target = ctx.get("target") or ctx.get("attacker")
        part = "Appendage"
        if match.group(0):
             if "Wings" in match.group(0): part = "Wings"
             elif "Claws" in match.group(0): part = "Claws"
             elif "Gills" in match.group(0): part = "Gills"
        if "log" in ctx: ctx["log"].append(f"{target.name} grows {part}!")

    def _handle_natural_armor(self, match, ctx):
        """Increase base AC/Natural armor"""
        if "log" in ctx: ctx["log"].append("Natural Armor increased")

    def _handle_swarm_form(self, match, ctx):
        """Turn into bugs"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.is_swarm = True
            if "log" in ctx: ctx["log"].append(f"{target.name} transforms into a Swarm!")

    def _handle_clone(self, match, ctx):
        """Grow spare body"""
        if "log" in ctx: ctx["log"].append("Spare body grown (Clone defined)")

    def _handle_animate_plant(self, match, ctx):
        """Animate plant ally"""
        engine = ctx.get("engine")
        attacker = ctx.get("attacker")
        if engine and attacker:
             minion = engine.spawn_minion("Animated Plant", attacker.x + 1, attacker.y)
             if "log" in ctx: ctx["log"].append("Plant Animated (Minion Spawned).")

    def _handle_create_life(self, match, ctx):
        """Create lifeform"""
        engine = ctx.get("engine")
        attacker = ctx.get("attacker")
        if engine and attacker:
             minion = engine.spawn_minion("Homunculus", attacker.x - 1, attacker.y)
             if "log" in ctx: ctx["log"].append(f"Lifeform Created: {minion.name}")

    def _handle_detect_life(self, match, ctx):
        """Detect Life Radar"""
        if "log" in ctx: ctx["log"].append("Pulse: Life Detected in area")

    def _handle_vines(self, match, ctx):
        """Entangle with vines"""
        target = ctx.get("target")
        if target:
            target.is_restrained = True
            if "log" in ctx: ctx["log"].append(f"{target.name} Entangled by Vines!")

    # ============================================
    # SCHOOL OF LUX HANDLERS
    # ============================================

    def _handle_laser(self, match, ctx):
        """Laser damage (Radiant)"""
        if "log" in ctx: ctx["log"].append("Laser Beam! (Radiant Damage)")
        ctx["damage_type"] = "Radiant"

    def _handle_nova(self, match, ctx):
        """Massive Light Damage"""
        if "log" in ctx: ctx["log"].append("NOVA ATTACK! Massive Radiant Damage!")
        ctx["damage_type"] = "Radiant"
        ctx["is_crit"] = True # Nova usually crits or hits hard

    def _handle_split_beam(self, match, ctx):
        """Split beam to hit multiple targets"""
        if "log" in ctx: ctx["log"].append("Beam Splits! Hitting multiple targets.")

    def _handle_burn_undead(self, match, ctx):
        """Bonus damage vs Undead"""
        target = ctx.get("target")
        if target and hasattr(target, "species") and "Undead" in target.species:
            if "incoming_damage" in ctx:
                ctx["incoming_damage"] *= 2
            if "log" in ctx: ctx["log"].append("Holy Light burns the Undead! (Double Damage)")

    def _handle_light_explosion(self, match, ctx):
        """Flashbang effect"""
        target = ctx.get("target")
        if target:
            target.is_blinded = True
            if "log" in ctx: ctx["log"].append("Flashbang! Target Blinded.")

    def _handle_heat_metal(self, match, ctx):
        """Heat Metal"""
        target = ctx.get("target")
        if target:
            if "log" in ctx: ctx["log"].append(f"{target.name}'s armor is searing hot! (Fire Damage)")

    def _handle_see_invis(self, match, ctx):
        """See Invisibility"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.can_see_invisible = True
            if "log" in ctx: ctx["log"].append(f"{target.name} gains True Seeing!")

    def _handle_xray(self, match, ctx):
        """See Through Walls"""
        if "log" in ctx: ctx["log"].append("X-Ray Vision active!")

    def _handle_darkvision(self, match, ctx):
        """Darkvision"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.has_darkvision = True
            if "log" in ctx: ctx["log"].append(f"{target.name} gains Darkvision.")

    def _handle_gps(self, match, ctx):
        """Know Location"""
        if "log" in ctx: ctx["log"].append("Location Pinpointed (GPS).")

    def _handle_postcognition(self, match, ctx):
        """See the past"""
        if "log" in ctx: ctx["log"].append("Vision within the past revealed...")

    def _handle_scry(self, match, ctx):
        """Remote Viewing"""
        if "log" in ctx: ctx["log"].append("Scrying sensor active.")

    def _handle_bonus_perception(self, match, ctx):
        """Bonus to Perception"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            if "log" in ctx: ctx["log"].append(f"{target.name} gains Enhanced Vision (+Perception).")

    def _handle_blindness(self, match, ctx):
        """Inflict Blindness"""
        target = ctx.get("target")
        if target:
            target.is_blinded = True
            if hasattr(target, "apply_effect"):
                target.apply_effect("Blindness", duration=1)
            if "log" in ctx: ctx["log"].append(f"{target.name} is Blinded!")

    def _handle_perm_blind(self, match, ctx):
        """Permanent Blindness"""
        target = ctx.get("target")
        if target:
            target.is_blinded = True
            if "log" in ctx: ctx["log"].append(f"{target.name} is Permanently Blinded!")

    def _handle_dazzle(self, match, ctx):
        """Dazzle (-1 to hit)"""
        target = ctx.get("target")
        if target:
            if "log" in ctx: ctx["log"].append(f"{target.name} is Dazzled! (-1 to Hit)")

    def _handle_block_sight(self, match, ctx):
        """Block Sight Line"""
        if "log" in ctx: ctx["log"].append("Sight line blocked (Smoke/Darkness).")

    def _handle_invisibility(self, match, ctx):
        """Turn Invisible"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.is_invisible = True
            target.is_hidden = True
            if hasattr(target, "apply_effect"):
                target.apply_effect("Invisibility", duration=3)
            if "log" in ctx: ctx["log"].append(f"{target.name} turns Invisible!")

    def _handle_disguise(self, match, ctx):
        """Alter Self"""
        if "log" in ctx: ctx["log"].append("Appearance altered (Disguise).")

    def _handle_camo(self, match, ctx):
        """Camouflage"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            if "log" in ctx: ctx["log"].append(f"{target.name} blends with surroundings (Camo).")

    def _handle_illusion(self, match, ctx):
        """Create Illusion/Hologram"""
        if "log" in ctx: ctx["log"].append("Illusion created.")

    def _handle_major_image(self, match, ctx):
        """Major Image / Fake Terrain"""
        if "log" in ctx: ctx["log"].append("Major Illusion generated (Fake Terrain).")

    def _handle_hidden_reality(self, match, ctx):
        """Hidden from Reality (Dimensional stealth)"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.is_invisible = True
            target.is_ethereal = True
            if "log" in ctx: ctx["log"].append(f"{target.name} is Hidden from Reality!")

    # ============================================
    # SPECIES SKILL HANDLERS
    # ============================================

    def _handle_gore_charge(self, match, ctx):
        """Charge attack bonus (+1d6 damage, etc)"""
        if "log" in ctx: ctx["log"].append("Charge: +1d6 Damage if moved 20ft.")
        if "damage_bonus" in ctx: ctx["damage_bonus"] = ctx.get("damage_bonus", 0) + random.randint(1, 6)

    def _handle_lunge_reach(self, match, ctx):
        """Increase melee reach"""
        attacker = ctx.get("attacker")
        if attacker:
            # Mechanically handled in attack_target check if pattern matches
            if "log" in ctx: ctx["log"].append("Lunge: Reach increased!")

    def _handle_venom_injection(self, match, ctx):
        """Inject poison on hit"""
        target = ctx.get("target")
        if target:
            if hasattr(target, "apply_effect"):
                target.apply_effect("Poisoned", duration=3)
            else:
                target.is_poisoned = True
            # Deal initial poison damage?
            dmg = random.randint(1, 6)
            target.hp -= dmg
            if "log" in ctx: ctx["log"].append(f"Venom injected! {target.name} takes {dmg} Poison damage + Poisoned status.")

    def _handle_trample(self, match, ctx):
        """Knockdown + Damage"""
        target = ctx.get("target")
        if target:
            target.is_prone = True
            dmg = random.randint(1, 6) + 2
            target.hp -= dmg
            if "log" in ctx: ctx["log"].append(f"Trampled! {target.name} takes {dmg} dmg and falls Prone.")

    def _handle_wall_walk(self, match, ctx):
        """Climb walls"""
        user = ctx.get("attacker")
        if user:
            user.has_climb_speed = True
            if "log" in ctx: ctx["log"].append("Wall Walker active.")

    def _handle_tremorsense(self, match, ctx):
        """Detect vibration"""
        user = ctx.get("attacker")
        if user:
            user.has_tremorsense = True
            if "log" in ctx: ctx["log"].append("Tremorsense active.")

    def _handle_grapple_bonus(self, match, ctx):
        """Advantage on grapple"""
        if "log" in ctx: ctx["log"].append("Grapple Advantage active.")

    def _handle_cone_attack(self, match, ctx):
        """Generic Cone Attack"""
        # Parse range from match if possible, else default 15
        range_ft = 15
        if match.group(0) and "10" in match.group(0): range_ft = 10
        if "log" in ctx: ctx["log"].append(f"Cone Attack ({range_ft}ft)! Dex save for half.")

    def _handle_bleed_dot(self, match, ctx):
        """Apply Bleed DoT"""
        target = ctx.get("target")
        if target:
             if hasattr(target, "apply_effect"):
                 target.apply_effect("Bleeding", duration=3)
             target.is_bleeding = True
             if "log" in ctx: ctx["log"].append(f"{target.name} is Bleeding!")

    def _handle_ignore_cover(self, match, ctx):
        """Ignore cover penalties"""
        if "log" in ctx: ctx["log"].append("Attacker ignores cover.")

    def _handle_auto_grapple(self, match, ctx):
        """Grapple on hit"""
        target = ctx.get("target")
        if target:
            target.is_grappled = True
            if "log" in ctx: ctx["log"].append(f"{target.name} is Grappled!")

    def _handle_burrow_speed(self, match, ctx):
        """Burrow speed"""
        user = ctx.get("attacker") or ctx.get("target")
        if user:
            user.has_burrow_speed = True
            if "log" in ctx: ctx["log"].append("Gained Burrow Speed!")

    def _handle_squeeze(self, match, ctx):
        """Squeeze through tight spaces"""
        if "log" in ctx: ctx["log"].append("Can squeeze through small spaces.")

    def _handle_biosense(self, match, ctx):
        """Detect Life/Heartbeat"""
        if "log" in ctx: ctx["log"].append("Bio-Sense active: Detecting heartbeats.")

    def _handle_thermal_sight(self, match, ctx):
        """Thermal Vision"""
        if "log" in ctx: ctx["log"].append("Thermal Sight active: Detecting heat signatures.")

    def _handle_omnivision(self, match, ctx):
        """Cannot be Flanked"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.cannot_be_flanked = True
            if "log" in ctx: ctx["log"].append("Omni-Vision: Cannot be Flanked.")

    def _handle_enhanced_hearing(self, match, ctx):
        """Eavesdrop"""
        if "log" in ctx: ctx["log"].append("Enhanced Hearing active.")

    def _handle_immovable(self, match, ctx):
        """Cannot be moved/shoved"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.is_immovable = True
            if "log" in ctx: ctx["log"].append("Anchored: Cannot be moved.")

    def _handle_slippery(self, match, ctx):
        """Advantage to escape grapple"""
        if "log" in ctx: ctx["log"].append("Slippery: Advantage to escape Grapple.")

    def _handle_withdraw(self, match, ctx):
        """ Withdraw into shell (+AC) """
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            if hasattr(target, "apply_effect"):
                target.apply_effect("Withdraw", duration=1) # High AC buff
            if "log" in ctx: ctx["log"].append("Withdrawn into Shell (+AC).")

    def _handle_web_shot(self, match, ctx):
        """Fire Web (Restrain)"""
        target = ctx.get("target")
        if target:
            target.is_restrained = True
            if "log" in ctx: ctx["log"].append(f"{target.name} is Restrained by Web!")

    def _handle_spore_cloud(self, match, ctx):
        """Poison Spore Cloud (10ft Radius)"""
        engine = ctx.get("engine")
        attacker = ctx.get("attacker")
        if engine and attacker:
            for t in engine.combatants:
                if t != attacker and t.is_alive():
                    # Check distance (Radius 2 aka 10ft)
                    if max(abs(t.x - attacker.x), abs(t.y - attacker.y)) <= 2:
                        t.is_poisoned = True
                        if hasattr(t, "apply_effect"): t.apply_effect("Poisoned", 3)
                        if "log" in ctx: ctx["log"].append(f"{t.name} poisoned by Spore Cloud!")

    def _handle_tail_sweep(self, match, ctx):
        """AOE Prone (Adjacent)"""
        engine = ctx.get("engine")
        attacker = ctx.get("attacker")
        if engine and attacker:
            for t in engine.combatants:
                 if t != attacker and t.is_alive():
                     if max(abs(t.x - attacker.x), abs(t.y - attacker.y)) <= 1:
                         t.is_prone = True
                         if "log" in ctx: ctx["log"].append(f"{t.name} knocked Prone by Tail Sweep!")

    def _handle_gust(self, match, ctx):
        """Wind Gust (Push 10ft Line)"""
        engine = ctx.get("engine")
        attacker = ctx.get("attacker")
        target = ctx.get("target")
        if target:
            # Push target away 2 squares
            dx = target.x - attacker.x
            dy = target.y - attacker.y
            # Normalize rough direction
            step_x = 1 if dx > 0 else -1 if dx < 0 else 0
            step_y = 1 if dy > 0 else -1 if dy < 0 else 0
            
            new_x = target.x + (step_x * 2)
            new_y = target.y + (step_y * 2)
            
            if engine:
                 success, msg = engine.move_char(target, new_x, new_y)
                 if "log" in ctx: ctx["log"].append(f"{target.name} blown back by Gust! ({msg})")
            else:
                 target.x, target.y = new_x, new_y # Fallback

    def _handle_solar_beam(self, match, ctx):
        """Solar Beam (Blind + Dmg)"""
        target = ctx.get("target")
        if target:
            target.is_blinded = True
            ctx["damage_type"] = "Radiant"
            if "log" in ctx: ctx["log"].append(f"Solar Beam! {target.name} is Blinded.")

    def _handle_lockjaw(self, match, ctx):
        """Grapple harder"""
        target = ctx.get("target")
        if target:
            target.is_grappled = True
            target.is_restrained = True # Lockjaw implies harder to escape than just grapple
            if "log" in ctx: ctx["log"].append(f"Lockjaw! {target.name} is Grappled & Restrained.")

    def _handle_goodberry(self, match, ctx):
        """Create Goodberry"""
        if "log" in ctx: ctx["log"].append("Goodberry created (Heals HP).")

    def _handle_mimicry(self, match, ctx):
        """Mimic sound"""
        if "log" in ctx: ctx["log"].append("Voice/Sound mimicked perfectly.")

    def _handle_water_breathing(self, match, ctx):
        """Breathe Underwater"""
        target = ctx.get("target") or ctx.get("attacker")
        if target:
            target.can_breathe_water = True
            if "log" in ctx: ctx["log"].append("Water Breathing active.")

    # --- TALENT HANDLERS ---
    def _handle_damage_vs_armor(self, match, ctx):
        """damage_bonus_vs_armor(N)"""
        bonus = int(match.group(1))
        target = ctx.get("target")
        # Heuristic: Check if target has Armor item equipped
        has_armor = False
        if target and getattr(target, "inventory", None) and target.inventory.equipped.get("Armor"):
            has_armor = True
            
        if has_armor:
            ctx["damage_bonus"] = ctx.get("damage_bonus", 0) + bonus
            if "log" in ctx: ctx["log"].append(f"Talent Bonus vs Armor: +{bonus} Damage")

    def _handle_knockback_talent(self, match, ctx):
        """Generic knockback on hit"""
        attacker = ctx.get("attacker")
        target = ctx.get("target")
        engine = ctx.get("engine")
        if attacker and target and engine:
            # Push 1 tile away
            dx = target.x - attacker.x
            dy = target.y - attacker.y
            if dx == 0 and dy == 0: return 
            
            if abs(dx) > abs(dy): dx = 1 if dx > 0 else -1; dy = 0
            else: dy = 1 if dy > 0 else -1; dx = 0
            
            nx, ny = target.x + dx, target.y + dy
            # Forced movement: bypass move_char, just check bounds and collisions
            if 0 <= nx < engine.cols and 0 <= ny < engine.rows:
                blocked = False
                for c in engine.combatants:
                    if c.is_alive() and c != target and c.x == nx and c.y == ny:
                        blocked = True
                        break
                if not blocked and (nx, ny) not in engine.walls:
                    target.x = nx
                    target.y = ny
                    if "log" in ctx: ctx["log"].append(f"{target.name} is knocked back!")

    def _handle_pierce_talent(self, match, ctx):
        """projectile_pierce(N)"""
        bonus = int(match.group(1))
        ctx["damage_bonus"] = ctx.get("damage_bonus", 0) + bonus

    def _handle_sunder_talent(self, match, ctx):
        if "log" in ctx: ctx["log"].append("Sunder applied! (Vulnerable)")

# Singleton instance for easy access
registry = EffectRegistry()

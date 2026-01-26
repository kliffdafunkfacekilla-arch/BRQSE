from typing import Dict, Any, Tuple, List
import random
import math
import math
import traceback
import json
import os
from brqse_engine.combat.mechanics import CombatEngine, Combatant
from brqse_engine.world.map_generator import MapGenerator, TILE_WALL, TILE_FLOOR, TILE_LOOT, TILE_ENEMY, TILE_HAZARD, TILE_DOOR
from scripts.world_engine import SceneStack, ChaosManager, Scene
from brqse_engine.abilities import engine_hooks
from brqse_engine.abilities.effects_registry import registry
from brqse_engine.core.event_engine import EventEngine
from brqse_engine.models.journal import Journal

class GameLoopController:
    """
    Manages the active game session:
    - Exploration Mode (Move, Search, Interact)
    - Combat Mode (Turn-based)
    - Scene Transitions
    """
    
    def __init__(self, chaos_manager: ChaosManager, game_state: Any = None, sensory_layer: Any = None):
        self.chaos = chaos_manager
        self.game_state = game_state
        self.sensory_layer = sensory_layer
        self.scene_stack = SceneStack(self.chaos)
        self.map_gen = MapGenerator(self.chaos)
        self.combat_engine = CombatEngine(20, 20)
        
        self.state = "EXPLORE"
        self.player_pos = (1, 10)
        self.player_combatant = None
        self.load_player()
        self.active_scene = None
        self.interactables = {}
        self.explored_tiles = set()
        self.explored_tiles = set()
        self.current_event = "SCENE_STARTED"
        self.dice_log = []
        
        # v2 Event System initialization
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../Data")
        self.event_engine = EventEngine(data_dir)
        self.journal = Journal()
        self.active_scenario = None
        self.is_event_resolved = True # Start resolved for the very first room
        self.inventory = [] # Player Inventory for Keys/Items
        
        # Initial Quest Gen
        self.scene_stack.generate_quest()
        self.advance_scene()

    def advance_scene(self) -> Scene:
        """Moves to next scene, resets visibility."""
        if not self.is_event_resolved:
            # We can't really return a Scene here, but we can prevent the update.
            # In handle_action, we already block the call to this.
            return self.active_scene

        scene = self.scene_stack.advance()
        if scene.text == "QUEST COMPLETE":
            self.active_scene = scene
            self.current_event = "QUEST_COMPLETE"
            return scene

        scene = self.map_gen.generate_map(scene)
        self.active_scene = scene
        self.combat_engine = CombatEngine(20, 20)
        
        # Setup interactables and walls
        self.interactables = {(node["x"], node["y"]): node for node in scene.interactables}
        for y, row in enumerate(scene.grid):
            for x, tile in enumerate(row):
                if tile == TILE_WALL: self.combat_engine.create_wall(x, y)
        
        self.explored_tiles = set()
        
        if scene.entrances: 
            self.player_pos = scene.entrances[0]
            if self._is_blocked(*self.player_pos):
                self.player_pos = self._find_safe_spawn(scene)
        
        self._update_visibility()
        
        if self.player_combatant:
            self.player_combatant.elevation = 0
            self.player_combatant.is_behind_cover = False
            self.player_combatant.facing = "N"
        else:
            self.load_player()
            
        # Trigger Entry Event
        self._trigger_scene_entry_event()
        
        self.state = "EXPLORE"
        self.current_event = "SCENE_STARTED"
        return scene

    def _trigger_scene_entry_event(self):
        """Triggers the primary encounter for a room upon entry."""
        self.trigger_event(is_entry=True)

    def trigger_event(self, is_entry: bool = False, force_type: str = None):
        """Unified event trigger for Entry and Tension events."""
        # Reset resolution flag if a significant new event occurs
        # or if we are entering a room.
        # v2: Generate Narrative/Mechanic Scenario via EventEngine
        scenario = self.event_engine.generate_scenario(self.active_scene.biome, sensory_layer=self.sensory_layer)
        self.active_scenario = scenario
        
        # Decide if this event locks the doors
        win_type = scenario["win_condition"]["type"]
        is_challenge = win_type in ["ENEMIES_KILLED", "PUZZLE_SOLVED", "TALKED_TO_NPC"]
        
        if is_entry:
            self.is_event_resolved = not is_challenge
        elif is_challenge:
            # If a challenge spawns dynamically (Tension), lock down
            self.is_event_resolved = False
        
        # If we handle force_type (like HAZARD for Chaos), we should let EventEngine know
        # but for now we'll stick to the 5xD20 logic
        
        self.active_scenario = scenario
        self.journal.log_event(
            scenario["archetype"], scenario["subject"], scenario["context"],
            scenario["reward"], scenario["chaos_twist"], scenario["narrative"],
            goal=scenario.get("goal_description", "Survive.")
        )
        
        # Manifest scenario entities
        res = {"log": scenario["narrative"]}
        if "goal_description" in scenario:
            res["log"] += f" GOAL: {scenario['goal_description']}"
            
        for item in scenario["setup"]:
            self._manifest_v2_entity(item, scenario, res)
        
        # If the new event is significant, re-block the exit
        if scenario["win_condition"]["type"] in ["ENEMIES_KILLED", "PUZZLE_SOLVED"]:
            self.is_event_resolved = False
        
        # Update the result log if this was called from handle_action
        return res

    def _manifest_v2_entity(self, setup_item: Dict, scenario: Dict, result: Dict):
        """Helper to place entities defined by the EventEngine."""
        etype = setup_item["type"]
        px, py = self.player_pos
        
        # Find spot
        spots = []
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                nx, ny = px + dx, py + dy
                if 0 <= nx < 20 and 0 <= ny < 20:
                    if self.active_scene.grid[ny][nx] == TILE_FLOOR and (nx, ny) not in self.interactables and abs(dx)+abs(dy) > 2:
                        spots.append((nx, ny))
        
        if not spots:
            # Fallback 1: Try adjacent/closer tiles (dist > 0)
            for dy in range(-4, 5):
                for dx in range(-4, 5):
                    nx, ny = px + dx, py + dy
                    if 0 <= nx < 20 and 0 <= ny < 20:
                        if self.active_scene.grid[ny][nx] == TILE_FLOOR and (nx, ny) not in self.interactables and (nx,ny) != (px,py):
                            spots.append((nx, ny))
                            
        if not spots:
            # Fallback 2: Scan ENTIRE grid for any open floor
            for r in range(20):
                for c in range(20):
                    if self.active_scene.grid[r][c] == TILE_FLOOR and (c, r) not in self.interactables and (c,r) != (px,py):
                        spots.append((c, r))
                        
        if not spots:
            # Critical Failsafe: No room to spawn.
            # We MUST auto-resolve if this was a blocking event, otherwise the game softlocks.
            if scenario.get("win_condition", {}).get("type") in ["ENEMIES_KILLED", "PUZZLE_SOLVED", "TALKED_TO_NPC"]:
                self.is_event_resolved = True
                result["log"] += " (The conceptual weight of the event collapses. The path opens.)"
            return

        sx, sy = random.choice(spots)

        if etype == "ENEMY_SPAWN":
            from brqse_engine.combat.enemy_spawner import spawner
            
            path = spawner.spawn_beast(biome=getattr(self.active_scene, 'biome', 'DUNGEON'), level=1)
            with open(path, 'r') as f: enemy_data = json.load(f)
            enemy = Combatant(data=enemy_data)
            enemy.team = "Enemies"
            # Propagate Key Data to Enemy
            if setup_item.get("has_key"):
                enemy.has_key = setup_item["has_key"]
                enemy.key_name = setup_item["key_name"]
            
            self.active_scene.grid[sy][sx] = TILE_ENEMY
            self.combat_engine.add_combatant(enemy, sx, sy)
            self.state = "COMBAT"
            result["event"] = "COMBAT_STARTED"

        elif etype == "NPC_SPAWN":
            self.interactables[(sx, sy)] = {
                "type": setup_item.get("subtype", "Stranger"), "x": sx, "y": sy,
                "tags": ["talk", "inspect"], "is_blocking": True,
                "dialogue_context": setup_item.get("dialogue_context")
            }
            # Don't change tile to LOOT, keep as existing (likely FLOOR) to avoid rendering a chest under them
            # self.active_scene.grid[sy][sx] = TILE_LOOT

        elif etype == "OBJECT_SPAWN":
            self.interactables[(sx, sy)] = {
                "type": setup_item.get("subtype", "Object"), "x": sx, "y": sy,
                "tags": setup_item.get("tags", ["inspect"]),
                "is_blocking": setup_item.get("is_blocking", True),
                "is_locked": setup_item.get("is_locked", False),
                "has_key": setup_item.get("has_key"),
                "key_name": setup_item.get("key_name"),
                "required_key": setup_item.get("required_key")
            }
            self.active_scene.grid[sy][sx] = TILE_LOOT

    def load_player(self):
        """Loads or reloads the player character from GameState."""
        if not self.game_state: return
        
        player_data = self.game_state.get_player()
        if player_data:
            self.player_combatant = Combatant(data=player_data)
            self.player_combatant.team = "Player"

    def handle_staged_battle(self):
        """Checks for a staged battle config and loads it."""
        if not self.game_state: return
        path = self.game_state.get_staged_config_path()
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    config = json.load(f)
                # Process config (Blue team vs Red team)
                # For now, we'll just set up the current scene to use this
                self.state = "COMBAT"
                # ... (Additional logic would go here to transition to battle view)
            except Exception as e:
                 print(f"Error loading staged battle: {e}")

    def handle_action(self, action_type: str, x: int, y: int) -> Dict[str, Any]:
        """Generic handler for player intent."""
        if self.state == "COMBAT":
            return self._handle_combat_action(action_type, x, y)
        if self.state != "EXPLORE": return {"success": False, "reason": "Locked"}

        # Update Facing for all actions (only if coords provided)
        if x is not None and y is not None:
            px, py = self.player_pos
            if x > px: self._set_facing("E")
            elif x < px: self._set_facing("W")
            elif y > py: self._set_facing("S")
            elif y < py: self._set_facing("N")

        result = {"success": True, "action": action_type}
        obj = self.interactables.get((x, y))
        
        if action_type == "move":
            move_res = self._process_move(x, y)
            if not move_res["success"]: return move_res
            result.update(move_res)
            if "log" not in result:
                result["log"] = f"Moved to {x}, {y}."
        
        elif action_type == "inspect":
            if obj:
                if "talk" in obj.get("tags", []):
                    result["log"] = f"You see {obj['type']}."
                else:
                    result["log"] = f"A sturdy {obj['type']}."
            else:
                # Check for combatant at x,y
                entity = None
                if self.combat_engine and self.combat_engine.combatants:
                    for c in self.combat_engine.combatants:
                        if c.x == x and c.y == y:
                            entity = c
                            break
                            
                if entity:
                    result["log"] = f"You see {entity.name} ({entity.species})."
                    if entity.team == "Enemies":
                        result["log"] += " It looks hostile."
                else:
                    result["log"] = "An ordinary patch of ground."

        elif action_type == "search" or action_type == "perception":
            if obj:
                tags = obj.get("tags", [])
                if "search" in tags or "open" in tags:
                    log = f"You search the {obj['type']}."
                    if obj.get("is_locked"):
                         log += " It is locked."
                         if "required_key" in obj:
                             has_key = any(k["id"] == obj["required_key"] for k in self.inventory)
                             if has_key:
                                 log += " You use the key to unlock it!"
                                 obj["is_locked"] = False
                             else:
                                 result["log"] = log + " You need a specific key."
                                 return result

                    if obj.get("has_key"):
                        item = {"id": obj["has_key"], "name": obj["key_name"]}
                        self.inventory.append(item)
                        log += f" You found: {item['name']}!"
                    else:
                        log += " You found some supplies."

                    result["log"] = log
                    # Potential for actual item drop logic here
                    del self.interactables[x, y]
                    self.active_scene.grid[y][x] = TILE_FLOOR
                elif "disarm" in tags:
                    result["log"] = f"You search the area and find a hidden {obj['type']}! Use 'disarm' to neutralize it."
                    obj["is_hidden"] = False
                else:
                    result["log"] = f"You search the {obj['type']} but find nothing unusual."
            else:
                result["log"] = "You scour the area with keen eyes."
            self._update_visibility(radius=7) # Temporary vision boost
            
        elif action_type == "disarm":
            if obj and "disarm" in obj.get("tags", []):
                result["log"] = f"You carefully disarm the {obj['type']}."
                del self.interactables[x, y]
                self.active_scene.grid[y][x] = TILE_FLOOR
            else: result = {"success": False, "reason": "Nothing to disarm"}

        elif action_type == "track":
            # Tracking / Forensics Logic
            if not self.chaos:
                result = {"success": False, "reason": "No Chaos Manager"}
            else:
                # 1. Determine Difficulty
                difficulty = 10 + self.chaos.chaos_level
                
                # 2. Roll (Simulated Survival/Perception)
                # TODO: Check for actual player skills if available
                roll = random.randint(1, 20)
                bonus = 0
                if self.player_combatant:
                    # quick check for skill keywords in powers/skills
                    skills = [s.lower() for s in self.player_combatant.character.skills]
                    if "survival" in skills: bonus += 3
                    elif "perception" in skills: bonus += 2
                
                total = roll + bonus
                
                result["log"] = f"Tracking (DC {difficulty})... Rolled {total} ({roll}+{bonus})."
                
                if total >= difficulty:
                    result["success"] = True
                    # If there's a specific object being tracked
                    if obj and "track" in obj.get("tags", []):
                        result["log"] += f" SUCCESS: You find distinct signs leading away from the {obj['type']}."
                    else:
                        # Generic Scene Tracking
                        biomes = getattr(self.active_scene, 'biome', 'DUNGEON')
                        result["log"] += " SUCCESS: You discern a path through the debris/foliage."
                        
                    if self.active_scenario:
                         # Check context - if it's a forensic encounter, this MUST progress it.
                         narrative = str(self.active_scenario.get("narrative", "")).lower()
                         win_type = self.active_scenario["win_condition"].get("type", "")
                         
                         if "track" in narrative or "clues" in narrative or "footprints" in narrative:
                             self._resolve_active_event("Tracked Successfully")
                             result["log"] += " You found the target!"
                         elif win_type == "FIND_CLUES": # explicit new type
                             self._resolve_active_event("Evidence Recovered")
                             result["log"] += " You uncovered the truth!"
                         elif win_type == "PUZZLE_SOLVED": # fallback
                             self._resolve_active_event("Mystery Solved via Tracking")
                
                else:
                    result["success"] = False
                    result["log"] += " FAILURE: The signs are too faint or corrupted to follow."
                    # Tension penalty for wasting time?
                    self.chaos.chaos_clock += 1
                    result["log"] += " FAILURE: The signs are too faint or corrupted to follow."
                    # Tension penalty for wasting time?
                    self.chaos.chaos_clock += 1

        elif action_type == "solve":
            if obj and "solve" in obj.get("tags", []):
                result["log"] = f"You concentrate and solve the {obj['type']}! A mechanism clicks."
                if self.active_scenario and self.active_scenario["win_condition"]["type"] == "PUZZLE_SOLVED":
                    self._resolve_active_event("Solved")
                del self.interactables[x, y]
                self.active_scene.grid[y][x] = TILE_FLOOR
            else: result = {"success": False, "reason": "Nothing to solve"}

        elif action_type == "smash":
            if obj and "smash" in obj.get("tags", []):
                result["log"] = f"Smashed {obj['type']}!"
                self.active_scene.grid[y][x] = TILE_FLOOR
                del self.interactables[x,y]
            else: result = {"success": False, "reason": "Fail"}
            
        elif action_type == "push":
            if obj and "push" in obj.get("tags", []):
                dx, dy = x - px, y - py
                tx, ty = x + dx, y + dy
                # Check landing spot
                if 0 <= tx < 20 and 0 <= ty < 20 and self.active_scene.grid[ty][tx] == TILE_FLOOR and (tx, ty) not in self.interactables:
                    # Move the object
                    self.interactables[tx, ty] = obj
                    del self.interactables[x, y]
                    obj["x"], obj["y"] = tx, ty
                    # Update grid representation
                    self.active_scene.grid[y][x] = TILE_FLOOR
                    self.active_scene.grid[ty][tx] = TILE_LOOT
                    result["log"] = f"Pushed the {obj['type']} forward."
                else:
                    result = {"success": False, "reason": "Blocked"}
            else: result = {"success": False, "reason": "Cannot push this"}

        elif action_type == "vault":
            if obj and "vault" in obj.get("tags", []):
                dx, dy = x - px, y - py
                tx, ty = x + dx, y + dy
                # Check landing spot past the object
                if 0 <= tx < 20 and 0 <= ty < 20 and self.active_scene.grid[ty][tx] == TILE_FLOOR and (tx, ty) not in self.interactables:
                    self.player_pos = (tx, ty)
                    if self.player_combatant: self.player_combatant.elevation = 0
                    result["log"] = f"Vaulted over the {obj['type']}!"
                    self._update_visibility()
                else:
                    result = {"success": False, "reason": "No landing space"}
            else: result = {"success": False, "reason": "Cannot vault this"}

        elif action_type in ["climb", "pull", "flip", "open"]:
            if obj and action_type in obj.get("tags", []):
                result["log"] = f"{action_type.capitalize()}ed the {obj['type']}."
                if action_type == "climb" and "elevation" in obj.get("tags", []):
                    self.player_pos = (x, y)
                    if self.player_combatant: self.player_combatant.elevation = 1
                    self._update_visibility()
                
                elif action_type == "unlock":
                    if obj.get("required_key"):
                         has_key = any(k["id"] == obj["required_key"] for k in self.inventory)
                         if has_key:
                             result["log"] = f"You unlock the {obj['type']}."
                             obj["is_locked"] = False
                             if obj.get("is_blocking"): obj["is_blocking"] = False
                         else:
                             result["log"] = "It won't budge. You need a key."
                    elif obj["type"] == "Cage":
                        result["log"] = "You free a traveler! They reward you with a scrap of map."
                        del self.interactables[x,y]
                        self.active_scene.grid[y][x] = TILE_FLOOR

                        self.active_scene.grid[y][x] = TILE_FLOOR

        elif action_type == "use":
            # Map generic use to contextual actions
            if not obj:
                 result = {"success": False, "reason": "Nothing to use"}
            else:
                tags = obj.get("tags", [])
                if "solve" in tags:
                    return self.handle_action("solve", x, y)
                elif "open" in tags:
                     return self.handle_action("open", x, y)
                elif "unlock" in tags:
                     return self.handle_action("unlock", x, y)
                elif "talk" in tags:
                     return self.handle_action("talk", x, y)
                else:
                     result = {"success": False, "reason": "Can't use this."}

        elif action_type == "talk":
            if obj and "talk" in obj.get("tags", []):
                if self.sensory_layer:
                    # AI Dialogue Generation
                    ai_context = {
                        "actor_name": "Player",
                        "target_name": obj['type'],
                        "method": "Diplomacy",
                        "defense": "Unknown",
                        "result": "Success"
                    }
                    context_data = self.chaos.get_atmosphere()
                    context_data["inventory"] = [i["name"] for i in self.inventory]
                    
                    narrative = self.sensory_layer.generate_narrative(
                        context=context_data, 
                        event_type="SOCIAL", 
                        combat_data=ai_context,
                        quest_context=obj.get("dialogue_context")
                    )
                    if "narrative" in narrative:
                         result["log"] = f"Dialogue: {narrative['narrative']}"
                    else:
                         result["log"] = f"The {obj['type']} speaks: 'We must survive.'"
                else:
                    result["log"] = f"The {obj['type']} speaks: 'Fortune favors the bold!'"

                if self.active_scenario and self.active_scenario["win_condition"]["type"] == "TALKED_TO_NPC":
                    self._resolve_active_event("Negotiated/Contacted")
            else: result = {"success": False, "reason": "Nobody to talk to"}
        
        elif action_type == "wait" or action_type == "rest":
            result["log"] = "You take a moment to steady your breath."
            if self.player_combatant:
                self.player_combatant.hp = min(self.player_combatant.hp + 1, self.player_combatant.max_hp)

        elif action_type == "channel":
            # CHAOS CHANNELING (Separate Mechanic)
            if not self.chaos:
                result = {"success": False, "reason": "No Chaos Manager"}
            else:
                # Roll d10 vs Chaos Level (Design Bible IV)
                roll = random.randint(1, 10)
                level = self.chaos.chaos_level
                
                result["log"] = f"Channeling Chaos... Rolled {roll} vs Level {level}."
                
                # Logic Fix: Roll > Level (High Roll vs Difficulty)
                if roll > level:
                    # Success: Manifest Effect
                    # TODO: Add specific spell selection? For now, just a generic blast or mana restore
                    result["log"] += " SUCCESS! Pure chaos energy surges under your control."
                    if self.player_combatant:
                        self.player_combatant.fp = self.player_combatant.max_fp # Refill Focus
                else:
                    # Failure: Backfire (Roll <= Level)
                    result["log"] += " BACKFIRE! The energy writhes uncontrollably."
                    self.chaos.chaos_clock += 1 # Advance Clock
                    if self.player_combatant:
                        # Damage = Amount failed by? Or just flat? Design Bible implies severity.
                        dmg = (level - roll) + 1
                        self.player_combatant.take_damage(dmg) 
                        result["log"] += f" You take {dmg} damage!"

        # Catch-all for Spell/Skill usage
        else:
            known_abilities = []
            if self.player_combatant:
                known_abilities = [a.lower() for a in self.player_combatant.character.powers] + [s.lower() for s in self.player_combatant.character.skills]
            
            if action_type in known_abilities:
                # 1. Get Ability Data (Description/Effects) from loader
                ability_data = engine_hooks.get_ability_data(action_type)
                if ability_data:
                    desc = ability_data.get("Description") or ability_data.get("Effect") or ability_data.get("Effect Description")
                    
                    # 2. Build Context for EffectRegistry
                    log_messages = []
                    ctx = {
                        "attacker": self.player_combatant,
                        "engine": self,
                        "log": log_messages,
                        "state": self.state # Exploration or Combat
                    }
                    
                    # 3. Resolve Mechanics using Central Registry
                    try:
                        registry.resolve(desc, ctx)
                        result["success"] = True
                        if log_messages:
                            result["log"] = " ".join(log_messages)
                        else:
                            result["log"] = f"You use {action_type}."
                    except Exception as e:
                        result["success"] = False
                        result["reason"] = str(e)
                else:
                    # Fallback if no specific data found but known (e.g. built-in string)
                    if "wait" in action_type or "rest" in action_type:
                        registry.resolve("Rest", {"attacker": self.player_combatant, "log": result.setdefault("log_list", [])})
                        result["log"] = " ".join(result.pop("log_list", ["You rest."]))
                    else:
                        result["log"] = f"You use {action_type}."
            else:
                return {"success": False, "reason": f"Unknown action: {action_type}"}
                
        if not self.player_combatant:
            self.load_player()
            if not self.player_combatant:
                self.player_combatant = Combatant(data={"Name": "Player"})

        self._update_tactical_status()
        
        self._update_tactical_status()
        
        # Tension Rules: Only in EXPLORE mode, and only on time-consuming actions
        if self.chaos and self.state == "EXPLORE" and action_type in ["search", "disarm", "solve", "smash", "push", "vault", "climb", "pull", "open", "rest", "wait"]:
            t_res = self.chaos.roll_tension()
            result["tension"] = t_res
            if t_res == "EVENT":
                event_res = self.trigger_event()
                if "log" in result: result["log"] += " " + event_res["log"]
                else: result["log"] = event_res["log"]
                if "event" in event_res: result["event"] = event_res["event"]
                # Store event data for frontend modal
                if event_res.get("event") == "EVENT_TRIGGERED":
                    self.active_event_data = event_res.get("data")
                    self.is_event_resolved = False
                # Store event data for frontend modal
                if event_res.get("event") == "EVENT_TRIGGERED":
                    self.active_event_data = event_res.get("data")
                    self.is_event_resolved = False
            elif t_res == "CHAOS_EVENT":
                from brqse_engine.world.encounter_table import EncounterTable
                twist = EncounterTable.get_chaos_twist()
                msg = f"CHAOS SURGE: {twist['Domain']} - {twist['Description']}"
                if "log" in result: result["log"] += f" {msg}"
                else: result["log"] = msg
                # Trigger a specific Hazard/Scenario on surge
                event_res = self.trigger_event() # Could refine this to force Hazard 
                if "log" in result: result["log"] += " " + event_res["log"]
            elif t_res == "SAFE":
                if random.random() < 0.2:
                    atm = self.chaos.get_atmosphere()
                    if "log" in result: result["log"] += f" {atm['descriptor']}"
                    else: result["log"] = atm["descriptor"]
                elif "log" in result:
                    result["log"] += " Tension grows..."
                else:
                    result["log"] = "Tension grows with every step."

        # === ENEMY TURN (SIMPLIFIED) ===
        if self.state == "COMBAT" and action_type in ["move", "attack", "wait", "rest", "defend"] and not result.get("event") == "COMBAT_STARTED":
            try:
                # 0. Check for Dead Enemies & Drops
                # print(f"DEBUG: Checking {len(self.combat_engine.combatants)} combatants for death/drops")
                dead_enemies = [c for c in self.combat_engine.combatants if c.team != "Player" and c.is_dead]
                for dead in dead_enemies:
                    # print(f"DEBUG: Found dead enemy {dead}. has_key? {getattr(dead, 'has_key', 'NoAttr')}")
                    if hasattr(dead, "has_key") and dead.has_key:
                        # Drop Key
                        self.inventory.append({"id": dead.has_key, "name": dead.key_name})
                        if "log" in result: result["log"] += f" The enemy dropped a {dead.key_name}!"
                        else: result["log"] = f"The enemy dropped a {dead.key_name}!"
                        # Prevent double drop
                        dead.has_key = None
                
                # Simple AI: Move closer, Attack if adjacent
                if not "log" in result: result["log"] = ""
                
                enemies_acted = 0
                # Get enemy combatants from combat engine
                for c in self.combat_engine.combatants:
                    # Check if combatant is valid
                    if not c or not hasattr(c, "team"): continue
                    
                    if c.team != "Player" and not c.is_dead:
                        # Force Reset Action Economy for AI (simplification for this loop style)
                        c.action_used = False
                        
                        enemies_acted += 1
                        # SAFETY CHECK: positions
                        if c.x is None or c.y is None or self.player_combatant.x is None or self.player_combatant.y is None:
                            continue
                            
                        dist = abs(c.x - self.player_combatant.x) + abs(c.y - self.player_combatant.y)
                        
                        if dist <= 1:
                            # Attack!
                            # Check clash
                            clash_roll = random.randint(1, 20)
                            player_defence = random.randint(1, 20) + self.player_combatant.get_stat_modifier("Reflexes")
                            
                            if clash_roll > player_defence:
                                dmg = random.randint(1, 6)
                                self.player_combatant.take_damage(dmg)
                                result["log"] += f" {c.name} attacks you for {dmg} damage!"
                            else:
                                 result["log"] += f" {c.name} attacks but you dodge!"
                                 
                        elif dist > 1:
                             # Move closer
                             dx = 1 if self.player_combatant.x > c.x else -1 if self.player_combatant.x < c.x else 0
                             dy = 1 if self.player_combatant.y > c.y else -1 if self.player_combatant.y < c.y else 0
                             
                             # Check walls? For now, ghost movement to ensure they are scary
                             c.x += dx
                             c.y += dy
                             result["log"] += f" {c.name} advances."
            except Exception as e:
                print(f"[GameLoop] Enemy Turn Error: {e}")
                # traceback.print_exc()
                result["log"] += f" [Enemy AI Error: {str(e)}]"
            
            # === END OF TURN RESET ===
            # Since we use a Phase system (Player Action -> Enemy Reponse), we must reset the player for the next request.
            if self.player_combatant:
                self.player_combatant.action_used = False
                self.player_combatant.bonus_action_used = False
                self.player_combatant.reaction_used = False

        return result

    def _set_facing(self, direction: str):
        if self.player_combatant:
            self.player_combatant.facing = direction

    def _process_move(self, tx, ty) -> Dict[str, Any]:
        if not (0 <= tx < 20 and 0 <= ty < 20): return {"success": False, "reason": "Void"}
        tile = self.active_scene.grid[ty][tx]
        if tile == TILE_WALL: return {"success": False, "reason": "Stone"}
        if (tx, ty) in self.interactables and self.interactables[tx,ty].get("is_blocking"):
             return {"success": False, "reason": "Blocked"}
            
        self.player_pos = (tx, ty)
        if self.player_combatant: 
            self.player_combatant.elevation = 0
            self.player_combatant.x, self.player_combatant.y = tx, ty
        self._update_visibility()
        
        if tile == TILE_DOOR:
            if not self.is_event_resolved:
                return {"success": False, "reason": "The way is barred until the current situation is resolved."}
            self.advance_scene()
            return {"success": True, "event": "SCENE_ADVANCED"}
        return {"success": True}

    def _resolve_active_event(self, reason: str):
        """Called when a win condition is met."""
        self.is_event_resolved = True
        self.journal.resolve_last_event(reason)
        
        # UI Feedback
        self.current_event = "EVENT_RESOLVED"
        self.active_scene.text += " (CLEARED)"
        
        # If this was a Quest Goal, advance the stack logic
        if "GOAL" in self.active_scene.text:
             # Just a marker
             pass

        print(f"[GameLoop] Event Resolved: {reason}")

    def _update_tactical_status(self):
        """Checks surroundings for cover."""
        if not self.player_combatant: return
        px, py = self.player_pos
        has_cover = False
        # Improved cover detection: check adjacent tiles for 'cover' tag
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0: continue
                nx, ny = px + dx, py + dy
                if (nx, ny) in self.interactables:
                    obj = self.interactables[nx, ny]
                    if "cover" in obj.get("tags", []):
                        has_cover = True; break
            if has_cover: break
        self.player_combatant.is_behind_cover = has_cover

    def _update_visibility(self, radius=5):
        px, py = self.player_pos
        for y in range(max(0, py-radius), min(20, py+radius+1)):
             for x in range(max(0, px-radius), min(20, px+radius+1)):
                 if abs(x-px) + abs(y-py) <= radius + 1:
                     self.explored_tiles.add((x,y))

    def _is_blocked(self, x, y) -> bool:
        if not (0 <= x < 20 and 0 <= y < 20): return True
        tile = self.active_scene.grid[y][x]
        if tile == TILE_WALL: return True
        if (x, y) in self.interactables and self.interactables[x,y].get("is_blocking"):
             return True
        return False

    def _find_safe_spawn(self, scene) -> Tuple[int, int]:
        """BFS or scanning for nearest floor tile."""
        for dist in range(1, 10):
            for dy in range(-dist, dist + 1):
                for dx in range(-dist, dist + 1):
                    nx, ny = self.player_pos[0] + dx, self.player_pos[1] + dy
                    if 0 <= nx < 20 and 0 <= ny < 20:
                        if scene.grid[ny][nx] == TILE_FLOOR:
                            return (nx, ny)
        return self.player_pos # Fallback

    def force_combat(self):
        """Debug method to trigger combat."""
        res = {"log": "DEBUG: Forcing combat..."}
        self._manifest_v2_entity({"type": "ENEMY_SPAWN"}, {}, res)
        if self.state == "COMBAT":
             self.active_scenario = {"win_condition": {"type": "ENEMIES_KILLED"}, "narrative": "Forced Battle"}
        return res

    def _handle_combat_action(self, action: str, x: int, y: int) -> Dict[str, Any]:
        """Turn-based combat logic."""
        try:
            # RESET ACTION ECONOMY FLAGS at start of input processing
            # This logic assumes "One Click = One Action Opportunity" for the player in this game loop model
            if self.player_combatant:
                self.player_combatant.action_used = False
                self.player_combatant.bonus_action_used = False
                self.player_combatant.reaction_used = False

            res = {"success": True, "action": action}
            
            # 0. Check for Dead Enemies & Drops (Before new actions)
            dead_enemies = [c for c in self.combat_engine.combatants if c.team != "Player" and c.is_dead]
            for dead in dead_enemies:
                if hasattr(dead, "has_key") and dead.has_key:
                    # Drop Key
                    self.inventory.append({"id": dead.has_key, "name": dead.key_name})
                    if "log" in res: res["log"] += f" The enemy dropped a {dead.key_name}!"
                    else: res["log"] = f"The enemy dropped a {dead.key_name}!"
                    # Prevent double drop
                    dead.has_key = None
            
            # 1. Player Turn
            if action in ["move", "attack"]:
                # Check if clicking on an enemy -> Attack
                target = self.combat_engine.get_combatant_at(x, y)
                if target and target.team != "Player":
                    # Synchorize play pos just in case
                    px, py = self.player_pos
                    self.player_combatant.x, self.player_combatant.y = px, py
                    
                    # Check range (assume melee 1.5 tiles (diagonals ok) for now)
                    dist = math.hypot(x - px, y - py)
                    if dist <= 1.5:
                        # Use mechanics.py attack method
                        log_lines = self.combat_engine.attack_target(self.player_combatant, target)
                        res["log"] = " ".join(log_lines)
                        
                        # Extract details from replay log for Dice Log
                        if self.combat_engine.replay_log:
                            last_entry = self.combat_engine.replay_log[-1]
                            # Format based on entry type
                            if last_entry.get("type") in ["attack", "clash"]:
                                self.dice_log.append({
                                    "source": "Player",
                                    "action": last_entry.get("type", "Action").capitalize(),
                                    "roll": last_entry.get("attack_roll", 0),
                                    "details": last_entry.get("description", str(log_lines)),
                                    "result": last_entry.get("result", "INFO").upper()
                                })
                    else: 
                         return {"success": False, "reason": "Too far to attack"}
                
                elif action == "attack":
                     # Explicit attack on empty/friendly tile -> Fail
                     return {"success": False, "reason": "Nothing to attack here"}

                else:
                    # Move logic (mechanics.py might not have move validation exposed same way, using existing _process_move)
                    dist = abs(x - self.player_pos[0]) + abs(y - self.player_pos[1])
                    # Combatant from mechanics uses data.get("Stats") dict directly
                    stats = getattr(self.player_combatant, 'stats', {})
                    # Mechanics combatant calculates base_movement in init
                    speed = getattr(self.player_combatant, "base_movement", 6)
                    
                    if dist * 5 > speed * 5: # mechanics uses ft? No, grid units usually. Let's assume tiles.
                        # mechanics.py base_movement is usually 25+ (ft). 5 ft per tile.
                        # So speed in tiles = base_movement / 5
                        speed_tiles = speed / 5
                        if dist > speed_tiles:
                             return {"success": False, "reason": "Too far"}
                    
                    move_res = self._process_move(x, y) 
                    if not move_res["success"]: return move_res
                    
                    res["log"] = f"Moved to {x}, {y}."
            
            elif action in ["wait", "rest"]:
                 res["log"] = "You hold your ground."
                 if self.player_combatant:
                     heal = max(1, int(self.player_combatant.max_hp * 0.05))
                     self.player_combatant.hp = min(self.player_combatant.hp + heal, self.player_combatant.max_hp)
                     res["log"] += f" (+{heal} HP)"
            
            elif action == "Attack": 
                 res["log"] = "Select a target."
                 return {"success": False, "reason": "Select target"}
    
            # 2. Enemy Turn
            self._process_enemy_turns(res)
            
            # 3. Check State
            self._check_combat_end()
            
            return res
        except Exception as e:
            traceback.print_exc()
            return {"success": False, "reason": f"Combat Error: {str(e)}", "log": f"System Error: {str(e)}"}

    def _process_enemy_turns(self, result_log):
        """Simple enemy AI."""
        enemies = [c for c in self.combat_engine.combatants if c.team == "Enemies" and c.hp > 0]
        if not enemies: return
        
        log_entries = []
        for e in enemies:
            # Force Reset Action Economy for AI
            e.action_used = False
            
            # Simple AI: Move to player
            px, py = self.player_pos
            dist = math.hypot(px - e.x, py - e.y)
            
            if dist <= 1.5: # Adjacent-ish
                # Attack using mechanics engine
                # mechanics.py attack_target(attacker, target)
                log_lines = self.combat_engine.attack_target(e, self.player_combatant)
                log_entries.extend(log_lines)
            else:
                # Move towards player
                # Basic pathfinding towards player
                dx = 1 if px > e.x else -1 if px < e.x else 0
                dy = 1 if py > e.y else -1 if py < e.y else 0
                
                # Desired new pos
                nx, ny = e.x + dx, e.y + dy
                
                # Check collision (Walls, Player, Other Enemies)
                is_blocked = False
                if not (0 <= nx < 20 and 0 <= ny < 20): is_blocked = True
                elif self.active_scene.grid[ny][nx] == 0: is_blocked = True # Wall
                elif (nx, ny) == (px, py): is_blocked = True # Player
                elif self.combat_engine.get_combatant_at(nx, ny): is_blocked = True # Other enemy
                
                if not is_blocked:
                     e.x, e.y = nx, ny
        
        if log_entries:
            combined_log = " ".join(log_entries)
            if "log" in result_log: result_log["log"] += " " + combined_log
            else: result_log["log"] = combined_log

    def _check_combat_end(self):
        enemies = [c for c in self.combat_engine.combatants if c.team == "Enemies" and c.hp > 0]
        if not enemies:
            self.state = "EXPLORE"
            if self.active_scenario and self.active_scenario["win_condition"]["type"] == "ENEMIES_KILLED":
                 self._resolve_active_event("Victory")

    def get_state(self):
        # 1. Check for Auto-Resolution (e.g. Combat Over)
        if not self.is_event_resolved and self.active_scenario:
            win_type = self.active_scenario["win_condition"]["type"]
            if win_type == "ENEMIES_KILLED":
                enemies = [c for c in self.combat_engine.combatants if c.team == "Enemies" and c.hp > 0]
                has_grid_enemies = self.active_scene.grid_has_no_enemies() if self.active_scene else True
                if (not enemies and self.state == "COMBAT") or (not enemies and not has_grid_enemies):
                    self._resolve_active_event("Combat Victory")
                    self.state = "EXPLORE"

        # 2. Calculate progress
        if self.scene_stack:
            current_step = self.scene_stack.total_steps - len(self.scene_stack.stack)
            progress = f"{current_step}/{self.scene_stack.total_steps}"
            quest_title = self.scene_stack.quest_title
            quest_description = self.scene_stack.quest_description
        else:
            progress = "0/0"
            quest_title = "None"
            quest_description = "No active quest."
        
        return {
            "mode": self.state,
            "player_pos": self.player_pos,
            "grid": self.active_scene.grid if self.active_scene and hasattr(self.active_scene, 'grid') else [],
            "explored": [list(pos) for pos in self.explored_tiles],
            "objects": list(self.interactables.values()),
            "grid_w": 20, "grid_h": 20,
            "scene_text": self.active_scene.text if self.active_scene else "",
            "elevation": self.player_combatant.elevation if self.player_combatant else 0,
            "is_behind_cover": self.player_combatant.is_behind_cover if self.player_combatant else False,
            "facing": self.player_combatant.facing if self.player_combatant else "N",
            "quest_title": quest_title,
            "quest_description": quest_description,
            "quest_progress": progress,
            "quest_objective": self.active_scene.text if self.active_scene else "Explore",
            # v2 Event System info
            "is_event_resolved": self.is_event_resolved,
            "active_scenario": self.active_scenario,
            "is_event_resolved": self.is_event_resolved,
            "active_scenario": self.active_scenario,
            "journal": self.journal.get_summary(),
            "dice_log": self.dice_log[-50:], # Return last 50 logs
            # V2: Return combatants for rendering
            "combatants": [
                {
                    "name": c.name,
                    "x": c.x, "y": c.y,
                    "team": c.team,
                    "hp": c.hp,
                    "max_hp": c.max_hp,
                    "sprite": c.data.get("sprite") or c.data.get("Sprite") or c.data.get("Portrait", 'badger_front.png'),
                    "facing": getattr(c, 'facing', 'S'),
                    "tags": ["attack", "inspect"] if c.team == "Enemies" else ["talk", "inspect"]
                }
                for c in self.combat_engine.combatants if c.hp > 0
            ]
        }

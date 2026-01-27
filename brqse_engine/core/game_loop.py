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
from brqse_engine.core.interaction import InteractionEngine 
from brqse_engine.world.campaign_logger import CampaignLogger
from brqse_engine.world.donjon_generator import DonjonGenerator, Cell
from brqse_engine.world.story_director import StoryDirector
from brqse_engine.world.narrator import Narrator

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
        
        # Initialize Logger
        self.logger = CampaignLogger()
        self.chaos = chaos_manager
        
        # Initialize Interaction Engine with RAG capacity
        self.interaction = InteractionEngine(self.logger, sensory_layer)
        
        # Initialize Narrator (AI DM)
        self.narrator = Narrator(sensory_layer, self.logger)
        
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
        self.dungeon_cache = {} # Cache generated levels to prevent re-rolling on reload
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

        # AI-Enhanced Story Director Hook
        # Replace old MapGenerator with new Donjon+StoryDirector
        level = len(self.scene_stack.stack) + 1
        scene = self.generate_dungeon(level=level)
        
        # Ensure CombatEngine matches new grid size
        rows = len(scene.grid)
        cols = len(scene.grid[0])
        self.active_scene = scene
        self.combat_engine = CombatEngine(cols, rows)
        
        # Setup interactables and walls
        self.interactables = {(node["x"], node["y"]): node for node in scene.interactables}
        for y, row in enumerate(scene.grid):
            for x, tile in enumerate(row):
                if tile == TILE_WALL: self.combat_engine.create_wall(x, y)
                
        # LOAD PREBUILT ASI CONTENT
        if hasattr(scene, "prebuilt_objects"):
            for obj in scene.prebuilt_objects:
                # Convert ASI object format to GameLoop interactable format
                self.interactables[(obj["x"], obj["y"])] = {
                    "type": obj.get("subtype", obj.get("type", "Object")), # Use subtype for naming if avail
                    "x": obj["x"], "y": obj["y"],
                    "tags": obj.get("tags", ["inspect"]),
                    "is_blocking": True, # Most objects block
                    "is_locked": obj.get("locked", False), # ASI uses "locked", Loop uses "is_locked"
                    "required_key": obj.get("key_required"),
                    "has_key": obj.get("has_key"),
                    "key_name": obj.get("key_name")
                }
                # Update tile visual
                if obj.get("type") == "chest": self.active_scene.grid[obj["y"]][obj["x"]] = TILE_LOOT
                if obj.get("type") == "door": self.active_scene.grid[obj["y"]][obj["x"]] = TILE_DOOR

        if hasattr(scene, "prebuilt_entities"):
            from brqse_engine.combat.mechanics import Combatant
            import json
            # We need a way to load enemy stats by type
            # For now, simplistic fallback or loop through known files
            
            for ent in scene.prebuilt_entities:
                # 1. Try to load stats based on type
                # Assuming ent["type"] maps to a filename like "orc_jailer"
                # TODO: Real loader. For now, hacky generic.
                
                # Try spawning it via spawner to get stats
                from brqse_engine.combat.enemy_spawner import spawner
                try:
                    # Map ASI type to filename key
                    fname = ent["type"] # e.g. "orc_jailer" or "BST_01"
                    
                    beast_id = fname if fname.startswith("BST_") else None
                    if not beast_id and "orc" in fname: beast_id = "BST_05" # Fallback mapping if old types exist
                    
                    # Spawn specific beast if ID is known, otherwise random for biome
                    path = spawner.spawn_beast(beast_id=beast_id, biome="DUNGEON", level=1)
                    with open(path, 'r') as f: enemy_data = json.load(f)
                    
                    enemy = Combatant(data=enemy_data)
                    enemy.name = ent["name"]
                    enemy.team = ent.get("team", "Enemies")
                    
                    # INJECT ASI BRAIN
                    if "ai_context" in ent:
                        enemy.ai_context = ent["ai_context"]
                        
                    self.active_scene.grid[ent["y"]][ent["x"]] = TILE_ENEMY
                    self.combat_engine.add_combatant(enemy, ent["x"], ent["y"])
                except Exception as e:
                    print(f"Failed to spawn ASI entity {ent['name']}: {e}")
        
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

    # --- NEW: AI-Driven Generation ---
    def generate_dungeon(self, level=1):
        """
        Uses DonjonGenerator + StoryDirector to build a level.
        """
        # 0. Check Cache
        if level in self.dungeon_cache:
            print(f"[GameLoop] Loading cached dungeon for Level {level}")
            return self.dungeon_cache[level]

        # 1. Generate Topology
        dg = DonjonGenerator()
        # Must be Odd for Maze algorithm
        # CombatEngine expects consistent size. Let's use 21x21.
        w, h = 21, 21
        map_data = dg.generate(width=w, height=h)
        
        # 2. Director Scripting (The Hook)
        director = StoryDirector(sensory_layer=self.sensory_layer)
        director.direct_scene(map_data, level, self.logger)
        
        # 3. Convert to active scene
        # TITLE: Level X - Theme
        scene = Scene(f"Level {level}: {map_data.get('theme', 'Dungeon')}", "DUNGEON")
        scene.biome = map_data.get("theme", "Dungeon")
        
        # INTRO: Set the main description to the AI's narrative hook
        if "intro" in map_data:
            scene.text = map_data["intro"]
        
        # Convert Donjon Grid to Game Grid
        # Donjon: 0=Nothing, 1=Blocked, 2=Room, 4=Corridor
        # Game: 0=Wall, 1=Floor
        rows, cols = len(map_data["grid"]), len(map_data["grid"][0])
        game_grid = [[TILE_WALL for _ in range(cols)] for _ in range(rows)]
        
        for r in range(rows):
            for c in range(cols):
                cell = map_data["grid"][r][c]
                if cell & (Cell.ROOM | Cell.CORRIDOR):
                    game_grid[r][c] = TILE_FLOOR
                if cell & Cell.DOOR:
                    game_grid[r][c] = TILE_DOOR
                    
        # Apply Objects & Entities
        interactables = []
        for obj in map_data.get("objects", []):
            game_grid[obj["y"]][obj["x"]] = TILE_LOOT # Visual
            if obj["type"] == "door": game_grid[obj["y"]][obj["x"]] = TILE_DOOR
            
            # Add to interactables
            self.interactables[(obj["x"], obj["y"])] = obj
            
        for ent in map_data.get("entities", []):
            game_grid[ent["y"]][ent["x"]] = TILE_ENEMY
            # Spawn logic...
            # For brevity, reusing the existing spawn logic in _manifest or manual here
            from brqse_engine.combat.mechanics import Combatant
            if ent.get("type") == "boss_monster":
                # Create Combatant from data dict
                c_data = {
                    "Name": ent["name"],
                    "HP": 50, # Placeholder
                    "Stats": {"Might": 14, "Reflexes": 12}, 
                    "Sprite": "badger_front.png" # Placeholder
                }
                c = Combatant(data=c_data)
                c.team = "Enemies"
                c.ai_context = ent.get("ai_context")
                self.combat_engine.add_combatant(c, ent["x"], ent["y"])

        scene.grid = game_grid
        self.active_scene = scene
        
        # Set Player Start
        start_room = list(map_data["rooms"].values())[0] # Naive start
        self.player_pos = start_room["center"]
        
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
                "type": setup_item.get("subtype", "Object"), 
                "name": setup_item.get("name") or setup_item.get("subtype", "Object"), # Fix: Ensure Name
                "x": sx, "y": sy,
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
        
        # --- NEW: Inspector ---
        if action_type == "debug_inspect":
            self._debug_inspect_room(x, y)
            return {"success": True, "log": "Inspector triggered. Check console."}

        # --- NEW: Interaction Engine Integration ---
        # Map specific actions to generic 'interact' or handle legacy logic via tags
        
        # Get target object (if any)
        # Note: In new system, objects should be Entity instances. 
        # For now, we wrap legacy dicts into Entity on the fly OR rely on InteractionEngine 
        # to handle dicts if we updated it (we didn't, so let's stick to dicts for now 
        # but the InteractionEngine expects objects with .has_tag).
        
        # BRIDGE: Convert dict object to Entity-like wrapper for InteractionEngine
        obj_data = self.interactables.get((x, y))
        target_entity = None
        if obj_data:
            from brqse_engine.models.entity import Entity
            target_entity = Entity(obj_data.get("name", "Unknown"), x, y)
            # Hydrate tags
            for tag in obj_data.get("tags", []): target_entity.add_tag(tag)
            # Hydrate specific properties as data or tags
            if obj_data.get("is_locked"): target_entity.add_tag("locked")
            if obj_data.get("required_key"): 
                target_entity.data["required_key"] = obj_data["required_key"]
            if obj_data.get("has_key"):
                target_entity.add_tag("pickup") # Or specific tag?
                target_entity.data["pickup_item_id"] = obj_data["has_key"]
                target_entity.data["pickup_item_name"] = obj_data["key_name"]

        if action_type == "attack":
             # Transition to Combat if target is enemy
             target = self.combat_engine.get_combatant_at(x, y)
             if target and target.team != "Player":
                 self.state = "COMBAT"
                 result["log"] = f"Combat Started! {target.name} engages."
                 result["event"] = "COMBAT_STARTED"
                 # Execute the attack immediately as opener?
                 # No, let them have initiative roll or just start combat.
                 # Actually user wants to attack. Let's make it an opener.
                 log_lines = self.combat_engine.attack_target(self.player_combatant, target)
                 result["log"] += " " + " ".join(log_lines)
                 return result
             else:
                 return {"success": False, "reason": "Nothing to attack here."}

        # 1. MOVE
        if action_type == "move":
            move_res = self._process_move(x, y)
            if not move_res.get("success"): return move_res
            result.update(move_res)
            if "log" not in result: result["log"] = f"Moved to {x}, {y}."
            
        # 2. INTERACT / USE / OPEN / GET
        elif action_type in ["interact", "use", "open", "get", "pickup"]:
            if target_entity:
                # Wrap Player as Actor
                # We need a dummy actor that has 'inventory'
                class ActorWrapper:
                    def __init__(self, inventory): self.inventory = inventory
                
                # Convert self.inventory (list of dicts) to list of Entities for consistency?
                # InteractionEngine expects actors inventory to be objects with tags/data.
                # Let's wrap the inventory items too.
                actor_inv = []
                for item in self.inventory:
                     e = Entity(item["name"], 0, 0)
                     e.data["id"] = item["id"]
                     e.add_tag(item["id"]) # ID as tag for easy lookup
                     actor_inv.append(e)
                
                actor = ActorWrapper(actor_inv)
                
                # PERFORM INTERACTION
                log = self.interaction.interact(actor, target_entity)
                result["log"] = log
                
                # SYNC BACK STATE
                # If unlocked...
                if not target_entity.has_tag("locked") and obj_data.get("is_locked"):
                    obj_data["is_locked"] = False
                    # Update tags in map data
                    if "locked" in obj_data.get("tags", []): obj_data["tags"].remove("locked")
                    
                # If picked up...
                if target_entity.has_tag("carried"):
                    # Remove from world
                    del self.interactables[(x, y)]
                    self.active_scene.grid[y][x] = TILE_FLOOR
                    # Add to real inventory
                    if "pickup_item_id" in target_entity.data:
                         self.inventory.append({
                             "id": target_entity.data["pickup_item_id"],
                             "name": target_entity.data["pickup_item_name"]
                         })
            else:
                 result["log"] = "Nothing to interact with here."

        # 3. EXAMINE (Narrative Detailed Look)
        elif action_type == "examine":
            if target_entity:
                # 1. Get History Context
                depth = getattr(self.active_scene, "depth", 1)
                logs = self.logger.get_context(level=depth)
                # 2. Consult InteractionEngine (which asks Oracle)
                result["log"] = self.interaction.examine(target_entity, logs)
            else:
                 result["log"] = "You see nothing of interest here."

        # 4. CONSULT (Chatbot)
        elif action_type == "consult":
             # Payload "query" should be in the kwargs or extra args, 
             # but handle_action signature is (action, x, y). 
             # We might need to assume 'consult' is triggered with a special x,y or just ignore them 
             # and look for a way to pass query.
             # Actually, let's assume the query is passed via a property on self temporarily set 
             # or we change handle_action signature.
             # Given constraints, let's assume we use a 'last_query' state or similar if inputs are restricted.
             # OR: abuse X/Y or rely on a separate method. 
             # BUT: The requirement was to add it to handle_action.
             # Let's pivot: If action="consult", we expect the input string to be passed somehow.
             # We will look for it in `self.game_state.last_chat_input` if we had one, or ...
             # Hack: We'll allow the caller to pass it as 'x' if type is string? No 'x' is int tag.
             pass # Placeholder until better input hook defined, handled separate loop usually.

        # 5. INSPECT (Technical Tag Dump)
        elif action_type == "inspect":
            if target_entity:
                tags = sorted(list(target_entity.tags))
                result["log"] = f"[DEBUG] {target_entity.name} Tags: {tags}"
            else:
                 result["log"] = "An ordinary patch of ground."


        


        






        # 3. EXAMINE (Narrative detailed look)
        elif action_type == "examine":
            if target_entity:
                # 1. Get History Context
                depth = getattr(self.active_scene, "depth", 1)
                logs = self.logger.get_context(level=depth)
                # 2. Consult InteractionEngine (which asks Oracle)
                result["log"] = self.interaction.examine(target_entity, logs)
            else:
                 result["log"] = "You see nothing of interest here."
        
        # 4. CONSULT (Chatbot)
        elif action_type == "consult":
             # Placeholder until better input hook defined
             pass 

        elif action_type == "track":
             result = self._handle_track_action(x, y)
             
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

        # --- NEW: AI Narrator Hook (Exploration/Events) ---
        if self.narrator and result.get("success"):
            # If we have an active scene, pass its context
            context = self.active_scene.biome if self.active_scene else "dungeon"
            
            # Narrate significant events (Discovery, Tension, etc.)
            flavor = self.narrator.narrate(result, state_context=context)
            if flavor:
                # Override the mechanical log
                result["log"] = flavor

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
        
        # Check Enemy Collision
        enemy = self.combat_engine.get_combatant_at(tx, ty)
        if enemy and enemy.team != "Player" and enemy.hp > 0:
            self.state = "COMBAT"
            return {"success": False, "reason": f"Running into {enemy.name} starts combat!", "event": "COMBAT_STARTED", "log": f"You bump into {enemy.name}. Combat!"}
            
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
            
            # --- NEW: AI Narrator Hook ---
            if self.narrator and res.get("success"):
                context = self.active_scene.biome if self.active_scene else "dungeon"
                flavor = self.narrator.narrate(res, state_context=context)
                if flavor: res["log"] = flavor
            
            return res
            
        except Exception as e:
            traceback.print_exc()
            return {"success": False, "reason": f"Combat Error: {str(e)}", "log": f"System Error: {str(e)}"}

    def _handle_combat_action(self, action, x, y):
        # Oops, previous code snippet seemed to be inside _handle_combat_action?
        # No, wait. I need to be careful. The VIEW showed lines 1080+ which seemed to be inside _handle_combat_action based on 'res' variable.
        # But my previous edit replaced lines in 'handle_action' (generic).
        # Let's look at where I am. 
        # Line 413 calls self._handle_combat_action(action_type, x, y)
        # So I should probably put the Narrator hook inside _handle_combat_action too OR just wrapper handle_action?
        # The prompt "AI DM" implies *all* actions.
        # My previous edit was likely trying to edit _handle_combat_action but I treated it as handle_action?
        # Let's revert to a safe state where I wrap the RETURN of handle_action.
        pass

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
            "grid_w": len(self.active_scene.grid[0]) if self.active_scene and self.active_scene.grid else 20,
            "grid_h": len(self.active_scene.grid) if self.active_scene and self.active_scene.grid else 20,
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

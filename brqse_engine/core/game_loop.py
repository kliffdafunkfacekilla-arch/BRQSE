from typing import Dict, Any, Tuple, List
import random
from brqse_engine.combat.combat_engine import CombatEngine
from brqse_engine.world.map_generator import MapGenerator, TILE_WALL, TILE_FLOOR, TILE_LOOT, TILE_ENEMY, TILE_HAZARD, TILE_DOOR
from brqse_engine.combat.combatant import Combatant
from scripts.world_engine import SceneStack, ChaosManager, Scene

class GameLoopController:
    """
    Manages the active game session:
    - Exploration Mode (Move, Search, Interact)
    - Combat Mode (Turn-based)
    - Scene Transitions
    """
    
    def __init__(self, chaos_manager: ChaosManager, game_state: Any = None):
        self.chaos = chaos_manager
        self.game_state = game_state
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
        self.current_event = "SCENE_STARTED"
        
        self.scene_stack.generate_quest()
        self.advance_scene()

    def advance_scene(self) -> Scene:
        """Moves to next scene, resets visibility."""
        scene = self.scene_stack.advance()
        if scene.text == "QUEST COMPLETE":
            self.active_scene = scene
            self.current_event = "QUEST_COMPLETE"
            return scene

        scene = self.map_gen.generate_map(scene)
        self.active_scene = scene
        self.combat_engine = CombatEngine(20, 20)
        for y, row in enumerate(scene.grid):
            for x, tile in enumerate(row):
                if tile == TILE_WALL: self.combat_engine.create_wall(x, y)
        
        if scene.entrances: 
            self.player_pos = scene.entrances[0]
            # --- SAFE SPAWN CHECK ---
            if self._is_blocked(*self.player_pos):
                self.player_pos = self._find_safe_spawn(scene)
        
        self.interactables = {(node["x"], node["y"]): node for node in scene.interactables}
        self.explored_tiles = set()
        self._update_visibility()
        
        if self.player_combatant:
            self.player_combatant.elevation = 0
            self.player_combatant.is_behind_cover = False
            self.player_combatant.facing = "N"
        else:
            self.load_player() # Attempt reload if missing
            
        self.state = "EXPLORE"
        self.current_event = "SCENE_STARTED"
        return scene

    def load_player(self):
        """Loads or reloads the player character from GameState."""
        if not self.game_state: return
        
        player_data = self.game_state.get_player()
        if player_data:
            from brqse_engine.models.character import Character
            self.player_combatant = Combatant(Character(player_data))
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
        if self.state != "EXPLORE": return {"success": False, "reason": "Combat Lock"}

        # Update Facing for all actions
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
        
        elif action_type == "inspect":
            result["log"] = f"A sturdy {obj['type']}." if obj else "An ordinary patch of ground."

        elif action_type == "search":
            result["log"] = f"Search {obj['type']}... nothing." if obj else "Scoured the ground... dust."
            
        elif action_type == "smash":
            if obj and "smash" in obj.get("tags", []):
                result["log"] = f"Smashed {obj['type']}!"
                self.active_scene.grid[y][x] = TILE_FLOOR
                del self.interactables[x,y]
            else: result = {"success": False, "reason": "Fail"}
            
        elif action_type in ["push", "pull", "climb", "vault", "flip", "open"]:
            if obj and action_type in obj.get("tags", []):
                result["log"] = f"{action_type} {obj['type']}."
                if action_type in ["climb", "vault"] and "elevation" in obj.get("tags", []):
                    self.player_pos = (x, y)
                    if self.player_combatant: self.player_combatant.elevation = 1
            else: result = {"success": False, "reason": "Fail"}
            
        if not self.player_combatant:
            self.load_player()
            if not self.player_combatant:
                from brqse_engine.models.character import Character
                self.player_combatant = Combatant(Character({"Name": "Player"}))

        self._update_tactical_status()
        
        if self.chaos:
            result["tension"] = self.chaos.roll_tension()

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
        if self.player_combatant: self.player_combatant.elevation = 0
        self._update_visibility()
        
        if tile == TILE_DOOR:
            self.advance_scene()
            return {"success": True, "event": "SCENE_ADVANCED"}
        return {"success": True}

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

    def _update_visibility(self):
        px, py = self.player_pos
        radius = 5
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

    def get_state(self):
        return {
            "mode": self.state,
            "player_pos": self.player_pos,
            "grid": self.active_scene.grid if self.active_scene and hasattr(self.active_scene, 'grid') else [],
            "explored": list(self.explored_tiles),
            "objects": list(self.interactables.values()),
            "grid_w": 20, "grid_h": 20,
            "scene_text": self.active_scene.text if self.active_scene else "",
            "elevation": self.player_combatant.elevation if self.player_combatant else 0,
            "is_behind_cover": self.player_combatant.is_behind_cover if self.player_combatant else False,
            "facing": self.player_combatant.facing if self.player_combatant else "N"
        }

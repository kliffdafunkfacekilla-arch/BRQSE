from typing import Dict, Any, Tuple, List
from brqse_engine.combat.combat_engine import CombatEngine
from brqse_engine.world.map_generator import MapGenerator, TILE_WALL, TILE_FLOOR, TILE_LOOT, TILE_ENEMY
from brqse_engine.combat.combatant import Combatant
from scripts.world_engine import SceneStack, ChaosManager, Scene

class GameLoopController:
    """
    Manages the active game session:
    - Exploration Mode (Free move, real-time-ish interact)
    - Combat Mode (Turn-based, Initiative)
    - Transitions between them
    """
    
    def __init__(self, chaos_manager: ChaosManager):
        self.chaos = chaos_manager
        self.scene_stack = SceneStack(self.chaos)
        self.map_gen = MapGenerator(self.chaos)
        self.combat_engine = CombatEngine(20, 20) # Updated to 20x20
        
        self.state = "EXPLORE" # EXPLORE, COMBAT, DIALOGUE
        self.player_pos = (1, 10) # Default
        self.step_counter = 0 # For tension rolls
        
        self.active_scene = None
        self.interactables = {}
        self.explored_tiles = set()
        
        # Load initial quest
        self.scene_stack.generate_quest()
        self.advance_scene()

    def advance_scene(self) -> Scene:
        """Moves to next scene, generates map, places player."""
        scene = self.scene_stack.advance()
        
        # Generate Map Data (modifies scene in-place)
        scene = self.map_gen.generate_map(scene)
        self.active_scene = scene
        
        # Setup Combat Engine Grid (for Combat Mode usage)
        self.combat_engine = CombatEngine(20, 20)
        
        # 1. Apply Walls to Combat Engine (for potential combat checks later)
        for y, row in enumerate(scene.grid):
            for x, tile in enumerate(row):
                if tile == TILE_WALL:
                    self.combat_engine.create_wall(x, y)
                elif tile == TILE_ENEMY and scene.encounter_type == "COMBAT":
                    pass

        # 2. Place Player
        if scene.entrances:
            self.player_pos = scene.entrances[0]
        else:
            self.player_pos = (1, 10)
        
        # 3. Setup Interactables
        self.interactables = {
            (node["x"], node["y"]): node for node in scene.loot_nodes
        }
        
        # 4. Initialize Visibility
        self.explored_tiles = set()
        self._update_visibility()
            
        self.current_scene_text = scene.text
        self.state = "EXPLORE"
        return scene

    def _update_visibility(self):
        # Reveal radius around player (e.g. 5 tiles)
        px, py = self.player_pos
        radius = 5 # Should come from Character Awareness
        for y in range(max(0, py-radius), min(20, py+radius+1)):
             for x in range(max(0, px-radius), min(20, px+radius+1)):
                 # Simple Euclidean-ish or Chebyshev
                 if abs(x-px) + abs(y-py) <= radius + 1: # Manhattan with buffer?
                     self.explored_tiles.add((x,y))

    def handle_move(self, target_x: int, target_y: int, traits: List[str] = None) -> Dict[str, Any]:
        """
        Attempts to move player to target.
        Returns result dict for UI.
        """
        if traits is None: traits = []
        
        if self.state != "EXPLORE":
            return {"success": False, "reason": "Not in Exploration Mode"}
            
        # 1. Distance Check (1 tile only)
        dx = abs(target_x - self.player_pos[0])
        dy = abs(target_y - self.player_pos[1])
        if dx > 1 or dy > 1 or (dx == 0 and dy == 0):
             return {"success": False, "reason": "Too far"}
             
        # 2. Collision Check (Grid)
        if not (0 <= target_x < 20 and 0 <= target_y < 20):
             return {"success": False, "reason": "Out of bounds"}

        tile = self.active_scene.grid[target_y][target_x]
        
        # WALL LOGIC
        if tile == TILE_WALL:
             if "Sticky Pads" in traits:
                 pass # Climb!
             else:
                 return {"success": False, "reason": "Blocked"}
                 
        # HAZARD LOGIC
        if tile == TILE_HAZARD:
             # Wings allow flying over hazards safely
             pass 

        # HUGE SIZE LOGIC (Squeeze penalty/check)
        if "Huge Size" in traits:
             # Check for 1-tile narrow corridor
             # If moving horizontally, check up/down walls
             blocked_v = False
             blocked_h = False
             
             # Check vertical squeeze (walls above and below)
             if (target_y > 0 and self.active_scene.grid[target_y-1][target_x] == TILE_WALL) and \
                (target_y < 19 and self.active_scene.grid[target_y+1][target_x] == TILE_WALL):
                 blocked_v = True
                 
             # Check horizontal squeeze (walls left and right)
             if (target_x > 0 and self.active_scene.grid[target_y][target_x-1] == TILE_WALL) and \
                (target_x < 19 and self.active_scene.grid[target_y][target_x+1] == TILE_WALL):
                 blocked_h = True
                 
             if blocked_v or blocked_h:
                 # Apply penalty or block? User said "Cannot fit ... without squeezing (Movement penalty)"
                 # For now, we'll just log it as an event, or maybe consume extra tension step?
                 self.step_counter += 1 # Double step cost
        
        # 3. Object Collision (Interactables)
        if (target_x, target_y) in self.interactables and tile != TILE_LOOT: # Loot is walkable-ish if we decide so, but usually interact first
             return {"success": False, "reason": "Object in way (Click to Interact)"}
             
        # 4. Execute Move
        self.player_pos = (target_x, target_y)
        self.step_counter += 1
        
        # UPDATE VISIBILITY
        self._update_visibility()
        
        # 5. Check Tension (Every 10 steps)
        tension_result = "SAFE"
        if self.step_counter >= 10:
            self.step_counter = 0
            if "Wings" in traits and tile == TILE_HAZARD:
                 # Flying over hazard is safe? Maybe reduce tension risk?
                 pass
            elif tile == TILE_HAZARD:
                 # Walking in hazard triggers tension immediately?
                 tension_result = self.chaos.roll_tension() # Hazard triggers check
            else:
                 tension_result = self.chaos.roll_tension()
            
        # 6. Check Combat Trigger
        if self.active_scene.encounter_type == "COMBAT":
             for y in range(max(0, target_y-3), min(20, target_y+4)):
                 for x in range(max(0, target_x-3), min(20, target_x+4)):
                     if self.active_scene.grid[y][x] == TILE_ENEMY:
                          self.start_combat()
                          return {
                             "success": True, 
                             "player_pos": self.player_pos,
                             "tension": tension_result,
                             "event": "COMBAT_STARTED"
                          }

        return {
            "success": True, 
            "player_pos": self.player_pos,
            "tension": tension_result
        }

        
    def handle_interact(self, target_x: int, target_y: int) -> Dict[str, Any]:
        # Check adjacency
        px, py = self.player_pos
        if abs(target_x - px) > 1 or abs(target_y - py) > 1:
            return {"success": False, "reason": "Too far"}
            
        if (target_x, target_y) in self.interactables:
            obj = self.interactables.pop((target_x, target_y))
            
            # Remove from grid so it's walkable? Or replace with open chest?
            # For simplicity, just remove logic blocking
            if self.active_scene.grid[target_y][target_x] == TILE_LOOT:
                 self.active_scene.grid[target_y][target_x] = TILE_FLOOR
                 
            return {"success": True, "effect": f"Interacted with {obj['type']}"}
            
        return {"success": False, "reason": "Nothing there"}

    def start_combat(self):
        self.state = "COMBAT"
        # Logic to init combatants in engine
        # self.combat_engine.start_combat()

    def get_state(self):
        # Construct backward compatible wall list for now?
        # Or just rely on grid. Let's send everything.
        walls = []
        if self.active_scene:
            for y, row in enumerate(self.active_scene.grid):
                for x, tile in enumerate(row):
                    if tile == TILE_WALL:
                        walls.append((x, y))

        return {
            "mode": self.state,
            "player_pos": self.player_pos,
            "scene": self.current_scene_text if self.active_scene else "",
            "grid": self.active_scene.grid if self.active_scene else [],
            "explored": list(self.explored_tiles),
            "walls": walls, # Legacy support
            "objects": list(self.interactables.values()),
            "grid_w": 20,
            "grid_h": 20
        }

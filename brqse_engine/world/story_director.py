import random
import math
import requests
import json
from brqse_engine.world.event_manager import EventManager
from brqse_engine.world.donjon_generator import Cell

class StoryDirector:
    """
    The ASI (Artificial Story Intelligence).
    It orchestrates the level layout and uses Local AI to write the lore.
    """

    def __init__(self, api_url="http://localhost:5001/generate", sensory_layer=None):
        self.events = EventManager()
        self.api_url = api_url
        self.sensory_layer = sensory_layer
        # Fallback names if AI is offline
        self.fallback_names = ["Gorg", "Thrak", "The Silent One", "Darko"]

    # --- Helper: AI Communication ---
    def _consult_ai(self, prompt, temp=0.7):
        """
        Sends a request to your local 'simple_api.py' OR uses internal SensoryLayer.
        """
        if self.sensory_layer:
            try:
                # Direct internal call (Self-Hosted mode)
                return self.sensory_layer.consult_oracle("You are a creative game master.", prompt)
            except Exception as e:
                print(f"[StoryDirector] Internal AI fail: {e}")
                return None
        
        # Fallback to HTTP
        payload = {
            "prompt": f"System: You are a creative game master.\nUser: {prompt}\nAssistant:",
            "max_new_tokens": 100,
            "temperature": temp
        }
        try:
            response = requests.post(self.api_url, json=payload, timeout=5)
            if response.status_code == 200:
                text = response.json().get("response", "").strip().strip('"')
                return text
        except:
            return None 
        return None

    # --- Helper: Spawning ---
    def _spawn_object(self, map_data, room, obj_data):
        map_data.setdefault("objects", [])
        obj_data["x"], obj_data["y"] = room["center"]
        obj_data["room_id"] = room["id"]
        map_data["objects"].append(obj_data)

    def _spawn_entity(self, map_data, room, ent_data):
        map_data.setdefault("entities", [])
        ent_data["x"], ent_data["y"] = room["center"]
        ent_data["room_id"] = room["id"]
        map_data["entities"].append(ent_data)

    def handle_entity_death(self, entity, map_data, logger):
        """
        Called when an entity dies. Checks for plot breaks and asks AI to patch them.
        """
        # 1. Check Role
        ai_context = getattr(entity, "ai_context", {})
        role = ai_context.get("role")
        
        if role in ["guardian", "boss", "quest_giver"]:
            # 2. Consult AI for a Patch
            problem = f"The player killed {entity.name}, who was the {role}. The story flow might be broken. How does the player proceed?"
            patch = self._consult_ai(
                f"{problem} Provide a one-sentence adaptation (e.g. 'The key slides into a grate', 'A ghost rises').", 
                temp=0.8
            )
            
            if patch:
                logger.log(map_data.get("depth", 1), "PATCH", f"DM Adaptation: {patch}", tags={"entity": entity.name})
                
                # 3. Mechanically Apply Patch (Simple Heuristic: Spawn Ghost)
                if "ghost" in patch.lower() or "spirit" in patch.lower():
                    # Find room
                    room = self._find_room_by_pos(map_data, entity.x, entity.y)
                    if room:
                        self._spawn_entity(map_data, room, {
                            "type": "ghost_remnant", 
                            "name": f"Ghost of {entity.name}",
                            "description": "A spectral remnant lingering with purpose.",
                            "tags": ["neutral", "spirit"]
                        })

    def _find_room_by_pos(self, map_data, x, y):
        for r in map_data["rooms"].values():
            if r["x"] <= x < r["x"] + r["w"] and r["y"] <= y < r["y"] + r["h"]:
                return r
        return None

    def inject_scene_context(self, map_data, scene):
        """
        Flavors a single-scene map based on a specific Scene object.
        Used by CampaignBuilder for the Linked Map System.
        """
        # 1. Set Meta
        map_data["theme"] = scene.biome
        map_data["scene_title"] = scene.text
        
        # 2. Main Description (Scene Text)
        # We can ask AI to expand this if it's brief
        if len(scene.text) < 50:
             expanded = self._consult_ai(f"Describe a location based on this prompt: '{scene.text}'. The location is in a {scene.biome}. 2 sentences.")
             map_data["intro"] = expanded or scene.text
        else:
            map_data["intro"] = scene.text
            
        # 3. Spawn Scene Enemy (if any)
        # Place in the "Best" room (Strategy: Goal Room or Center?)
        # For a single scene map, usually the last room is the 'Goal' of that scene.
        rooms = list(map_data["rooms"].values())
        if not rooms: return
        
        # Heuristic: Place enemy in the last room (furthest)
        # or if it's a Boss scene, definitely last.
        target_room = rooms[-1]
        
        if scene.enemy_data:
             self._spawn_entity(map_data, target_room, {
                "type": "enemy", 
                "name": scene.enemy_data["Species"],
                "tags": ["enemy", "hostile"],
                "ai_context": {"role": "antagonist", "motive": "guarding area"}
             })
             
        # 4. Fill other rooms with minor flavor
        for r in rooms:
            if r == target_room: continue
            if random.random() < 0.3:
                # Minor exploration event
                self._spawn_object(map_data, r, {
                    "type": "flavor", 
                    "name": "Atmosphere", 
                    "description": "Evidence of recent activity.",
                    "tags": ["scenery"]
                })

    def direct_scene(self, map_data, level_depth, logger):
        # Legacy method compatibility or removal?
        # Keeping it for now but it's largely superseded by inject_scene_context in the new flow.
        pass

    # --- Helper: Topology ---
    def _find_room_with_feature(self, map_data, flag):
        grid = map_data["grid"]
        for r in map_data["rooms"].values():
            cx, cy = r["center"]
            # Check center or near center? The logic in user code checked center.
            # But feature flags are usually on specific tiles.
            # Checking just the center tile for the flag:
            if grid[cy][cx] & flag: return r
        return None

    def _get_furthest_room(self, start, rooms):
        best, max_d = start, 0
        sx, sy = start["center"]
        for r in rooms:
            rx, ry = r["center"]
            d = math.sqrt((rx-sx)**2 + (ry-sy)**2)
            if d > max_d: max_d, best = d, r
        return best

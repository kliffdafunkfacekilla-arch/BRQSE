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
    def __init__(self, api_url="http://localhost:5001/generate"):
        self.events = EventManager()
        self.api_url = api_url
        # Fallback names if AI is offline
        self.fallback_names = ["Gorg", "Thrak", "The Silent One", "Darko"]

    def direct_scene(self, map_data, level_depth, logger):
        rooms = list(map_data["rooms"].values())
        if not rooms: return

        # 1. AI: Generate a Theme for this floor
        theme_prompt = f"Give me a short, evocative theme for Dungeon Level {level_depth} (e.g. 'The Flooded Barracks', 'The Crystal Mines'). Return ONLY the name."
        theme = self._consult_ai(theme_prompt) or f"Dungeon Level {level_depth}"
        map_data["theme"] = theme
        
        logger.log(level_depth, "THEME", f"Theme established: {theme}")

        # 2. Topology: Find Start (Stairs Up) and Goal (Furthest Room)
        start_room = self._find_room_with_feature(map_data, Cell.STAIR_UP) or rooms[0]
        goal_room = self._get_furthest_room(start_room, rooms)
        
        # 3. Lock & Key Puzzle
        key_room = random.choice(rooms)
        # Avoid placing key in start or goal for now, though goal could have boss+key
        attempts = 0
        while key_room["id"] in [start_room["id"], goal_room["id"]] and attempts < 10:
            key_room = random.choice(rooms)
            attempts += 1

        # 4. Generate The "MacGuffin" (The Key Item)
        key_name = self._consult_ai(f"Name a mystical key found in {theme}. Return ONLY the name.") or "Iron Key"
        key_id = f"key_{level_depth}"
        
        # Spawn Key
        self._spawn_object(map_data, key_room, {
            "id": key_id, "type": "key", "name": key_name,
            "tags": ["pickup", "quest_item", "key", f"key_{level_depth}"], # Correct tag for locking mechanic
            "description": f"The key to the level's exit, found in {theme}."
        })
        logger.log(level_depth, "QUEST", f"The {key_name} is hidden in Room {key_room['id']}.", tags={"room_id": key_room['id']})

        # 5. Generate The Boss (The Guardian)
        boss_name = self._consult_ai(f"Name a dangerous mini-boss creature living in {theme}. Return ONLY the name.") or "Dungeon Guardian"
        boss_desc = self._consult_ai(f"Describe the appearance of {boss_name} in one sentence.") or "It looks angry."
        
        # Spawn Boss in Goal Room? User code said "key room or goal room".
        # Logic says Key guards exit, or Boss guards Key. 
        # User code: "Spawn Boss in Key Room or Goal Room" (implementation used Key Room context but variable naming?)
        # Let's put Boss in Key Room to guard it.
        self._spawn_entity(map_data, key_room, {
            "type": "boss_monster", "name": boss_name,
            "tags": ["enemy", "boss", "flesh"],
            "description": boss_desc,
            "ai_context": {"role": "guardian", "guarding": key_id}
        })
        logger.log(level_depth, "BOSS", f"{boss_name} guards the key in Room {key_room['id']}.", tags={"boss_name": boss_name})

        # 6. Fill Empty Rooms with Random Events (Flavored by AI)
        for room in rooms:
            # Skip critical rooms
            if room["id"] in [start_room["id"], goal_room["id"], key_room["id"]]: continue
            
            # 20% Chance of Event
            if random.random() < 0.2:
                event = self.events.get_random_event()
                if event:
                    # Ask AI to flavor this generic event to fit the Theme
                    flavor_text = self._consult_ai(
                        f"Describe a '{event['name']}' event occurring in {theme}. One sentence.", 
                        temp=0.8
                    )
                    
                    self._spawn_object(map_data, room, {
                        "type": "event_marker", "name": event['name'],
                        "tags": ["event", "inspectable"],
                        "description": flavor_text or event.get('description', "An event.")
                    })
                    logger.log(level_depth, "EVENT", f"Room {room['id']}: {flavor_text}", tags={"event_type": event.get('type', 'Unknown')})

    # --- Helper: AI Communication ---
    def _consult_ai(self, prompt, temp=0.7):
        """
        Sends a request to your local 'simple_api.py'.
        """
        payload = {
            "prompt": f"System: You are a creative game master.\nUser: {prompt}\nAssistant:",
            "max_new_tokens": 60,
            "temperature": temp
        }
        try:
            response = requests.post(self.api_url, json=payload, timeout=5) # Increased timeout slightly
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

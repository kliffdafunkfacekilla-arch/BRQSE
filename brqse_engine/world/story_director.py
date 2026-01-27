import random
import math
from brqse_engine.world.event_manager import EventManager

class StoryDirector:
    """
    The ASI (Artificial Story Intelligence).
    Responsible for placing Logic, Keys, Locks, and Bosses into a pre-generated map.
    """
    def __init__(self):
        self.events = EventManager()

    def direct_scene(self, map_data, level_depth):
        """
        Injects story data into the map dictionary.
        """
        rooms = list(map_data["rooms"].values())
        if not rooms: return

        # 1. Topology Analysis
        # Identify the "Entry Room" (where stairs up are) and "Exit Room"
        start_room = self._find_room_with_feature(map_data, 0x400000) # STAIR_UP
        if not start_room: start_room = rooms[0]

        # 2. Pick the Goal (The Boss/Stairs Down)
        # We want the room furthest from the start
        goal_room = self._get_furthest_room(start_room, rooms)
        
        # 3. Create a Lock & Key Puzzle
        # Pick a room midway between start and goal to hold the key
        key_room = random.choice(rooms)
        while key_room == start_room or key_room == goal_room:
            key_room = random.choice(rooms)

        # 4. Inject Entities
        # Make sure the map has lists for these
        if "entities" not in map_data: map_data["entities"] = []
        if "objects" not in map_data: map_data["objects"] = []

        # -- Place Key --
        key_id = f"iron_key_{level_depth}"
        cx, cy = key_room["center"]
        map_data["objects"].append({
            "type": "key", "id": key_id, "name": "Iron Key",
            "x": cx, "y": cy,
            "description": "A heavy iron key encrusted with rust.",
            # Compatibility with current engine:
            "subtype": "Loot Cache",
            "has_key": key_id,
            "key_name": "Iron Key",
            "tags": ["search"]
        })
        
        # -- Place Guardian (Context Aware AI) --
        # This entity KNOWS it is guarding the key
        map_data["entities"].append({
            "name": f"Keykeeper of Level {level_depth}",
            "type": "orc_jailer",
            "subtype": "Orc Jailer", # Engine compat
            "x": cx, "y": cy,
            "ai_context": {
                "role": "guardian",
                "target_object_id": key_id,
                "patrol_room_id": key_room["id"]
            }
        })

        # -- Place Locked Chest/Door at Goal --
        # Decide if it's the STAIRS or a CHEST. If this is the last room, likely stairs down are locked or guarded.
        gx, gy = goal_room["center"]
        
        # Compatible Locked Object
        map_data["objects"].append({
            "type": "chest", "id": f"chest_{level_depth}",
            "subtype": "Reinforced Chest", # Engine compat
            "x": gx, "y": gy,
            "is_locked": True,
            "required_key": key_id,
            "loot_table": f"tier_{level_depth}_loot",
            "tags": ["open", "unlock", "inspect"]
        })

        # -- Place Boss --
        map_data["entities"].append({
            "name": f"Boss of Level {level_depth}",
            "type": "troll_warlord",
            "subtype": "Troll Warlord", # Engine compat
            "x": gx, "y": gy,
            "team": "Enemies",
            "ai_context": {
                "role": "boss",
                "shout_on_sight": "You shall not pass to the next level!"
            }
        })

        # NEW: Populate remaining empty rooms with Random Events
        for room in rooms:
            # Skip if room is already critical (Start/End/Key)
            # Logic: If center is occupied, skip?
            # Better: Check against known locations
            cx, cy = room["center"]
            is_occupied = False
            # Check objects
            for obj in map_data["objects"]:
                if obj["x"] == cx and obj["y"] == cy: is_occupied = True
            for ent in map_data["entities"]:
                 if ent["x"] == cx and ent["y"] == cy: is_occupied = True
                 
            if is_occupied: continue
            
            # Roll an event (10% chance of Chaos)
            event = self.events.get_random_event(chaos_chance=0.1)
            self._apply_event_to_room(map_data, room, event)

        print(f"   [ASI] Lvl {level_depth}: Key in Room {key_room['id']} -> Chest in Room {goal_room['id']}")

    def _apply_event_to_room(self, map_data, room, event):
        cx, cy = room["center"]
        
        if event["type"] == "empty": return

        # Add a marker/object
        obj_data = {
            "x": cx, "y": cy,
            "type": "event_trigger",
            "subtype": "Curious Object",
            "icon": "mysterious_orb", 
            "event_data": event,
            "tags": ["inspect", "touch"]
        }
        
        # Customize based on type
        if event["type"] == "combat":
            obj_data["subtype"] = "Battle Sign"
            if "Goblins" in event["description"]: obj_data["subtype"] = "Goblin Camp"
            
            # Spawn Enemies
            from brqse_engine.combat.enemy_spawner import spawner
            beast = None
            if spawner.beast_data:
                # Filter for actual beasts (ignoring empty rows)
                valid_beasts = [b for b in spawner.beast_data if b.get("Entity_ID") and b["Entity_ID"].startswith("BST")]
                if valid_beasts:
                    beast = random.choice(valid_beasts)
            
            ent_type = beast["Entity_ID"] if beast else "BST_01"
            ent_name = f"{beast.get('Family_Name')} {beast.get('Role')}" if beast else event["name"]

            map_data["entities"].append({
                "x": cx, "y": cy,
                "type": ent_type,
                "team": "Enemies",
                "name": ent_name,
                "description": event["description"] 
            })
            
        elif event["type"] == "treasure":
            obj_data["subtype"] = "Lost Treasure"
            obj_data["tags"] = ["search", "loot"]
            
        map_data["objects"].append(obj_data)

    def _find_room_with_feature(self, map_data, feature_flag):
        # Look through rooms to see if one contains a specific tile flag (like stairs)
        grid = map_data["grid"]
        for room in map_data["rooms"].values():
            cx, cy = room["center"]
            if grid[cy][cx] & feature_flag:
                return room
        return None

    def _get_furthest_room(self, start_room, rooms):
        best_room = start_room
        max_dist = 0
        sx, sy = start_room["center"]
        
        for room in rooms:
            rx, ry = room["center"]
            dist = math.sqrt((rx-sx)**2 + (ry-sy)**2)
            if dist > max_dist:
                max_dist = dist
                best_room = room
        return best_room

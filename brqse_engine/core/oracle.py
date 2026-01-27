import json

class DungeonOracle:
    def __init__(self, sensory_layer):
        self.sensory_layer = sensory_layer

    def inspect_entity(self, entity, room_history):
        """
        Explains an object using Tags + History.
        This remains deterministic/hybrid for speed, but we could RAG it too.
        For now, let's keep the reliable tag description but add RAG flavor if available.
        """
        # 1. Base Description from Tags
        desc = f"You are looking at a {entity.name}."
        
        details = []
        if entity.has_tag("locked"):
            details.append("It is sealed tight.")
        if entity.has_tag("flammable"):
            details.append("It looks dry enough to burn.")
        if entity.has_tag("heavy"):
            details.append("It looks incredibly heavy.")
        if entity.has_tag("valuable"):
            details.append("It glitters with value.")
        if entity.has_tag("enemy"):
            details.append("It looks hostile.")
        if entity.has_tag("search"):
            details.append("It seems to contain something.")

        # 2. Context from Story Director (The "Why")
        lore = ""
        if room_history:
            for entry in room_history:
                ent_id = entity.data.get("id")
                if ent_id and str(ent_id) == str(entry.get("tags", {}).get("item_id")):
                    lore = f"\n(Insight): {entry['text']}"
                    break
                if entry["category"] == "CHAOS" and "event_trigger" in entity.data.get("type", ""):
                     if "event_type" in entry.get("tags", {}) and entry["tags"]["event_type"] == entity.data.get("event_data", {}).get("type"):
                        lore = f"\n(Warning): The air around it warps. {entry['text']}"

        return f"{desc} {' '.join(details)} {lore}"

    def consult(self, player_input, game_state):
        """
        RAG-based Consultation.
        """
        # --- Step 1: Gather Context (Retrieval) ---
        # 1. Room Context
        player = game_state.player
        # Note: game_state objects need 'room_id' or we calculate it.
        # Assuming we can filter objects by proximity or room if set.
        # For now, just grab visible objects in the scene.
        visible_objects = [
            f"{o.name} ({', '.join(list(o.tags))})" 
            for o in game_state.objects 
            if abs(o.x - player.x) <= 10 and abs(o.y - player.y) <= 8 # Approximate screen bounds
        ]
        
        # 2. History Context
        # Get logs for current level
        depth = getattr(game_state, "current_depth", 1)
        # We need the logger which is on InteractionEngine? 
        # Actually DungeonOracle is init with sensory_layer, but we need Logger for retrieval.
        # Plan change: DungeonOracle needs Logger access too or GameState needs it.
        # GameState usually doesn't hold Logger, GameLoop does.
        # But consult is passed `game_state` which in `handle_action` is `self` (GameLoopController).
        # So `game_state` IS `GameLoopController` instance based on our previous call.
        
        logger = getattr(game_state, "logger", None)
        room_logs = []
        if logger:
            # Try to get room-specific logs if we can infer room logic, or just level logs
            # Let's give it the last 5 level logs for immediate context
            all_logs = logger.get_context(level=depth)
            room_logs = all_logs[-5:] if all_logs else []
            
        # 3. Player Status
        hp_status = f"{player.hp}/{player.max_hp}"
        inventory = [i.name for i in getattr(game_state, "inventory", [])]

        # --- Step 2: Construct System Prompt ---
        system_prompt = f"""
        You are the Dungeon Master (The Oracle).
        
        [GAME STATE]
        - Level: {depth}
        - Player HP: {hp_status}
        - Inventory: {', '.join(inventory)}
        - Nearby Objects: {', '.join(visible_objects)}
        - Recent Events: {json.dumps(room_logs)}
        
        [INSTRUCTION]
        Answer the player's question briefly (under 50 words) and in character.
        If they ask for a hint, use the Nearby Objects.
        If they ask about story, use Recent Events.
        Do not make up facts that contradict the State.
        """

        # --- Step 3: Consult RAG ---
        return self.sensory_layer.consult_oracle(system_prompt, player_input)

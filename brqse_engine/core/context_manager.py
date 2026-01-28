import json

class ContextManager:
    """
    Aggregates the full game state into a 'Mega-Prompt' for the active AI.
    Sources: Player Data, Visible Gameplay Objects, Story Logs, and Rules.
    """
    def __init__(self, game_loop):
        self.loop = game_loop
        # We access game_state via the loop usually, or pass it directly.
        # The plan said internal logic uses game_state, but in GameLoopController, 
        # 'self.game_state' is the persistence manager, while 'self' holds the active simulation.
        # So we'll accept the GameLoopController instance as 'game_loop'.

    def build_full_context(self):
        """
        Compiles the context string.
        """
        if not self.loop.player_combatant:
            return "[Context Unavailable: No active player]"

        player = self.loop.player_combatant
        scene = self.loop.active_scene
        
        # 1. Player Context
        # Status Effects not fully implemented in Combatant yet, using placeholders/attributes if avail
        effects = getattr(player, "status_effects", [])
        inventory = [item["name"] for item in self.loop.inventory]
        
        # Safe access to class info
        char_class = "Unknown"
        if hasattr(player, "character") and player.character:
            char_class = getattr(player.character, "char_class", "Unknown")
        elif hasattr(player, "char_class"):
            char_class = player.char_class
            
        player_ctx = f"""
        [PLAYER STATUS]
        Name: {player.name} | HP: {player.hp}/{player.max_hp} | Class: {char_class}
        Inventory: {', '.join(inventory) or "Empty"}
        Active Effects: {', '.join(effects) or "None"}
        """

        # 2. Location Context
        # Fetch visible items/entities within range of player
        visible_objs = []
        px, py = self.loop.player_pos
        
        # Scan immediate area (e.g. 7x7 grid around player)
        view_radius = 5
        seen_entities = []
        
        if scene:
            # Objects
            for (ox, oy), obj in self.loop.interactables.items():
                if abs(ox - px) <= view_radius and abs(oy - py) <= view_radius:
                    name = obj.get("name", obj.get("type", "Object"))
                    tags = ",".join(obj.get("tags", []))
                    visible_objs.append(f"{name} ({tags})")

            # Entities (Combatants)
            for c in self.loop.combat_engine.combatants:
                if c == player: continue
                if c.hp <= 0: continue # Skip dead
                if abs(c.x - px) <= view_radius and abs(c.y - py) <= view_radius:
                    seen_entities.append(f"{c.name} (Team: {c.team})")
        
        scene_name = getattr(scene, "name", "Unknown Location") if scene else "Unknown Location"
        loc_ctx = f"""
        [LOCATION]
        Scene: {scene_name}
        Visible Objects: {', '.join(visible_objs) or "None"}
        Visible Entities: {', '.join(seen_entities) or "None"}
        """

        # 3. Story Context (History)
        # Using CampaignLogger
        logger = self.loop.logger
        depth = getattr(scene, "depth", 1) if scene else 1
        
        recent_logs = []
        quest_logs = []
        
        if logger:
             # Just grab last 5 entries of current level
             all_logs = logger.get_context(level=depth)
             recent_logs = all_logs[-5:]
             # Filter for QUEST category
             quest_logs = [l for l in all_logs if l.get("category") == "QUEST"]

        story_ctx = f"""
        [STORY STATE]
        Active Quests: {self._format_logs(quest_logs)}
        Recent Events: {self._format_logs(recent_logs)}
        """

        # 4. Rules Context
        # Dynamic injection based on visible tags
        rules_ctx = "[RULES]"
        obj_str = str(visible_objs).lower()
        if "wood" in obj_str or "crate" in obj_str:
             rules_ctx += "\n- Wood objects are flammable. Fire deals 1d6 dmg/turn."
        if "water" in obj_str or "pool" in obj_str:
             rules_ctx += "\n- Water extinguishes fire and conducts electricity."
        if seen_entities:
             rules_ctx += "\n- Combat is turn-based. Roll d20 + Bonus vs AC to hit."
        if "lock" in obj_str or "door" in obj_str:
             rules_ctx += "\n- Locked objects require a specific Key to open. 'Unlock' action checks Inventory."

        return f"{player_ctx}\n{loc_ctx}\n{story_ctx}\n{rules_ctx}"

    def _format_logs(self, logs):
        if not logs: return "None"
        return "\n".join([f"- {l['text']}" for l in logs])

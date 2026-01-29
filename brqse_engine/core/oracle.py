from brqse_engine.core.context_manager import ContextManager
from brqse_engine.core.arbiter import Arbiter
from brqse_engine.core.dice import Dice

class DungeonOracle:
    def __init__(self, sensory_layer, game_loop=None):
        self.sensory_layer = sensory_layer
        self.loop = game_loop
        self.ctx_manager = ContextManager(game_loop) if game_loop else None
        self.arbiter = Arbiter(sensory_layer=sensory_layer) # Pass sensory layer directly
        self.dice = Dice() # Standard d20 system

        
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
        details.append(f"Tags: {', '.join(entity.tags)}")

        # 2. Context from Story Director (The "Why")
        lore = ""
        if room_history:
            for entry in room_history:
                ent_id = entity.data.get("id")
                if ent_id and str(ent_id) == str(entry.get("tags", {}).get("item_id")):
                    lore = f"\n(Insight): {entry['text']}"
                    break
        return f"{desc} {' '.join(details)} {lore}"

    def speak_as_npc(self, npc_entity, player_message):
        """
        Converses with an NPC using Persona + World Context.
        """
        if not self.ctx_manager:
            return "The air is heavy, but no words come."

        # 1. Fetch NPC Persona from tags or data
        archetype = npc_entity.data.get("archetype", "Cryptic Sage")
        voice_cue = npc_entity.data.get("voice_cue", "Mysterious and indirect.")
        motive = npc_entity.data.get("motive", "Wants to test the traveler's intent.")
        
        # 2. Build the Persona Prompt
        full_context = self.ctx_manager.build_full_context()
        
        prompt = f"""
        You are an NPC in a Dark Fantasy RPG. 
        YOUR NAME: {npc_entity.name}
        YOUR ARCHETYPE: {archetype}
        YOUR VOICE: {voice_cue}
        YOUR MOTIVE: {motive}
        
        CURRENT WORLD CONTEXT:
        {full_context}
        
        PLAYER SAYS: "{player_message}"
        
        INSTRUCTIONS:
        - Speak in character using your assigned voice and archetype.
        - Use first person ("I", "Me").
        - Keep it brief (under 40 words).
        - If the player asks about the world, use the context provided.
        
        NPC:
        """
        
        # 3. Call AI
        response = self.sensory_layer.consult_oracle(prompt, player_message)
        return response

    def chat(self, user_message):
        """
        Direct chat interface for the player (Omniscient GM).
        Now with Arbiter Interception for Skill Checks.
        """
        if not self.ctx_manager:
            return "The spirits are silent (Context Manager not initialized)."

        # 1. ARBITRATION STEP: Check for Risky Actions
        # We pass self.loop as game_state context if needed
        check_request = self.arbiter.judge_intent(user_message, self.loop)
        
        roll_info = ""
        
        if check_request:
            # A check is required!
            skill = check_request.get("skill", "General")
            dc = check_request.get("dc", 10)
            reason = check_request.get("reason", "Unknown risk")
            
            # Auto-Resolve Roll (Simulated Player Roll)
            # In a full UI, we'd ask the frontend to roll, but here we auto-roll for fluid chat.
            # TODO: Fetch actual player stats for bonus.
            bonus = 0
            # Resolve Bonus
            bonus = 0
            if self.loop and self.loop.player_combatant:
                # 1. Get Attribute from Arbiter (e.g. "MIGHT")
                attr_name = check_request.get("attribute", "Might").title()
                
                # 2. Get Modifier from Player (e.g. +3)
                # Ensure get_stat_modifier exists/works
                if hasattr(self.loop.player_combatant, "get_stat_modifier"):
                    bonus = self.loop.player_combatant.get_stat_modifier(attr_name)
                else:
                    # Fallback if bare entity
                    stats = getattr(self.loop.player_combatant, "stats", {})
                    score = stats.get(attr_name, 10)
                    bonus = (score - 10) // 2

            # Dice returns (total, rolls, breakdown)
            roll_val, _, _ = self.dice.roll("1d20")
            total = roll_val + bonus
            success = total >= dc
            outcome = "SUCCESS" if success else "FAILURE"
            
            roll_info = f"""
            [SYSTEM EVENT]
            ACTION: {user_message}
            CHECK: {skill} ({attr_name.upper()} {bonus:+}) vs DC {dc} | REASON: {reason}
            RESULT: {outcome} (Rolled {roll_val} {bonus:+} = {total})
            """
            
            # Only append to prompt. We return the narration of this result.
            # We modify the user message seen by the AI to include the mechanical truth.
            user_message = f"{user_message} \n(MECHANICAL TRUTH: {roll_info})"

        # 2. Build the Mega-Context
        full_context = self.ctx_manager.build_full_context()
        
        # 3. Build Prompt
        prompt = f"""
        You are the Dungeon Master. Use the Game State and Rules below to answer the player.
        
        {full_context}
        
        PLAYER INPUT: "{user_message}"
        
        INSTRUCTIONS:
        - If [SYSTEM EVENT] is present, NARRATE the outcome ({roll_info}) dramatically. Do not ask for a roll, it is already done.
        - If no system event, answer normally.
        - Keep it brief (under 50 words).
        
        DM:
        """

        # 4. Call AI
        response = self.sensory_layer.consult_oracle(prompt, user_message)
        
        # Prepend the roll info to the response so the user sees the mechanics too
        if roll_info:
            response = f"{roll_info.strip()}\n\n{response}"
            
        return response

    def consult(self, player_input, game_state=None):
        """
        Backwards compatibility alias for chat.
        """
        return self.chat(player_input)

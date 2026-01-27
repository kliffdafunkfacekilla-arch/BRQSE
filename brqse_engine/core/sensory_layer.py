import json
import os
import random
import requests

class SensoryLayer:
    """
    The Sensory Layer acts as the translator between the mechanical Game State
    and the Player's Narrative Experience.
    
    It consumes raw data (Outcome Tags, Biome Tags, Chaos State) and produces
    sensory-rich descriptions via an LLM.
    """
    
    SYSTEM_PROMPT = """You are the Game Master for a grimdark tactical RPG called The Chaos Engine. 
You do not calculate damage or roll dice; the Engine provides those numbers. 
Your job is to describe the scene, the action, and the consequence based on the biome tags and physics data provided. 
Your tone changes based on the 'Chaos Level' provided in the prompt.

Start descriptions directly with the sensory details. Use present tense."""

    def __init__(self, model="llama3:latest", api_url="http://localhost:11434/api/chat"):
        self.model = model
        self.api_url = api_url
        self.history = []

            
    def consult_oracle(self, system_prompt, user_query):
        """
        Direct interface for RAG-based Oracle.
        """
        try:
            import requests
        except ImportError:
            return "The Oracle's voice is lost (requests library missing)."

        # Prepare Ollama Payload with Custom System Prompt
        ollama_payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            "stream": False
        }
        
        try:
            print(f"[SensoryLayer] Oracle consulting {self.model}...", flush=True)
            response = requests.post(self.api_url, json=ollama_payload, timeout=30)
            response.raise_for_status()
            
            result_json = response.json()
            return result_json.get("message", {}).get("content", "The mists obscure all answers.")
            
        except requests.exceptions.RequestException as e:
            print(f"[SensoryLayer] Oracle Error: {e}", flush=True)
            return "The Oracle is silent (Connection Error)."

    def generate_narrative(self, context, event_type, combat_data=None, quest_context=None):
        """
        Main entry point for generating descriptions.
        """
        try:
            import requests
        except ImportError:
            return {"error": "Missing 'requests' library. Please pip install requests."}

        payload = self._build_payload(context, event_type, combat_data, quest_context)
        prompt_content = self._construct_prompt(payload)
        
        # Prepare Ollama Payload
        ollama_payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt_content}
            ],
            "stream": False
        }
        
        try:
            print(f"[SensoryLayer] Sending request to {self.model} via {self.api_url}...", flush=True)
            # Increased timeout to 60s for initial model loading
            response = requests.post(self.api_url, json=ollama_payload, timeout=60)
            response.raise_for_status()
            
            result_json = response.json()
            narrative = result_json.get("message", {}).get("content", "")
            
            return {
                "payload": payload,
                "narrative": narrative,
                "raw_response": result_json
            }
            
        except requests.exceptions.RequestException as e:
            print(f"[SensoryLayer] Connection Error/Timeout: {e}", flush=True)
            print("[SensoryLayer] Falling back to Mock Generator...", flush=True)
            return {
                "payload": payload,
                "error": str(e),
                "narrative": self.mock_api_call(payload) # Fallback to mock
            }

    def _build_payload(self, context, event_type, combat_data, quest_context=None):
        """Constructs the JSON State Object."""
        
        # 1. Base State
        state = {
            "dm_mode": "narrator",
            "chaos_level": context.get("chaos_level", 1),
            "chaos_clock": context.get("chaos_clock", 0),
            "tension": context.get("tension", "Low"),
            "quest_context": quest_context,
            "inventory": context.get("inventory", []),
            "context": {
                "location": context.get("biome", "Unknown"),
                "atmosphere": context.get("atmosphere", "Neutral"),
                "lighting": context.get("lighting", "Dim"),
                "smell": context.get("smell", "Stale air")
            }
        }
        
        # 2. Add Event Data
        if event_type == "SCENE":
            state["event"] = {
                "type": "SCENE_ENTER",
                "features": context.get("features", [])
            }
            
        elif event_type == "COMBAT":
             # "Describe a heavy hammer strike..."
             state["event"] = {
                 "type": "COMBAT_ACTION",
                 "actor": combat_data.get("actor_name", "Unknown"),
                 "target": combat_data.get("target_name", "Unknown"),
                 "action": combat_data.get("action", "Attack"),
                 "weapon": combat_data.get("weapon", "Unarmed"),
                 "defense": combat_data.get("armor", "Unarmored"),
                 "result": combat_data.get("result", "Miss"), # Hit/Miss/Clash
                 "margin": combat_data.get("margin", 0),
                 "damage": combat_data.get("damage", 0),
                 "effect": combat_data.get("style", "Normal") # Crit/Glancing etc
             }
             
        elif event_type == "SOCIAL":
            state["event"] = {
                "type": "SOCIAL_INTERACTION",
                "actor": combat_data.get("actor_name"),
                "target": combat_data.get("target_name"),
                "method": combat_data.get("method", "Intimidation"), # e.g. Intimidation
                "defense": combat_data.get("defense", "Stoicism"),  # e.g. Stoicism
                "result": combat_data.get("result", "Failure")
            }
            if quest_context:
                state["instruction"] = f"The player talks to the NPC. They are on a quest: '{quest_context}'. The NPC should respond relevantly to this goal, either helping or hindering."
            
        elif event_type == "QUEST_GEN":
            # Direct instruction for JSON generation
            state["event"] = {
                "type": "QUEST_GENERATION",
                "rules": context.get("rules", {}),
                "rolls": context.get("rolls", {})
            }
            # Override instruction for JSON
            state["instruction"] = (
                "You are a Game Designer. Convert the provided RPG table rolls into a JSON scenario object. "
                "Output ONLY valid JSON. "
                "Schema: { "
                "'narrative': string (Atmospheric description), "
                "'goal_description': string (Clear, actionable 1-sentence task for the player, e.g. 'Defeat the Alpha Wolf' or 'Solve the Rune Puzzle'), "
                "'setup': [ { 'type': 'ENEMY_SPAWN'|'OBJECT_SPAWN', 'subtype': string, 'tags': [], 'count': int } ], "
                "'win_condition': { 'type': string } "
                "} "
                "Ensure the goal is OBVIOUS to the player."
            )

        # 3. Tone Injection based on Chaos Clock (only for narrative modes)
        if event_type != "QUEST_GEN":
            clock = state["chaos_clock"]
            if clock >= 10:
                 state["instruction"] = "The dungeon is actively hostile. Personify the environment. Shadows move. Walls breathe."
            elif clock >= 6:
                 state["instruction"] = "The atmosphere is tense. Use sensory details of decay and danger."
            else:
                 state["instruction"] = "Keep descriptions clinical and mysterious."
             
        return state

    def _construct_prompt(self, payload):
        """Wraps the payload in the final prompt string."""
        if payload.get("event", {}).get("type") == "QUEST_GENERATION":
             return f"GENERATE SCENARIO FROM ROLLS:\n{json.dumps(payload, indent=2)}\n\nRESPOND WITH JSON ONLY."
             
        return json.dumps(payload, indent=2)

    def mock_api_call(self, payload):
        """
        Simulates an API response for testing locally.
        """
        event = payload.get("event", {})
        etype = event.get("type")
        
        if etype == "COMBAT_ACTION":
            actor = event.get("actor")
            target = event.get("target")
            weapon = event.get("weapon")
            result = event.get("result")
            margin = event.get("margin")
            
            if result == "hit":
                return f"{actor} swings the {weapon} in a wide arc. It connects with {target}'s armor, buckling the metal and driving the breath from their lungs."
            elif result == "miss":
                return f"{actor} thrusts with the {weapon}, but {target} steps aside at the last moment. The blade bites harmlessly into the empty air."
            elif "clash" in str(result).lower():
                 return f"{actor} and {target} lock weapons. Sparks fly as metal grinds against metal. With a grunt of effort, they shove against each other, neither giving ground."
                 
        elif etype == "SCENE_ENTER":
            loc = payload["context"]["location"]
            atm = payload["context"]["atmosphere"]
            return f"You step into the {loc}. {atm}. The air smells of ozone and old dust."
            
        return "The scene shifts..."

import random

class Narrator:
    """
    The Voice of the Dungeon Master.
    Interprets raw game events and weaves them into a narrative.
    """
    def __init__(self, sensory_layer, logger):
        self.sensory_layer = sensory_layer
        self.logger = logger

    def narrate(self, action_result, state_context=None):
        """
        Takes the result of an action (success/fail, log) and flavors it.
        """
        raw_log = action_result.get("log", "")
        if not raw_log: return ""

        # Simple actions don't always need AI (save tokens/latency)
        # But user wants "AI DM", so we should flavor significant moments.
        
        event_type = action_result.get("event", "ACTION")
        
        # 1. Combat / intricate events -> AI Narration
        if event_type in ["COMBAT_STARTED", "ATTACK", "DEATH", "DISCOVERY"]:
            prompt = f"You are a Dungeon Master. The player just did this: '{raw_log}'. Describe the action and result in a thrilling, 2-sentence narrative specific to the {state_context or 'dungeon'}."
            flavor = self._consult_ai(prompt)
            if flavor:
                # Log the flavor to chronicle
                self.logger.log(0, "NARRATIVE", flavor) 
                return flavor
        
        # 2. Movement / trivial -> Return raw or light flavor
        return raw_log

    def _consult_ai(self, prompt):
        try:
            return self.sensory_layer.consult_oracle("You are a gritty fantasy narrator.", prompt)
        except Exception as e:
            print(f"[Narrator] AI Error: {e}")
            return None

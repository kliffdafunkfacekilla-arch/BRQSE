import random
import os
import csv
import json
from typing import Dict, Any, List, Optional

class EventEngine:
    """
    Handles the 5xD20 Modular Scenario generation and Instruction Interpretation.
    """
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.tables: Dict[str, List[Dict]] = {}
        self._load_tables()

    def _load_tables(self):
        mapping = {
            "archetype": "Modular_Archetype.csv",
            "subject": "Modular_Subject.csv",
            "context": "Modular_Context.csv",
            "reward": "Modular_Reward.csv",
            "chaos": "Modular_Chaos.csv"
        }
        for key, filename in mapping.items():
            path = os.path.join(self.data_dir, filename)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    self.tables[key] = list(csv.DictReader(f))
            else:
                self.tables[key] = []

    def generate_scenario(self, biome: str) -> Dict[str, Any]:
        """Rolls 5xD20 and generates a Mock AI Scenario JSON."""
        rolls = {
            "archetype": random.choice(self.tables["archetype"]),
            "subject": random.choice(self.tables["subject"]),
            "context": random.choice(self.tables["context"]),
            "reward": random.choice(self.tables["reward"]),
            "chaos": random.choice(self.tables["chaos"])
        }

        # Mock AI Narrative Construction
        archetype = rolls["archetype"]["Archetype"]
        subject = rolls["subject"]["Subject"]
        context = rolls["context"]["Context"]
        reward = rolls["reward"]["Reward"]
        twist = rolls["chaos"]["Power_Effect"]

        narrative = f"A {archetype} encounter unfolds! A group of {subject} is seen {context}. "
        narrative += f"The air ripples with {twist}. If successful, you might claim {reward}."

        # Generate Instruction Set (Mock AI Logic)
        scenario = {
            "narrative": narrative,
            "archetype": archetype,
            "subject": subject,
            "context": context,
            "reward": reward,
            "chaos_twist": twist,
            "setup": self._generate_setup(rolls),
            "win_condition": self._generate_win_condition(rolls)
        }
        return scenario

    def _generate_setup(self, rolls: Dict) -> List[Dict]:
        """Determines what to spawn based on Archetype."""
        archetype = rolls["archetype"]["Archetype"]
        setup = []
        
        if "Hostile" in archetype:
            setup.append({"type": "ENEMY_SPAWN", "count": random.randint(1, 3)})
        elif "Social" in archetype:
            setup.append({"type": "NPC_SPAWN", "subtype": rolls["subject"]["Subject"]})
        elif "Puzzle" in archetype:
            setup.append({"type": "OBJECT_SPAWN", "subtype": "Puzzle Mechanism", "tags": ["solve", "inspect"]})
        
        # Always spawn a potential reward container
        setup.append({"type": "OBJECT_SPAWN", "subtype": "Loot Cache", "tags": ["search", "open"], "is_locked": True})
        
        return setup

    def _generate_win_condition(self, rolls: Dict) -> Dict:
        """Determines the 'Resolve' trigger."""
        archetype = rolls["archetype"]["Archetype"]
        
        if "Hostile" in archetype:
            return {"type": "ENEMIES_KILLED"}
        elif "Social" in archetype:
            return {"type": "TALKED_TO_NPC"}
        elif "Puzzle" in archetype:
            return {"type": "PUZZLE_SOLVED"}
        
        return {"type": "LOCATION_REACHED"}

    def process_trigger(self, trigger_type: str, context: Dict) -> List[str]:
        """Interprets a trigger and returns a list of instructions."""
        # Simple Logic: Action -> Result
        instructions = []
        if trigger_type == "solve":
            instructions.append("RESOLVE_EVENT")
            instructions.append("LOG: The mechanism clicks into place!")
        elif trigger_type == "talk":
            instructions.append("RESOLVE_EVENT")
            instructions.append("LOG: The stranger shares their secrets.")
        elif trigger_type == "enemy_death":
            # Check if all enemies dead in GameLoop
            pass 
        return instructions

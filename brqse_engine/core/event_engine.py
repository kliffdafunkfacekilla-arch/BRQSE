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

    def generate_scenario(self, biome: str, sensory_layer=None) -> Dict[str, Any]:
        """Rolls 5xD20 and generates a Mock AI Scenario JSON."""
        rolls = {
            "archetype": random.choice(self.tables["archetype"]),
            "subject": random.choice(self.tables["subject"]),
            "context": random.choice(self.tables["context"]),
            "reward": random.choice(self.tables["reward"]),
            "chaos": random.choice(self.tables["chaos"])
        }

        # AI Narrative Construction
        archetype = rolls["archetype"]["Archetype"]
        subject = rolls["subject"]["Subject"]
        context = rolls["context"]["Context"]
        reward = rolls["reward"]["Reward"]
        twist = rolls["chaos"]["Power_Effect"]
        
        narrative = f"A {archetype} encounter unfolds! A group of {subject} is seen {context}. "
        narrative += f"The air ripples with {twist}. If successful, you might claim {reward}."

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

        # If Sensory Layer is available, let AI design the specifics
        if sensory_layer:
            try:
                ai_result = sensory_layer.generate_narrative(
                    {"rolls": rolls, "rules": scenario}, 
                    event_type="QUEST_GEN"
                )
                if ai_result and "narrative" in ai_result:
                    # Parse the JSON response
                    try:
                        raw_json = ai_result["narrative"]
                        # Sanitize Markdown
                        if "```json" in raw_json:
                            raw_json = raw_json.split("```json")[1].split("```")[0].strip()
                        elif "```" in raw_json:
                            raw_json = raw_json.split("```")[1].split("```")[0].strip()
                            
                        ai_data = json.loads(raw_json)
                        scenario.update(ai_data) # Override mechanical defaults with AI creativity
                        
                        # Ensure goal_description exists
                        if "goal_description" not in scenario:
                             scenario["goal_description"] = f"Complete the objective: {scenario['win_condition']['type']}"
                             
                        # Inject Context into Spawns
                        for item in scenario.get("setup", []):
                            item["dialogue_context"] = scenario["goal_description"]
                             
                        print("[EventEngine] AI Scenario applied successfully.")
                    except json.JSONDecodeError as e:
                         print(f"[EventEngine] JSON Decode Error: {e}")
                         print(f"[EventEngine] Raw Content: {ai_result['narrative']}")
            except Exception as e:
                print(f"[EventEngine] AI Generation failed: {e}")

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
        elif "Mystery" in archetype or "Forensic" in archetype or "Exploration" in archetype:
            setup.append({"type": "OBJECT_SPAWN", "subtype": "Strange Clue", "tags": ["track", "inspect"]})
            setup.append({"type": "OBJECT_SPAWN", "subtype": "Footprints", "tags": ["track"]})

        # Context-sensitive spawns
        context_str = rolls["context"]["Context"].lower()
        if "trapped" in context_str or "locked" in context_str or random.random() < 0.3:
             self._inject_lock_key_puzzle(setup, context_str)
        elif "trapped" in context_str:
             setup.append({"type": "OBJECT_SPAWN", "subtype": "Locked Cage", "tags": ["unlock", "inspect", "open"], "is_blocking": True})
        
        # Always spawn a potential reward container
        setup.append({"type": "OBJECT_SPAWN", "subtype": "Loot Cache", "tags": ["search", "open"], "is_locked": True})
        
        return setup

    def _inject_lock_key_puzzle(self, setup: List[Dict], context: str):
        """Injects a Key and a Locked Object into the setup."""
        key_id = f"key_{random.randint(100, 999)}"
        
        # 1. Create the Key (add to existing container or new one)
        # Try to find a Loot Cache or Enemy to hold the key
        holder = None
        for item in setup:
            if item["type"] == "ENEMY_SPAWN" or item.get("subtype") == "Loot Cache":
                holder = item
                break
        
        if holder:
            holder["has_key"] = key_id
            holder["key_name"] = "Iron Key"
        else:
            # Spawn a specific container for it
            setup.append({
                "type": "OBJECT_SPAWN", 
                "subtype": "Old Corpse", 
                "tags": ["search"], 
                "has_key": key_id,
                "key_name": "Bloody Key"
            })
            
        # 2. Create the Lock (Door or Chest)
        setup.append({
            "type": "OBJECT_SPAWN",
            "subtype": "Reinforced Chest",
            "tags": ["open", "unlock", "inspect"],
            "is_locked": True,
            "required_key": key_id,
            "is_blocking": True
        })

    def _generate_win_condition(self, rolls: Dict) -> Dict:
        """Determines the 'Resolve' trigger."""
        archetype = rolls["archetype"]["Archetype"]
        
        if "Hostile" in archetype:
            return {"type": "ENEMIES_KILLED"}
        elif "Social" in archetype:
            return {"type": "TALKED_TO_NPC"}
        elif "Puzzle" in archetype:
            return {"type": "PUZZLE_SOLVED"}
        elif "Mystery" in archetype or "Forensic" in archetype or "Exploration" in archetype:
            return {"type": "FIND_CLUES"}
        
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

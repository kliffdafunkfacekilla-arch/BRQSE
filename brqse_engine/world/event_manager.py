import csv
import random
import os

class EventManager:
    def __init__(self, data_dir=None):
        if data_dir is None:
            # Default to walking up from brqse_engine/world/event_manager.py -> ... -> Data
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.data_dir = os.path.join(base_dir, "Data")
        else:
            self.data_dir = data_dir
            
        self.tables = {
            "chaos": self._load_csv("Chaos_Twists.csv"),
            "combat": self._load_csv("Encounters_Combat.csv"),
            "flavor": self._load_csv("Encounters_Flavor.csv"),
            "hazard": self._load_csv("Encounters_Hazard.csv"),
            "puzzle": self._load_csv("Encounters_Puzzle.csv"),
            "social": self._load_csv("Encounters_Social.csv"),
            "treasure": self._load_csv("Encounters_Treasure.csv"),
        }

    def _load_csv(self, filename):
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path):
            print(f"⚠️ Warning: {filename} not found at {path}")
            return []
        
        entries = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                entries.append(row)
        return entries

    def get_random_event(self, event_type=None, chaos_chance=0.1):
        """
        Returns an event dict. 
        If event_type is None, picks randomly.
        chaos_chance: 0.0 to 1.0 probability of a Chaos Twist overriding the event.
        """
        # 1. Check for Chaos Override
        if random.random() < chaos_chance:
            return self.roll_chaos()

        # 2. Pick Event Type if generic
        if not event_type:
            event_type = random.choices(
                ["combat", "flavor", "hazard", "puzzle", "social", "treasure"],
                weights=[40, 20, 15, 10, 5, 10] # Adjust weights as needed
            )[0]

        # 3. Roll on specific table
        return self._roll_table(event_type)

    def roll_chaos(self):
        """ Forces a result from Chaos_Twists.csv """
        entry = self._roll_table("chaos")
        if entry["type"] == "empty": return entry
        
        # Chaos CSV headers: Twist, Description, Domain, etc.
        # Logic: Adapt to whatever headers exist
        data = entry["data"]
        return {
            "type": "chaos_twist",
            "name": data.get("Twist", "Chaos Twist"),
            "description": data.get("Description", "Reality bends..."),
            "effect": data.get("Domain", "Unknown"), # Mapping 'Domain' to effect type
            "data": data
        }

    def _roll_table(self, table_key):
        table = self.tables.get(table_key, [])
        if not table:
            return {"type": "empty", "description": "Nothing happens."}
        
        entry = random.choice(table)
        
        # Standardize Output
        # Headers might be "Event", "Description", "Suggested Creatures"
        name = entry.get("Event", entry.get("Encounter_Structure", "Unknown Event"))
        desc = entry.get("Description", entry.get("Suggested_Creatures", ""))
        
        return {
            "type": table_key,
            "name": name,
            "description": desc,
            "data": entry # Keep raw data just in case
        }

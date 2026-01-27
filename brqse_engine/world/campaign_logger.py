import json
import os
from datetime import datetime

class CampaignLogger:
    def __init__(self, save_dir="Saves/WorldStack"):
        self.save_dir = save_dir
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            
        self.history = []
        self.filepath = os.path.join(self.save_dir, "world_chronicle.json")
        # Ensure file exists or reset it
        self._append_to_file(None)

    def log(self, level, category, text, tags=None):
        """
        level: Integer depth (e.g., 1)
        category: String (e.g., "MAIN_QUEST", "EVENT", "CHAOS")
        text: The human-readable story bit
        tags: Dictionary of data for the AI (e.g., entity_ids, coordinates)
        """
        entry = {
            "id": len(self.history) + 1,
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "category": category,
            "text": text,
            "tags": tags or {}
        }
        
        self.history.append(entry)
        
        # Auto-save minimal update for crash safety
        self._append_to_file(entry)
        
        # Print to console for immediate feedback
        print(f"   📜 [LOG Lvl {level}]: {text}")

    def _append_to_file(self, entry):
        # We read/write the whole list to keep valid JSON structure
        # (For huge logs, we would use a specialized append approach, but this is fine for now)
        with open(self.filepath, "w") as f:
            json.dump({"entries": self.history}, f, indent=2)

    def get_context(self, level=None, category=None):
        """ Used by AI to recall specific history """
        results = self.history
        if level:
            results = [e for e in results if e["level"] == level]
        if category:
            results = [e for e in results if e["category"] == category]
        return results

import json
import os
from typing import Dict, Any, Optional
from brqse_engine.models.character import Character

class GameState:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.player_state_path = os.path.join(base_dir, "Web_ui", "public", "data", "player_state.json")
        self.replay_path = os.path.join(base_dir, "Web_ui", "public", "data", "last_battle_replay.json")
        self.saves_dir = os.path.join(base_dir, "brqse_engine", "Saves")
        self.staged_config_path = os.path.join(base_dir, "Web_ui", "public", "data", "staged_battle.json")
        
        self.player_data: Dict[str, Any] = {}
        self.load_state()

    def load_state(self):
        """Loads state from disk."""
        if os.path.exists(self.player_state_path):
            try:
                with open(self.player_state_path, 'r') as f:
                    self.player_data = json.load(f)
            except Exception as e:
                print(f"Error loading player state: {e}")
                self.player_data = {}
        else:
            self.player_data = {}

    def save_state(self):
        """Saves current memory state to disk."""
        try:
            with open(self.player_state_path, 'w') as f:
                json.dump(self.player_data, f, indent=4)
        except Exception as e:
            print(f"Error saving player state: {e}")
            
    def update_player(self, data: Dict[str, Any]):
        """Updates and persists player data."""
        self.player_data.update(data)
        self.save_state()
        
    def get_player(self) -> Dict[str, Any]:
        """Loads from disk to ensure sync, then returns normalized data."""
        self.load_state() 
        if not self.player_data:
            return {}
        # Normalize via Character model
        char = Character(self.player_data)
        return char.to_dict()

    def get_replay_path(self) -> str: return self.replay_path
    def get_saves_dir(self) -> str: return self.saves_dir
    def get_staged_config_path(self) -> str: return self.staged_config_path

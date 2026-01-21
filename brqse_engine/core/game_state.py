import json
import os
from typing import Dict, Any, Optional
from brqse_engine.core.data_loader import DataLoader

class GameState:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        # Define paths relative to the base directory
        self.player_state_path = os.path.join(base_dir, "Web_ui", "public", "data", "player_state.json")
        self.replay_path = os.path.join(base_dir, "Web_ui", "public", "data", "last_battle_replay.json")
        self.saves_dir = os.path.join(base_dir, "brqse_engine", "Saves")
        self.staged_config_path = os.path.join(base_dir, "Web_ui", "public", "data", "staged_battle.json")
        
        # Initialize Data Loader (Phase B)
        self.data_loader = DataLoader(base_dir)
        
        # In-Memory State
        self.player: Dict[str, Any] = {}
        # Placeholder for other state (Map, Inventory, etc.)
        
        self.load_state()

    def load_state(self):
        """Loads state from persistence layer (JSON files)"""
        # Load Player State
        if os.path.exists(self.player_state_path):
            try:
                with open(self.player_state_path, 'r') as f:
                    self.player = json.load(f)
            except Exception as e:
                print(f"Error loading player state: {e}")
                self.player = {}
        else:
            self.player = {}

    def save_state(self):
        """Persists state to disk"""
        try:
            with open(self.player_state_path, 'w') as f:
                json.dump(self.player, f, indent=4)
        except Exception as e:
            print(f"Error saving player state: {e}")
            
    def update_player(self, data: Dict[str, Any]):
        """Updates player state and persists"""
        self.player.update(data)
        self.save_state()
        
    def get_player(self) -> Dict[str, Any]:
        """Returns the current player state"""
        return self.player

    def get_replay_path(self) -> str:
        return self.replay_path
        
    def get_saves_dir(self) -> str:
        return self.saves_dir

    def get_staged_config_path(self) -> str:
        return self.staged_config_path

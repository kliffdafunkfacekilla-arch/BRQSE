
import sys
import os
import unittest
from unittest.mock import MagicMock

# MOCK MODULES
sys.modules["brqse_engine.world.map_generator"] = MagicMock()
sys.modules["brqse_engine.world.map_generator"].MapGenerator = MagicMock()
sys.modules["brqse_engine.combat.mechanics"] = MagicMock()
sys.modules["brqse_engine.combat.mechanics"].CombatEngine = MagicMock()
sys.modules["brqse_engine.world.story_director"] = MagicMock()
sys.modules["brqse_engine.world.narrator"] = MagicMock()
sys.modules["brqse_engine.core.event_engine"] = MagicMock()
sys.modules["brqse_engine.world.campaign_logger"] = MagicMock()
sys.modules["brqse_engine.world.donjon_generator"] = MagicMock()

# Patch Constants
sys.modules["brqse_engine.world.map_generator"].TILE_WALL = 0
sys.modules["brqse_engine.world.map_generator"].TILE_FLOOR = 1
sys.modules["brqse_engine.world.map_generator"].TILE_LOOT = 6
sys.modules["brqse_engine.world.map_generator"].TILE_HAZARD = 8
sys.modules["brqse_engine.world.map_generator"].TILE_DOOR = 4
sys.modules["brqse_engine.world.map_generator"].TILE_ENTRANCE = 7
sys.modules["brqse_engine.world.map_generator"].TILE_TREE = 2
sys.modules["brqse_engine.world.map_generator"].TILE_ENEMY = 3

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from brqse_engine.core.game_loop import GameLoopController
from brqse_engine.world.world_system import ChaosManager

def run_test():
    with open("debug_skill.txt", "w") as log_file:
        try:
            print("Init Skill Check Test...", file=log_file)
            
            # Mock Sensory Layer with a side-effect to capture the prompt
            mock_sense = MagicMock()
            
            # Capture the prompt passed to consult_oracle
            captured_prompts = []
            def side_effect(prompt, message):
                captured_prompts.append(prompt)
                return "I surrender!"
            
            mock_sense.consult_oracle.side_effect = side_effect
            
            loop = GameLoopController(ChaosManager(), sensory_layer=mock_sense)
            
            # Setup Arbiter Mock to force a check
            mock_arbiter = MagicMock()
            mock_arbiter.judge_intent.return_value = {
                "check_needed": True,
                "skill": "Intimidation",
                "dc": 10,
                "reason": "Player is threatening.",
                "attribute": "Charm" # Uses charm? Sure.
            }
            # Inject Arbiter into Oracle (GameLoop -> Interaction -> Oracle -> Arbiter)
            # wait, game_loop has interaction, interaction has oracle.
            loop.interaction.oracle.arbiter = mock_arbiter
            
            # Setup Scene & NPC
            scene = MagicMock()
            scene.grid = [[1 for _ in range(20)] for _ in range(20)]
            loop.active_scene = scene
            loop.player_pos = (5, 5)
            
            npc_data = {
                "type": "Stranger", "name": "Cowardly Bandit",
                "tags": ["npc", "talk"],
                "archetype": "Coward"
            }
            loop.interactables[(6, 5)] = npc_data
            
            # Act: Talk with a threat
            print("Action: Talk (Threatening)...", file=log_file)
            loop.handle_action("talk", 6, 5, input="Drop your weapon or else!")
            
            # Assert: Check if Arbiter was called
            mock_arbiter.judge_intent.assert_called()
            print("Arbiter called: YES", file=log_file)
            
            # Assert: Check if Prompt contains SYSTEM EVENT
            latest_prompt = captured_prompts[0] if captured_prompts else ""
            if "[SYSTEM EVENT]" in latest_prompt and "Intimidation" in latest_prompt:
                print("SUCCESS: Prompt contained Skill Check Event.", file=log_file)
                print(f"Snippet: {latest_prompt[-300:]}", file=log_file)
            else:
                print("FAILURE: Prompt missing Skill Check.", file=log_file)
                print(f"Full Prompt: {latest_prompt}", file=log_file)

        except Exception as e:
            print("CRASHED:", file=log_file)
            import traceback
            traceback.print_exc(file=log_file)

if __name__ == "__main__":
    run_test()

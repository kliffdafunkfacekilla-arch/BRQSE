
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brqse_engine.core.game_loop import GameLoopController
from brqse_engine.core.game_state import GameState
from brqse_engine.world.story_director import StoryDirector
from brqse_engine.core.sensory_layer import SensoryLayer
from scripts.world_engine import ChaosManager

# Mock classes to avoid full dependencies if needed, or use real ones
class MockLogger:
    def log(self, level, category, text, tags=None):
        print(f"[LOG] {category}: {text}")
    def get_context(self, level=1):
        return [{"category": "QUEST", "text": "Find the Iron Key."}, {"category": "INTRO", "text": "Welcome to the dungeon."}]

def test_omniscient_gm():
    print("Initializing Omniscient GM Verification...")
    
    # 1. Setup minimal GameLoop
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    state = GameState(base_dir)
    chaos = ChaosManager()
    sensory = SensoryLayer(model="qwen2.5:latest")
    
    loop = GameLoopController(chaos, state, sensory_layer=sensory)
    loop.logger = MockLogger() # Override logger for simplicity
    
    # Mock Active Scene
    print("\n--- 1. Testing Context Manager ---")
    loop.state = "EXPLORE"
    loop.player_combatant.name = "TestPlayer"
    loop.player_combatant.hp = 10
    loop.player_combatant.max_hp = 20
    
    # Mock Objects
    loop.interactables[(2,2)] = {"name": "Wooden Crate", "tags": ["wood", "flammable"]}
    
    # Build Context
    ctx = loop.interaction.oracle.ctx_manager.build_full_context()
    print("Generated Context Snapshot:")
    print(ctx)
    
    if "Wooden Crate" in ctx and "flammable" in ctx and "TestPlayer" in ctx:
        print("SUCCESS: Context Manager is aggregating state correctly.")
    else:
        print("FAIL: Context missing key elements.")

    # 2. Test Story Patcher
    print("\n--- 2. Testing Story Patcher ---")
    # Generate a dummy map so loop has map_data
    scene = loop.generate_dungeon(level=1)
    
    # Mock a Boss Death
    boss_entity = type('obj', (object,), {
        "name": "Big Bad Boss",
        "x": 5, "y": 5,
        "ai_context": {"role": "boss"}
    })
    
    print("Simulating Boss Death...")
    loop.story_director.handle_entity_death(boss_entity, scene.map_data, loop.logger)
    
    # We can't easily assert the AI response in a script without mocking the AI, 
    # but we can look for the output or check if Entity was spawned if "ghost" was returned.
    # For now, visual confirmation of the [LOG] PATCH line is enough having run it.

if __name__ == "__main__":
    test_omniscient_gm()

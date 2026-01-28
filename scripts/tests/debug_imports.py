
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

print("1. Importing ChaosManager...")
try:
    from scripts.world_engine import ChaosManager
    print("   Success.")
except Exception as e:
    print(f"   FAIL: {e}")

print("2. Importing StoryDirector...")
try:
    from brqse_engine.world.story_director import StoryDirector
    print("   Success.")
except Exception as e:
    print(f"   FAIL: {e}")

print("3. Importing CampaignBuilder...")
try:
    from brqse_engine.world.campaign_builder import CampaignBuilder
    print("   Success.")
except Exception as e:
    print(f"   FAIL: {e}")

print("4. Importing GameLoopController...")
try:
    from brqse_engine.core.game_loop import GameLoopController
    print("   Success.")
except Exception as e:
    print(f"   FAIL: {e}")

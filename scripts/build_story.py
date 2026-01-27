import sys
import os
import time

# Add BRQSE root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brqse_engine.world.donjon_generator import DonjonGenerator, Cell
from brqse_engine.world.story_director import StoryDirector
from brqse_engine.world.campaign_logger import CampaignLogger

def test_pipeline():
    print("[1] Initializing Pipeline...")
    # 1. Init Components
    logger = CampaignLogger()
    dg = DonjonGenerator(seed=12345)
    director = StoryDirector(api_url="http://localhost:5001/generate")
    
    # 2. Generate Semantic Map (Donjon)
    print("[2] Generating Topology (Donjon)...")
    map_data = dg.generate(width=31, height=31)
    print(f"    - Grid Size: {map_data['width']}x{map_data['height']}")
    print(f"    - Rooms: {len(map_data['rooms'])}")
    
    # 3. Direct Scene (StoryDirector + AI)
    print("[3] Directing Scene (Calling Local AI 'http://localhost:5001/generate')...")
    start_time = time.time()
    director.direct_scene(map_data, level_depth=1, logger=logger)
    duration = time.time() - start_time
    print(f"    - Direction Time: {duration:.2f}s")
    
    # 4. Verify AI Output
    print("\n[4] Verifying Semantic Content:")
    
    theme = map_data.get("theme", "UNKNOWN")
    print(f"    - Theme: {theme}")
    
    # Check Logs for AI content
    logs = logger.get_context(level=1)
    
    has_theme = any(l["category"] == "THEME" for l in logs)
    has_quest = any(l["category"] == "QUEST" for l in logs)
    has_boss = any(l["category"] == "BOSS" for l in logs)
    has_events = any(l["category"] == "EVENT" for l in logs)
    
    print("\n[5] Logger Analysis:")
    print(f"    - Theme Logged: {'✅' if has_theme else '❌'}")
    print(f"    - Quest Logged: {'✅' if has_quest else '❌'}")
    print(f"    - Boss Logged:  {'✅' if has_boss else '❌'}")
    print(f"    - Events Logged: {'✅' if has_events else '❌'} (Count: {len([l for l in logs if l['category'] == 'EVENT'])})")
    
    # Print Sample log content
    print("\n[6] Sample Log Entries:")
    for l in logs:
        print(f"    [{l['category']}] {l['text']}")
        
    if has_theme and has_quest and has_boss:
        print("\n✅ VERIFICATION SUCCESS: The Hook is complete.")
    else:
        print("\n❌ VERIFICATION FAILED: Missing semantic data.")

if __name__ == "__main__":
    test_pipeline()

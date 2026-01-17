
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "combat simulator"))
os.environ["SDL_VIDEODRIVER"] = "dummy" # Headless pygame

try:
    import pygame
    from arena import ArenaApp
    
    print("Initializing ArenaApp...")
    pygame.init()
    # Mock display surface
    pygame.display.set_mode((1,1)) 
    
    app = ArenaApp()
    print("ArenaApp initialized successfully.")
    
    # Check if engine is linked
    if app.engine:
        print("CombatEngine linked.")
        
    print("Arena Import Test Passed.")
    
except Exception as e:
    print(f"Arena Test Failed: {e}")
    import traceback
    traceback.print_exc()

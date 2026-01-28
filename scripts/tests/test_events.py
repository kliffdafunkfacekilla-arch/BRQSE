import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from brqse_engine.world.event_manager import EventManager

mgr = EventManager()

print("🎲 Rolling 5 Random Events:")
for i in range(5):
    evt = mgr.get_random_event()
    print(f"{i+1}. [{evt['type'].upper()}] {evt['name']}: {evt['description']}")

print("\n🌀 Rolling 5 Chaos Twists:")
for i in range(5):
    evt = mgr.roll_chaos()
    print(f"{i+1}. {evt['name']}: {evt['description']}")

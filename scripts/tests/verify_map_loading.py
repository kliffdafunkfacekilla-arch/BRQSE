import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from brqse_engine.combat.enemy_spawner import spawner

LEVEL_PATH = os.path.join(os.path.dirname(__file__), '../Saves/WorldStack/level_1.json')

def verify_map():
    print(f"🔍 Checking Map: {LEVEL_PATH}")
    if not os.path.exists(LEVEL_PATH):
        print("❌ Map file not found!")
        return

    with open(LEVEL_PATH, 'r') as f:
        data = json.load(f)

    entities = data.get("entities", [])
    print(f"✅ Found {len(entities)} entities.")

    for i, ent in enumerate(entities):
        etype = ent.get("type", "UNKNOWN")
        ename = ent.get("name", "Unknown Entity")

        print(f"   [{i}] Checking {ename} ({etype})...", end="")

        try:
            # Emulate GameLoop Loading Logic
            beast_id = etype if etype.startswith("BST_") else None
            # Fallback for legacy types
            if not beast_id and "orc" in etype: beast_id = "BST_05" 
            
            # Spawn
            path = spawner.spawn_beast(beast_id=beast_id, biome="DUNGEON", level=1)
            
            if not os.path.exists(path):
                print(f" ❌ Failed to generate file at {path}")
                continue

            with open(path, 'r') as bf:
                bdata = json.load(bf)

            # Assertions
            if bdata.get("Derived", {}).get("HP", 0) <= 0:
                print(f" ❌ Invalid HP in generated file!")
                continue
            
            if "Stats" not in bdata:
                print(f" ❌ Missing Stats!")
                continue

            print(f" ✅ OK -> Spawned {bdata['Name']} (HP: {bdata['Derived']['HP']})")

        except Exception as e:
            print(f" ❌ CRITICAL ERROR: {e}")

    print("\n🎉 Verification Complete (Review errors above)")

if __name__ == "__main__":
    verify_map()

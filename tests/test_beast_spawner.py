import sys
import os
import json

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "c:/Users/krazy/Desktop/BRQSE"))

from brqse_engine.combat.enemy_spawner import spawner
from brqse_engine.world.encounter_table import EncounterTable

def test_spawner():
    print("--- Testing Beast Spawner ---")
    
    # Test Biome Filtering
    biomes = ["DUNGEON", "CAVE", "FOREST"]
    for b in biomes:
        print(f"\nRolling for Biome: {b}")
        path = spawner.spawn_beast(biome=b, level=1)
        with open(path, 'r') as f:
            data = json.load(f)
        print(f"Spawned: {data['Name']} (Species: {data['Species']})")
        print(f"Stats: {data['Stats']}")
        print(f"HP: {data['Derived']['HP']}, Speed: {data['Derived']['Speed']}")

    # Test Level Scaling
    print("\n--- Testing Level Scaling ---")
    path_l1 = spawner.spawn_beast(biome="DUNGEON", level=1)
    path_l5 = spawner.spawn_beast(biome="DUNGEON", level=5)
    
    with open(path_l1, 'r') as f: d1 = json.load(f)
    with open(path_l5, 'r') as f: d5 = json.load(f)
    
    print(f"Level 1 Might: {d1['Stats']['Might']}")
    print(f"Level 5 Might: {d5['Stats']['Might']} (Diff: {d5['Stats']['Might'] - d1['Stats']['Might']})")

if __name__ == "__main__":
    test_spawner()

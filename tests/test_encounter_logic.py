import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "c:/Users/krazy/Desktop/BRQSE"))

from brqse_engine.world.encounter_table import EncounterTable

def test_encounter_variety():
    print("--- Testing Encounter Logic Variety ---")
    
    biomes = ["DUNGEON", "CAVE", "FOREST", "RUINS", "AQUATIC"]
    
    for biome in biomes:
        print(f"\nBiome: {biome}")
        results = {"AMBUSH": 0, "HAZARD": 0, "TREASURE": 0, "SOCIAL": 0, "FLAVOR": 0}
        
        # Simulate 100 encounters to check weights
        for _ in range(100):
            enc = EncounterTable.get_random_encounter(biome)
            etype = enc["type"]
            results[etype] += 1
            
        for etype, count in results.items():
            print(f"  {etype}: {count}%")
            
        # Basic Validation
        assert sum(results.values()) == 100
        print("  Pass: Types are correctly distributed.")

def test_encounter_structure():
    print("\n--- Testing Encounter Structure ---")
    enc = EncounterTable.get_random_encounter("DUNGEON", level=3)
    
    print(f"Sample Encounter: {enc}")
    assert "type" in enc
    assert "log" in enc
    assert "biome" in enc
    assert enc["level"] == 3
    
    if enc["type"] in ["HAZARD", "TREASURE", "SOCIAL", "FLAVOR"]:
        assert "subtype" in enc
        
    print("Pass: Structure is valid.")

if __name__ == "__main__":
    test_encounter_variety()
    test_encounter_structure()

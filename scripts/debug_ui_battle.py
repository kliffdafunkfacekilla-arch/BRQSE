import json
import os
import random
import time

# CONFIG
OUTPUT_PATH = os.path.join("Web_ui", "public", "data", "last_battle_replay.json")

def generate_test_battle():
    print("--- INITIATING UI TEST PROTOCOL ---")
    
    # 1. Define Combatants (Must match your sprite filenames!)
    # We use 'Badger' and 'Beaver' because we saw them in your upload.
    c1 = {
        "name": "Badger",
        "team": "blue",
        "max_hp": 50,
        "hp": 50,
        "x": 2,
        "y": 5
    }
    
    c2 = {
        "name": "Beaver",
        "team": "red",
        "max_hp": 60,
        "hp": 60,
        "x": 7,
        "y": 5
    }
    
    combatants = [c1, c2]
    log = []
    
    # 2. Script the choreography
    # Turn 1: They approach
    log.append({"type": "move", "actor": "Badger", "from": [2,5], "to": [3,5]})
    log.append({"type": "move", "actor": "Beaver", "from": [7,5], "to": [6,5]})
    
    # Turn 2: Closer...
    log.append({"type": "move", "actor": "Badger", "from": [3,5], "to": [4,5]})
    log.append({"type": "move", "actor": "Beaver", "from": [6,5], "to": [5,5]})
    
    # Turn 3: COMBAT!
    # Badger bites Beaver
    log.append({"type": "attack", "actor": "Badger", "target": "Beaver", "damage": 12, "result": "HIT"})
    
    # Beaver slaps back
    log.append({"type": "attack", "actor": "Beaver", "target": "Badger", "damage": 8, "result": "HIT"})
    
    # Turn 4: Tactical Flanking (Testing the Facing Logic)
    # Badger moves DOWN (Should load badger_front.png)
    log.append({"type": "move", "actor": "Badger", "from": [4,5], "to": [4,6]})
    
    # Beaver turns to face him
    # (Engine doesn't explicitly send facing, UI infers it from relative position if we attack)
    log.append({"type": "attack", "actor": "Beaver", "target": "Badger", "damage": 5, "result": "HIT"})

    # Turn 5: The Kill
    log.append({"type": "attack", "actor": "Badger", "target": "Beaver", "damage": 45, "result": "CRITICAL HIT"})
    
    # 3. Export
    battle_data = {
        "combatants": combatants,
        "log": log,
        "winner": "blue"
    }
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(battle_data, f, indent=2)
        
    print(f"--> PAYLOAD DELIVERED: {OUTPUT_PATH}")
    print("--> Go to http://localhost:5173 and verify visuals.")

if __name__ == "__main__":
    generate_test_battle()

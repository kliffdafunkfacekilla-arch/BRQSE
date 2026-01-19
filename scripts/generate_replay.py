import sys
import os
import json
import random
import time

# Ensure we can find the engine modules
# We need to add the PROJECT ROOT to sys.path so we can do 'from brqse_engine...'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from brqse_engine.combat import mechanics
except ImportError:
    # Fallback/Debug
    print("Could not import brqse_engine. check your paths.")
    sys.exit(1)

def generate_visual_battle():
    # --- BURT'S TARGET LOCK ---
    # We are targeting the NEW Web_ui folder
    output_path = os.path.join("Web_ui", "public", "data", "last_battle_replay.json")
    
    # Setup paths
    saves_dir = "brqse_engine/Saves"
    
    if not os.path.exists(saves_dir):
        print(f"Error: Saves directory not found at {saves_dir}")
        print("Current working directory:", os.getcwd())
        return

    # Load characters (Simulating "Selection")
    def load_char(filename):
        try:
            with open(os.path.join(saves_dir, filename), 'r') as f:
                data = json.load(f)
                # Ensure name exists, or default it
                if "name" not in data:
                    data["name"] = f"Unknown Entity ({filename})"
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    # Try to load some test characters, or create dummies
    char1_data = load_char("buggy.json") or {
        "name": "Buggy the Clown", "stats": {"attributes": {"Might": 4, "Reflexes": 6, "Vitality": 5}},
        "derived": {"hp": 30, "speed": 25}
    }
    char2_data = load_char("flower_knight.json") or {
        "name": "Flower Knight", "stats": {"attributes": {"Might": 8, "Reflexes": 3, "Vitality": 8}},
        "derived": {"hp": 45, "speed": 20}
    }

    print(f"Loading {char1_data['name']} and {char2_data['name']}...")

    # Initialize Engine
    engine = mechanics.CombatEngine(cols=10, rows=10) # 10x10 Grid for the Arena

    # Create Combatants
    # Note: Combatant init is (filepath, data). 
    # It reads "Name" (Capitalized) from data.
    
    # Capitalize keys for engine compatibility if needed
    if "Name" not in char1_data and "name" in char1_data: char1_data["Name"] = char1_data["name"]
    if "Name" not in char2_data and "name" in char2_data: char2_data["Name"] = char2_data["name"]

    c1 = mechanics.Combatant(data=char1_data)
    c2 = mechanics.Combatant(data=char2_data)

    # Set properties manually since init doesn't take them
    c1.team = "blue"
    c2.team = "red" 
    
    # Ensure Max HP is set (Engine might calculate it, but let's be safe)
    if not hasattr(c1, 'max_hp') or c1.max_hp == 0: c1.max_hp = c1.derived.get('hp', 30)
    if not hasattr(c2, 'max_hp') or c2.max_hp == 0: c2.max_hp = c2.derived.get('hp', 30)
    c1.hp = c1.max_hp
    c2.hp = c2.max_hp

    # Place allowed (and add to engine)
    c1.x, c1.y = 2, 5
    c2.x, c2.y = 7, 5
    
    engine.add_combatant(c1, c1.x, c1.y)
    engine.add_combatant(c2, c2.x, c2.y)

    # --- SIMULATE BATTLE ---
    print("Simulating Battle...")
    
    # We will just run a few rounds to generate logs
    for _ in range(5):
        # We need to manually trigger turns if we aren't using the full game loop
        # For this demo, let's just force some actions
        
        # 1. Move Blue
        engine.move_char(c1, c1.x + random.choice([-1, 0, 1]), c1.y + random.choice([-1, 0, 1]))
        
        # 2. Blue Attacks Red
        engine.attack_target(c1, c2)
        
        # 3. Move Red
        engine.move_char(c2, c2.x + random.choice([-1, 0, 1]), c2.y + random.choice([-1, 0, 1]))
        
        # 4. Red Attacks Blue
        engine.attack_target(c2, c1)

    # --- EXPORT DATA ---
    battle_data = {
        "combatants": [
            {"name": c1.name, "max_hp": c1.max_hp, "team": "blue"},
            {"name": c2.name, "max_hp": c2.max_hp, "team": "red"}
        ],
        "log": engine.replay_log
    }

    # Verify we have data
    print(f"Generated {len(engine.replay_log)} events.")

    # Save to Web Public Folder
    # BURT NOTE: This path needs to be correct relative to where you run the script!
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(battle_data, f, indent=2)
        
    print(f"--> TACTICAL DATA DROP: {output_path}")
    print("--> UI STATUS: READY FOR PLAYBACK")

if __name__ == "__main__":
    generate_visual_battle()

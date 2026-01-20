import sys
import os
import json
import time
import random
import glob

# Add root folder to sys.path so we can import 'brqse_engine'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from brqse_engine.combat.mechanics import CombatEngine, Combatant

def generate_replay():
    print("Initializing Battle Simulation...")
    
    # OUTPUT PATH (Direct to Web App)
    output_path = os.path.join("Web_ui", "public", "data", "last_battle_replay.json")

    # Initialize Engine
    engine = CombatEngine(cols=10, rows=10)
    
    # Load Characters (from Saves)
    # Check current directory context. Assuming run from root or via simple relative paths.
    save_dir = os.path.join("brqse_engine", "Saves")
    
    # Fallback paths if running from scripts folder
    if not os.path.exists(save_dir) and os.path.exists(os.path.join("..", "brqse_engine", "Saves")):
        save_dir = os.path.join("..", "brqse_engine", "Saves")

    # Random Selection Logic
    save_files = glob.glob(os.path.join(save_dir, "*.json"))
    if len(save_files) >= 2:
        f1, f2 = random.sample(save_files, 2)
        print(f"Selected Fighters: {os.path.basename(f1)} vs {os.path.basename(f2)}")
        p1 = Combatant(filepath=f1)
        p2 = Combatant(filepath=f2)
    else:
        # Load Blaze and Iron Default
        print("Not enough saves found. Defaulting to Blaze vs Iron.")
        p1 = Combatant(filepath=os.path.join(save_dir, "Blaze.json"))
        p2 = Combatant(filepath=os.path.join(save_dir, "Iron.json"))
    
    # If loading failed (empty data), inject defaults
    if not p1.name or p1.name == "Unknown":
        print("Warning: Could not load Blaze.json, using fallback.")
        p1.name = "Blaze"
        p1.max_hp = 100
        p1.hp = 100
        p1.stats = {"Might": 16, "Reflexes": 14, "Vitality": 14, "Knowledge": 10}
        p1.powers = ["Fireball", "Flame Strike"] # Give some spells
        
    if not p2.name or p2.name == "Unknown":
        print("Warning: Could not load Iron.json, using fallback.")
        p2.name = "Iron"
        p2.max_hp = 120
        p2.hp = 120
        p2.stats = {"Might": 18, "Reflexes": 10, "Vitality": 18, "Willpower": 14}
        p2.powers = ["Stone Skin", "Earthquake"]

    # Assign Teams and Positions
    p1.team = "blue"
    p2.team = "red"
    
    engine.add_combatant(p1, 2, 5)  # Left
    engine.add_combatant(p2, 7, 5)  # Right
    
    # Setup Map (Simple Arena)
    walls = [(2,2), (2,7), (7,2), (7,7)]
    for wx, wy in walls:
        engine.create_wall(wx, wy)
        
    map_tiles = [["floor_stone" for _ in range(10)] for _ in range(10)]
    for wx, wy in walls:
        map_tiles[wy][wx] = "wall_stone"

    # Start Combat
    print("Starting Combat Loop...")
    engine.start_combat()
    
    # Limit rounds to prevent infinite loops
    MAX_ROUNDS = 20
    round_count = 0
    
    while round_count < MAX_ROUNDS and p1.is_alive() and p2.is_alive():
        # Get active character
        active = engine.get_active_char()
        
        # Execute AI Turn
        # This will call move, attack, ability, etc. and populate engine.replay_log
        log = engine.execute_ai_turn(active)
        
        # End Turn (Rotation)
        engine.end_turn()
        
        # Check if round rolled over (idx reset)
        if engine.current_turn_index == 0:
            round_count += 1
            print(f"Round {round_count} complete.")

    print(f"Simulation ended after {round_count} rounds.")
    print(f"Winner: {p1.name if p1.is_alive() else p2.name}")
    print(f"Total Events: {len(engine.replay_log)}")

    # Construct Final JSON
    # Include 'x' and 'y' in combatants so the UI places them correctly at start
    final_data = {
        "combatants": [
            {
                "name": c.name, 
                "max_hp": c.max_hp, 
                "hp": c.hp, # Final HP (maybe UI wants Max to start? UI resets hp to max_hp usually)
                # Actually, UI resets to max_hp on load. So this is fine.
                "team": c.team,
                "x": 2 if c == p1 else 7, # Start positions
                "y": 5
            } for c in engine.combatants
        ],
        "log": engine.replay_log,
        "map": map_tiles
    }
    
    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(final_data, f, indent=2)
        
    print(f"Replay saved to: {output_path}")

if __name__ == "__main__":
    generate_replay()

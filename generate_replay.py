import sys
import os
import json
import random
import time

# Ensure project root is in path
sys.path.append(os.getcwd())

from brqse_engine.combat import mechanics

def generate_visual_battle():
    # Setup paths
    saves_dir = "brqse_engine/Saves"
    # BURT NOTE: This dumps the "Network Packet" directly to your web folder
    output_path = "web-character-creator/public/data/last_battle_replay.json"
    
    if not os.path.exists(saves_dir):
        print(f"Error: Saves directory not found at {saves_dir}")
        return

    saves = [f for f in os.listdir(saves_dir) if f.endswith('.json')]
    if len(saves) < 2: 
        print(f"Not enough fighters in {saves_dir}.")
        return

    # Pick Fighters
    # Ensure bug or flower are in there if possible for fun
    preferred = [f for f in saves if "buggy" in f.lower() or "flower" in f.lower()]
    others = [f for f in saves if f not in preferred]
    
    if len(preferred) >= 2:
        f1_file, f2_file = random.sample(preferred, 2)
    elif len(preferred) == 1 and others:
        f1_file = preferred[0]
        f2_file = random.choice(others)
    else:
        f1_file, f2_file = random.sample(saves, 2)

    print(f"Loading {f1_file} and {f2_file}...")
    f1 = mechanics.Combatant(filepath=os.path.join(saves_dir, f1_file))
    f2 = mechanics.Combatant(filepath=os.path.join(saves_dir, f2_file))
    
    # Tag them for the UI
    f1.name = f1.name + " (Blue)"
    f2.name = f2.name + " (Red)"
    f1.team = "blue"
    f2.team = "red"

    # Setup Arena
    engine = mechanics.CombatEngine(cols=10, rows=10)
    engine.add_combatant(f1, 2, 5) # Left side
    engine.add_combatant(f2, 7, 5) # Right side
    engine.start_combat()

    print(f"Simulating: {f1.name} vs {f2.name}...")

    # Run Loop (Simplified for Data Generation)
    turns = 0
    while f1.is_alive() and f2.is_alive() and turns < 20:
        turns += 1
        # Simple round logic
        # We need to manually cycle to mimic engine loop if we aren't using simulation_runner
        # But mechanics.py doesn't have a 'play round' method, just turns.
        
        # We iterate turn_order
        # Note: logic inside mechanics handles turn indexing
        # Just call start_turn -> execute_ai -> end_turn
        
        active = engine.get_active_char()
        if not active.is_alive(): 
            engine.end_turn()
            continue

        engine.start_turn(active)
        engine.execute_ai_turn(active)
        if engine.clash_active: engine.resolve_clash("Aggressive")
        engine.end_turn()

    # The "Game State" Packet
    battle_data = {
        "combatants": [
            {"name": f1.name, "species": f1.species, "max_hp": f1.max_hp, "team": "blue"},
            {"name": f2.name, "species": f2.species, "max_hp": f2.max_hp, "team": "red"}
        ],
        "log": engine.replay_log # This is the sequence the frontend will render
    }

    # Save to Web Public Folder
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(battle_data, f, indent=2)
    
    print(f"Battle Data saved to {output_path}! ({len(engine.replay_log)} events)")

if __name__ == "__main__":
    generate_visual_battle()

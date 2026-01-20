import sys
import os
import json
import random
import glob

# Add root folder to sys.path so we can import 'brqse_engine'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from brqse_engine.combat.mechanics import CombatEngine, Combatant

def generate_replay():
    print("Initializing Battle Simulation...")
    
    # PATHS
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    output_path = os.path.join(base_dir, "Web_ui", "public", "data", "last_battle_replay.json")
    player_state_path = os.path.join(base_dir, "Web_ui", "public", "data", "player_state.json")
    save_dir = os.path.join(base_dir, "brqse_engine", "Saves")

    # Initialize Engine
    engine = CombatEngine(cols=10, rows=10)
    
    # --- LOAD PLAYER STATE ---
    player_data = None
    if os.path.exists(player_state_path):
        try:
            with open(player_state_path, 'r') as f:
                player_data = json.load(f)
            print(f"Loaded player state: {player_data.get('name', 'Unknown')}")
        except Exception as e:
            print(f"Warning: Could not load player state: {e}")
    
    # --- CREATE PLAYER COMBATANT ---
    if player_data:
        # Create combatant with player's equipment
        p1 = Combatant()  # Empty init
        p1.name = player_data.get("name", "Hero")
        p1.data = {
            "Name": p1.name,
            "Species": player_data.get("species", "Mammal"),
            "Stats": player_data.get("stats", {}),
            "Skills": player_data.get("skills", []),
            "Powers": player_data.get("powers", []),
            "Inventory": [],  # Will add equipped items
            "Gear": []
        }
        
        # Add equipped items to inventory for the engine to equip
        equipment = player_data.get("equipment", {})
        for slot, item in equipment.items():
            if item != "Empty":
                p1.data["Inventory"].append(item)
                print(f"  Equipping: {item} -> {slot}")
        
        # Re-initialize from data
        p1.stats = p1.data.get("Stats", {})
        p1.powers = p1.data.get("Powers", [])
        p1.skills = p1.data.get("Skills", [])
        p1.traits = p1.data.get("Traits", [])
        
        # Calculate derived stats
        def get_score(name): return p1.stats.get(name, 10)
        p1.max_hp = 10 + get_score("Might") + get_score("Reflexes") + get_score("Vitality")
        p1.hp = p1.max_hp
        p1.max_cmp = 10 + get_score("Willpower") + get_score("Logic") + get_score("Awareness")
        p1.cmp = p1.max_cmp
        p1.max_sp = get_score("Endurance") + get_score("Finesse") + get_score("Fortitude")
        p1.sp = p1.max_sp
        p1.max_fp = get_score("Knowledge") + get_score("Charm") + get_score("Intuition")
        p1.fp = p1.max_fp
        
        # Movement
        raw_speed = get_score("Vitality") + get_score("Willpower")
        p1.base_movement = int(5 * round(raw_speed / 5))
        if p1.base_movement < 5: p1.base_movement = 5
        p1.movement = p1.base_movement
        p1.movement_remaining = p1.movement
        
        # Init flags
        p1.action_used = False
        p1.bonus_action_used = False
        p1.reaction_used = False
        p1.active_effects = []
        p1.x = 0
        p1.y = 0
        p1.initiative = 0
        p1.team = "Neutral"
        
        print(f"Player HP: {p1.max_hp}, Powers: {p1.powers}")
    else:
        # Fallback to random save file
        save_files = glob.glob(os.path.join(save_dir, "*.json"))
        if save_files:
            f1 = random.choice(save_files)
            print(f"No player state, using: {os.path.basename(f1)}")
            p1 = Combatant(filepath=f1)
        else:
            print("No saves found. Creating default player.")
            p1 = Combatant()
            p1.name = "Hero"
            p1.max_hp = 100
            p1.hp = 100
    
    # --- LOAD ENEMY ---
    save_files = glob.glob(os.path.join(save_dir, "*.json"))
    # Pick random enemy that's not the player
    enemy_files = [f for f in save_files if os.path.basename(f).lower() != f"{p1.name.lower()}.json"]
    
    if enemy_files:
        f2 = random.choice(enemy_files)
        print(f"Enemy: {os.path.basename(f2)}")
        p2 = Combatant(filepath=f2)
    else:
        print("No enemy saves found. Creating default enemy.")
        p2 = Combatant()
        p2.name = "Enemy"
        p2.max_hp = 80
        p2.hp = 80

    # Assign Teams and Positions
    p1.team = "blue"
    p2.team = "red"
    
    engine.add_combatant(p1, 2, 5)  # Left
    engine.add_combatant(p2, 7, 5)  # Right
    
    # Setup Map
    walls = [(2,2), (2,7), (7,2), (7,7)]
    for wx, wy in walls:
        engine.create_wall(wx, wy)
        
    map_tiles = [["floor_stone" for _ in range(10)] for _ in range(10)]
    for wx, wy in walls:
        map_tiles[wy][wx] = "wall_stone"

    # Start Combat
    print("Starting Combat Loop...")
    engine.start_combat()
    
    MAX_ROUNDS = 20
    round_count = 0
    
    while round_count < MAX_ROUNDS and p1.is_alive() and p2.is_alive():
        active = engine.get_active_char()
        engine.execute_ai_turn(active)
        engine.end_turn()
        
        if engine.current_turn_index == 0:
            round_count += 1
            print(f"Round {round_count} complete.")

    print(f"Simulation ended after {round_count} rounds.")
    print(f"Winner: {p1.name if p1.is_alive() else p2.name}")
    print(f"Total Events: {len(engine.replay_log)}")

    # Construct Final JSON
    final_data = {
        "combatants": [
            {
                "name": c.name, 
                "max_hp": c.max_hp, 
                "hp": c.hp,
                "team": c.team,
                "x": 2 if c == p1 else 7,
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

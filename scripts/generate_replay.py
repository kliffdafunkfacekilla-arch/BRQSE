import sys
import os
import json
import glob
import random

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from brqse_engine.core.game_state import GameState
from brqse_engine.core.data_loader import DataLoader
from brqse_engine.models.character import Character
from brqse_engine.combat.mechanics import CombatEngine
from brqse_engine.combat.combatant import Combatant
from brqse_engine.combat.simple_ai import SimpleAI

def generate_replay():
    print("Initializing Battle Simulation (Phase D Engine)...")
    
    # 1. Initialize State & Data
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    game_state = GameState(base_dir)
    data_loader = game_state.data_loader
    
    # 2. Setup Combat Engine
    engine = CombatEngine(cols=12, rows=12)
    
    # DEMO: Add Random Hazards
    print("Generating Hazards...")
    hazards = ["fire", "ice", "mud", "water_deep", "water_shallow", "wall_stone", "tree"]
    for _ in range(25): # Add more tiles to show off assets
        hx = random.randint(0, 11)
        hy = random.randint(0, 11)
        h_type = random.choice(hazards)
        if (hx, hy) not in [(2,6), (9,6)]: # Don't spawn on start (roughly)
            engine.set_terrain(hx, hy, h_type)
            if h_type == "wall_stone":
                engine.create_wall(hx, hy)
    
    # 3. Load Characters
    # Player
    player_data = game_state.get_player()
    if not player_data:
        print("No Player State found.")
        return

    # Create Player Character
    # Hydrate using data loader if needed, though GameState might have raw dict
    # Assuming player_data is compatible with Character constructor
    # Map 'stats' key to 'Stats' if case differs
    if "stats" in player_data: player_data["Stats"] = player_data["stats"]
    if "skills" in player_data: player_data["Skills"] = player_data["skills"]
    if "name" in player_data: player_data["Name"] = player_data["name"]
    if "species" in player_data: player_data["Species"] = player_data["species"]
    
    hero = Character(player_data)
    c_hero = Combatant(hero, x=2, y=6, team="Blue")
    engine.add_combatant(c_hero)
    print(f"Added Hero: {hero.name} (HP: {hero.current_hp})")

    # Enemy (Random from Saves)
    saves_dir = game_state.get_saves_dir()
    save_files = glob.glob(os.path.join(saves_dir, "*.json"))
    enemy_files = [f for f in save_files if os.path.basename(f).lower() != f"{hero.name.lower()}.json"]
    
    if enemy_files:
        path = random.choice(enemy_files)
        with open(path, 'r') as f:
            enemy_data = json.load(f)
        
        enemy = Character(enemy_data)
        c_enemy = Combatant(enemy, x=9, y=6, team="Red")
        engine.add_combatant(c_enemy)
        print(f"Added Enemy: {enemy.name} (HP: {enemy.current_hp})")
    else:
        print("No enemy saves found. Creating Default Enemy (Sniper).")
        default_data = {
            "Name": "Goblin Sniper", 
            "Stats": {"Reflexes": 14, "Might": 8}, 
            "Current_HP": 30,
            "AI_Archetype": "Sniper",
            "Sprite": "token_goblin_archer" # Assuming this exists or falls back
        }
        enemy = Character(default_data)
        # Spawn closer to force kiting logic (Range < 3)
        c_enemy = Combatant(enemy, x=3, y=6, team="Red") 
        engine.add_combatant(c_enemy)

    # 4. Start Combat
    engine.start_combat()
    
    # CAPTURE INITIAL STATE
    initial_combatants = []
    for c in engine.combatants:
        initial_combatants.append({
            "name": c.name,
            "max_hp": c.max_hp,
            "hp": c.current_hp,
            "team": c.team,
            "x": c.x,
            "y": c.y,
            "sprite": c.sprite or "wolf"
        })
    
    # 5. Simulation Loop
    MAX_ROUNDS = 20
    round_count = 0
    
    while round_count < MAX_ROUNDS:
        active = engine.get_active_char()
        
        # Check Win Condition
        blue_alive = any(c.is_alive for c in engine.combatants if c.team == "Blue")
        red_alive = any(c.is_alive for c in engine.combatants if c.team == "Red")
        
        if not blue_alive or not red_alive:
            break

        # AI Turn Execution
        if getattr(active, "is_alive", True): # Check if active is alive
            SimpleAI.execute_turn(active, engine)
        
        engine.end_turn()
        if engine.current_turn_index == 0:
            round_count += 1

    # 6. Export Replay
    output_path = game_state.get_replay_path()
    
    winner = "Blue Team" if any(c.is_alive and c.team == "Blue" for c in engine.combatants) else "Red Team"
    
    # Format for Frontend (preserving schema)
    # Frontend expects: combatants (list), log (list of strings), map (2d array), winner
    
    map_tiles = []
    for y in range(engine.rows):
        row = []
        for x in range(engine.cols):
            tile = engine.tiles[y][x]
            if (x, y) in engine.walls:
                row.append("wall_stone")
            else:
                 row.append(tile.terrain)
        map_tiles.append(row)
    
    
    # Use captured initial state for combatant display start
    combatant_data = initial_combatants

    final_data = {
        "combatants": combatant_data,
        "log": engine.replay_log,
        "map": map_tiles,
        "winner": winner
    }

    with open(output_path, 'w') as f:
        json.dump(final_data, f, indent=2)
    
    print(f"Replay generated: {output_path}")

if __name__ == "__main__":
    generate_replay()

import sys
import os
import json
import random
import glob

# Add root folder to sys.path so we can import 'brqse_engine'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from brqse_engine.combat.mechanics import CombatEngine, Combatant

def load_combatant_from_save(save_dir, name):
    """Load a combatant from a save file by name."""
    filepath = os.path.join(save_dir, f"{name}.json")
    if os.path.exists(filepath):
        return Combatant(filepath=filepath)
    # Try case-insensitive match
    for f in glob.glob(os.path.join(save_dir, "*.json")):
        if os.path.basename(f).lower() == f"{name.lower()}.json":
            return Combatant(filepath=f)
    return None

def generate_staged_replay(config):
    """Generate a battle with custom teams and terrain."""
    print("Initializing STAGED Battle Simulation...")
    
    # PATHS
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    output_path = os.path.join(base_dir, "Web_ui", "public", "data", "last_battle_replay.json")
    save_dir = os.path.join(base_dir, "brqse_engine", "Saves")
    
    # Get team configs
    blue_team_names = config.get("blue_team", [])
    red_team_names = config.get("red_team", [])
    terrain_config = config.get("terrain", [])
    
    print(f"Blue Team: {blue_team_names}")
    print(f"Red Team: {red_team_names}")
    print(f"Terrain tiles: {len(terrain_config)}")
    
    # Initialize Engine
    engine = CombatEngine(cols=12, rows=12)
    
    # Apply terrain
    for tile in terrain_config:
        x, y, t_type = tile.get("x", 0), tile.get("y", 0), tile.get("type", "normal")
        engine.set_terrain(x, y, t_type)
        print(f"  Terrain: {t_type} at ({x}, {y})")
    
    # Load Blue Team
    blue_combatants = []
    for i, name in enumerate(blue_team_names):
        c = load_combatant_from_save(save_dir, name)
        if c:
            c.team = "blue"
            # Position on left side, spread vertically
            x = 1
            y = 3 + i * 2  # Spread out
            if y >= 11: y = 11
            engine.add_combatant(c, x, y)
            c.facing = "E"  # Face right
            blue_combatants.append(c)
            print(f"  Blue: {c.name} at ({x}, {y})")
        else:
            print(f"  Warning: Could not load '{name}'")
    
    # Load Red Team  
    red_combatants = []
    for i, name in enumerate(red_team_names):
        c = load_combatant_from_save(save_dir, name)
        if c:
            c.team = "red"
            # Position on right side, spread vertically
            x = 10
            y = 3 + i * 2
            if y >= 11: y = 11
            engine.add_combatant(c, x, y)
            c.facing = "W"  # Face left
            red_combatants.append(c)
            print(f"  Red: {c.name} at ({x}, {y})")
        else:
            print(f"  Warning: Could not load '{name}'")
    
    if not blue_combatants or not red_combatants:
        print("ERROR: One or both teams have no valid combatants!")
        return None
    
    # Setup basic map tiles
    map_tiles = [["floor_stone" for _ in range(12)] for _ in range(12)]
    
    # Mark terrain on map
    for tile in terrain_config:
        x, y, t_type = tile.get("x", 0), tile.get("y", 0), tile.get("type", "normal")
        if 0 <= x < 12 and 0 <= y < 12:
            if t_type == "fire":
                map_tiles[y][x] = "fire"
            elif t_type == "water_shallow":
                map_tiles[y][x] = "water"
            elif t_type == "ice":
                map_tiles[y][x] = "ice"
            elif t_type in ["difficult", "mud"]:
                map_tiles[y][x] = "rubble"
    
    # Start Combat
    print("Starting Combat Loop...")
    engine.start_combat()
    
    MAX_ROUNDS = 30
    round_count = 0
    
    def any_alive(team):
        return any(c.is_alive() for c in (blue_combatants if team == "blue" else red_combatants))
    
    while round_count < MAX_ROUNDS and any_alive("blue") and any_alive("red"):
        active = engine.get_active_char()
        if active and active.is_alive():
            engine.execute_ai_turn(active)
        engine.end_turn()
        
        if engine.current_turn_index == 0:
            round_count += 1
            blue_alive = sum(1 for c in blue_combatants if c.is_alive())
            red_alive = sum(1 for c in red_combatants if c.is_alive())
            print(f"Round {round_count}: Blue={blue_alive}, Red={red_alive}")
    
    # Determine winner
    blue_alive = any_alive("blue")
    red_alive = any_alive("red")
    winner = "Blue Team" if blue_alive else ("Red Team" if red_alive else "Draw")
    
    print(f"Simulation ended after {round_count} rounds.")
    print(f"Winner: {winner}")
    print(f"Total Events: {len(engine.replay_log)}")
    
    # Available sprites for fallback
    FALLBACK_SPRITES = ["badger", "beaver", "wolf", "fox", "bear", "tiger", "mouse", "squirrel", "rabbit_blue", "racoon", "elephant", "horse"]
    
    # Construct Final JSON with sprite info
    combatant_data = []
    for i, c in enumerate(engine.combatants):
        # Try to get sprite from character data, otherwise use fallback
        sprite = getattr(c, 'data', {}).get("Sprite", None)
        if not sprite:
            # Use a consistent fallback based on index
            sprite = FALLBACK_SPRITES[i % len(FALLBACK_SPRITES)]
        combatant_data.append({
            "name": c.name,
            "max_hp": c.max_hp,
            "hp": c.hp,
            "team": c.team,
            "x": c.x,
            "y": c.y,
            "sprite": sprite
        })
    
    final_data = {
        "combatants": combatant_data,
        "log": engine.replay_log,
        "map": map_tiles,
        "winner": winner
    }
    
    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(final_data, f, indent=2)
    
    print(f"Replay saved to: {output_path}")
    return final_data


def generate_replay():
    """Original random battle generation."""
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
        p1 = Combatant()
        p1.name = player_data.get("name", "Hero")
        p1.data = {
            "Name": p1.name,
            "Species": player_data.get("species", "Mammal"),
            "Stats": player_data.get("stats", {}),
            "Skills": player_data.get("skills", []),
            "Powers": player_data.get("powers", []),
            "Inventory": [],
            "Gear": []
        }
        
        equipment = player_data.get("equipment", {})
        for slot, item in equipment.items():
            if item != "Empty":
                p1.data["Inventory"].append(item)
                print(f"  Equipping: {item} -> {slot}")
        
        p1.stats = p1.data.get("Stats", {})
        p1.powers = p1.data.get("Powers", [])
        p1.skills = p1.data.get("Skills", [])
        p1.traits = p1.data.get("Traits", [])
        
        def get_score(name): return p1.stats.get(name, 10)
        p1.max_hp = 10 + get_score("Might") + get_score("Reflexes") + get_score("Vitality")
        p1.hp = p1.max_hp
        p1.max_cmp = 10 + get_score("Willpower") + get_score("Logic") + get_score("Awareness")
        p1.cmp = p1.max_cmp
        p1.max_sp = get_score("Endurance") + get_score("Finesse") + get_score("Fortitude")
        p1.sp = p1.max_sp
        p1.max_fp = get_score("Knowledge") + get_score("Charm") + get_score("Intuition")
        p1.fp = p1.max_fp
        
        raw_speed = get_score("Vitality") + get_score("Willpower")
        p1.base_movement = int(5 * round(raw_speed / 5))
        if p1.base_movement < 5: p1.base_movement = 5
        p1.movement = p1.base_movement
        p1.movement_remaining = p1.movement
        
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

    p1.team = "blue"
    p2.team = "red"
    
    engine.add_combatant(p1, 2, 5)
    engine.add_combatant(p2, 7, 5)
    
    walls = [(2,2), (2,7), (7,2), (7,7)]
    for wx, wy in walls:
        engine.create_wall(wx, wy)
        
    map_tiles = [["floor_stone" for _ in range(10)] for _ in range(10)]
    for wx, wy in walls:
        map_tiles[wy][wx] = "wall_stone"

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
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(final_data, f, indent=2)
        
    print(f"Replay saved to: {output_path}")


if __name__ == "__main__":
    # Check for --staged flag
    if "--staged" in sys.argv:
        # Load staged config
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        config_path = os.path.join(base_dir, "Web_ui", "public", "data", "staged_battle.json")
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            generate_staged_replay(config)
        else:
            print(f"ERROR: Staged config not found at {config_path}")
            sys.exit(1)
    else:
        generate_replay()

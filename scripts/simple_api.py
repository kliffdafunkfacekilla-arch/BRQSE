"""
Simple API Server for BRQSE
Handles player state sync and battle generation.

Run with: python scripts/simple_api.py
Runs on: http://localhost:5001
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import subprocess
import sys
import glob

# Import GameState
# Ensure parent dir is in path to import brqse_engine
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from brqse_engine.core.game_state import GameState

app = Flask(__name__)
CORS(app)  # Allow requests from Vite dev server

# Initialize GameState
GAME_STATE = GameState(BASE_DIR)

# --- PLAYER STATE ---

@app.route('/api/player', methods=['GET'])
def get_player():
    """Returns current player state"""
    return jsonify(GAME_STATE.get_player())

@app.route('/api/player', methods=['POST'])
def update_player():
    """Updates player state (equipment, inventory, etc)"""
    try:
        data = request.get_json()
        GAME_STATE.update_player(data)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- CHARACTERS ---

@app.route('/api/characters', methods=['GET'])
def list_characters():
    """Returns list of available characters from Saves folder"""
    try:
        saves_dir = GAME_STATE.get_saves_dir()
        pattern = os.path.join(saves_dir, "*.json")
        files = glob.glob(pattern)
        characters = []
        for f in files:
            name = os.path.splitext(os.path.basename(f))[0]
            # Load character data for preview
            try:
                with open(f, 'r') as fp:
                    data = json.load(fp)
                    characters.append({
                        "name": name,
                        "species": data.get("Species", "Unknown"),
                        "skills": len(data.get("Skills", [])),
                        "powers": len(data.get("Powers", []))
                    })
            except:
                characters.append({"name": name, "species": "Unknown"})
        return jsonify({"characters": characters})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- BATTLE ---

@app.route('/api/battle', methods=['POST'])
def run_battle():
    """Runs generate_replay.py and returns the new replay"""
    try:
        # Run the replay generator
        script_path = os.path.join(BASE_DIR, "scripts", "generate_replay.py")
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return jsonify({
                "error": "Battle generation failed",
                "stderr": result.stderr
            }), 500
        
        # Return the new replay
        with open(GAME_STATE.get_replay_path(), 'r') as f:
            return jsonify(json.load(f))
            
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Battle timed out"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/battle/staged', methods=['POST'])
def run_staged_battle():
    """Runs a staged battle with custom teams and terrain"""
    try:
        config = request.get_json()
        
        # Validate required fields
        blue_team = config.get("blue_team", [])
        red_team = config.get("red_team", [])
        
        if not blue_team or not red_team:
            return jsonify({"error": "Both teams must have at least one character"}), 400
        
        # Save config for generate_replay.py to read
        with open(GAME_STATE.get_staged_config_path(), 'w') as f:
            json.dump(config, f, indent=2)
        
        # Run the replay generator with --staged flag
        script_path = os.path.join(BASE_DIR, "scripts", "generate_replay.py")
        result = subprocess.run(
            [sys.executable, script_path, "--staged"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=60  # More time for multi-character battles
        )
        
        if result.returncode != 0:
            return jsonify({
                "error": "Staged battle failed",
                "stderr": result.stderr,
                "stdout": result.stdout
            }), 500
        
        # Return the new replay
        with open(GAME_STATE.get_replay_path(), 'r') as f:
            return jsonify(json.load(f))
            
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Battle timed out"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- CHARACTER CREATION ---

@app.route('/api/character/save', methods=['POST'])
def save_character():
    """Saves a new character to the Saves folder"""
    try:
        data = request.get_json()
        name = data.get("Name", "Unnamed")
        
        # Clean name for filename
        safe_name = "".join(c for c in name if c.isalnum() or c in "_ -").strip()
        if not safe_name:
            safe_name = "Unnamed"
        
        filepath = os.path.join(GAME_STATE.get_saves_dir(), f"{safe_name}.json")
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return jsonify({"status": "ok", "path": filepath})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- HEALTH CHECK ---

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "online", "version": "2.2 (Phase B: AI Narration)"})

# --- WORLD ENGINE (Chaos/Tension/Atmosphere) ---

from scripts.world_engine import ChaosManager, SceneStack

# Global world state (will be initialized per session in future)
CHAOS_MANAGER = ChaosManager()
SCENE_STACK = SceneStack(CHAOS_MANAGER)

@app.route('/api/world/status', methods=['GET'])
def world_status():
    """Returns current chaos, tension, and atmosphere state."""
    return jsonify({
        "chaos_level": CHAOS_MANAGER.chaos_level,
        "chaos_clock": CHAOS_MANAGER.chaos_clock,
        "tension_threshold": CHAOS_MANAGER.tension_threshold,
        "is_doomed": CHAOS_MANAGER.is_doomed,
        "atmosphere": CHAOS_MANAGER.get_atmosphere()
    })

@app.route('/api/world/tension/roll', methods=['POST'])
def roll_tension():
    """Rolls the tension die. Returns EVENT, CHAOS_EVENT, or SAFE."""
    result = CHAOS_MANAGER.roll_tension()
    return jsonify({
        "result": result,
        "chaos_clock": CHAOS_MANAGER.chaos_clock,
        "tension_threshold": CHAOS_MANAGER.tension_threshold,
        "atmosphere": CHAOS_MANAGER.get_atmosphere()
    })

@app.route('/api/world/quest/generate', methods=['POST'])
def generate_quest():
    """Generates a new quest stack."""
    SCENE_STACK.generate_quest()
    return jsonify({
        "stack_size": len(SCENE_STACK.stack),
        "chaos_level": CHAOS_MANAGER.chaos_level
    })

@app.route('/api/world/scene/advance', methods=['POST'])
def advance_scene():
    """Advances to the next scene in the stack."""
    # Use GameLoop to ensure map is generated
    scene = GAME_LOOP.advance_scene()
    
    return jsonify({
        "text": scene.text,
        "encounter_type": scene.encounter_type,
        "enemy_data": scene.enemy_data,
        "remaining": len(SCENE_STACK.stack),
        "atmosphere": CHAOS_MANAGER.get_atmosphere()
    })


# --- GAME LOOP (Exploration/Combat Controller) ---

from brqse_engine.core.game_loop import GameLoopController

# Initialize one global controller for the session
GAME_LOOP = GameLoopController(CHAOS_MANAGER)

@app.route('/api/game/init', methods=['POST'])
def game_init():
    """Starts a new game session/quest."""
    # Reset controller
    global GAME_LOOP
    GAME_LOOP = GameLoopController(CHAOS_MANAGER)
    return jsonify(GAME_LOOP.get_state())

@app.route('/api/game/state', methods=['GET'])
def game_state():
    """Returns current board state (walls, objects, player pos)."""
    return jsonify(GAME_LOOP.get_state())

@app.route('/api/game/move', methods=['POST'])
def game_move():
    """Attempts to move player. Returns success/fail and events."""
    data = request.get_json()
    
    # Extract Player Traits (Prototype Mapping)
    player = GAME_STATE.get_player()
    traits = []
    species = player.get('species', "")
    
    if species == 'Avian': traits.append('Wings')
    elif species == 'Reptile': traits.append('Sticky Pads')
    elif species == 'Mammal' or species == 'Bear': traits.append('Huge Size')
    
    result = GAME_LOOP.handle_move(data.get('x'), data.get('y'), traits=traits)
    
    # Enrich result with full state update
    response = {
        "result": result,
        "state": GAME_LOOP.get_state(),
        "tension": {
            "threshold": CHAOS_MANAGER.tension_threshold,
            "chaos_clock": CHAOS_MANAGER.chaos_clock
        }
    }
    return jsonify(response)

@app.route('/api/game/interact', methods=['POST'])
def game_interact():
    """Interacts with object at target."""
    data = request.get_json()
    result = GAME_LOOP.handle_interact(data.get('x'), data.get('y'))
    return jsonify({
        "result": result,
        "state": GAME_LOOP.get_state()
    })

if __name__ == '__main__':
    print("=" * 50)
    print("BRQSE API Server v2.3 (Game Loop Integrated)")
    print(f"Base Dir: {BASE_DIR}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5001, debug=True)

"""
Simple API Server for BRQSE
Updated to support d12 Action-based Tension and Contextual Actions.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import glob
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from brqse_engine.core.game_state import GameState

app = Flask(__name__)
CORS(app)

GAME_STATE = GameState(BASE_DIR)

# --- WORLD & LOOP ---
from scripts.world_engine import ChaosManager
from brqse_engine.core.game_loop import GameLoopController

CHAOS_MANAGER = ChaosManager()
GAME_LOOP = GameLoopController(CHAOS_MANAGER, GAME_STATE)

@app.route('/api/player', methods=['GET'])
def get_player(): return jsonify(GAME_STATE.get_player())

@app.route('/api/player', methods=['POST'])
def update_player():
    data = request.get_json()
    GAME_STATE.update_player(data)
    return jsonify({"status": "ok"})

@app.route('/api/characters', methods=['GET'])
def list_characters():
    saves_dir = GAME_STATE.get_saves_dir()
    files = glob.glob(os.path.join(saves_dir, "*.json"))
    characters = []
    for f in files:
        name = os.path.splitext(os.path.basename(f))[0]
        try:
            with open(f, 'r') as fp:
                data = json.load(fp)
                characters.append({
                    "name": data.get("Name", name),
                    "species": data.get("Species", "Unknown"),
                    "sprite": data.get("Sprite", "badger_front.png"),
                    "level": data.get("Level", 1),
                    "filename": name
                })
        except: pass
    return jsonify({"characters": characters})

@app.route('/api/world/status', methods=['GET'])
def world_status():
    return jsonify({
        "chaos_level": CHAOS_MANAGER.chaos_level,
        "chaos_clock": CHAOS_MANAGER.chaos_clock,
        "tension_threshold": CHAOS_MANAGER.tension_threshold,
        "atmosphere": CHAOS_MANAGER.get_atmosphere()
    })

@app.route('/api/game/state', methods=['GET'])
def game_state(): return jsonify(GAME_LOOP.get_state())

@app.route('/api/game/action', methods=['POST'])
def game_action():
    """Universal endpoint for all map interactions."""
    data = request.get_json()
    action = data.get('action') # 'move', 'search', 'smash', etc.
    x, y = data.get('x'), data.get('y')
    
    result = GAME_LOOP.handle_action(action, x, y)
    
    return jsonify({
        "result": result,
        "state": GAME_LOOP.get_state(),
        "world": {
            "chaos_clock": CHAOS_MANAGER.chaos_clock,
            "tension_threshold": CHAOS_MANAGER.tension_threshold
        }
    })

@app.route('/api/character/save', methods=['POST'])
def save_character():
    data = request.get_json()
    name = data.get("Name")
    if not name:
        return jsonify({"error": "Name is required"}), 400
    
    saves_dir = GAME_STATE.get_saves_dir()
    if not os.path.exists(saves_dir):
        os.makedirs(saves_dir)
    
    fpath = os.path.join(saves_dir, f"{name}.json")
    with open(fpath, 'w') as f:
        json.dump(data, f, indent=4)
    
    # Also update current player if it's the one being saved
    GAME_STATE.update_player(data)
    GAME_LOOP.load_player()
    
    return jsonify({"status": "saved", "path": fpath})

@app.route('/api/character/load', methods=['POST'])
def load_character_api():
    data = request.get_json()
    name = data.get("name") # This is the filename without .json
    if not name:
        return jsonify({"error": "Name is required"}), 400
    
    fpath = os.path.join(GAME_STATE.get_saves_dir(), f"{name}.json")
    if not os.path.exists(fpath):
        return jsonify({"error": "Character file not found"}), 404
        
    try:
        with open(fpath, 'r') as f:
            char_data = json.load(f)
        
        # Update current game state player
        GAME_STATE.update_player(char_data)
        # Force game loop to refresh player instance
        GAME_LOOP.load_player()
        
        return jsonify({"status": "loaded", "character": char_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/battle/staged', methods=['POST'])
def staged_battle():
    data = request.get_json()
    staged_path = GAME_STATE.get_staged_config_path()
    with open(staged_path, 'w') as f:
        json.dump(data, f, indent=4)
    
    # Optional: trigger a game loop reset or state change
    return jsonify({"status": "staged"})

@app.route('/api/health', methods=['GET'])
def health(): return jsonify({"status": "online", "version": "2.7 - Action Engine"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

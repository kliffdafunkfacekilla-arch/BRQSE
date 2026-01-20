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

app = Flask(__name__)
CORS(app)  # Allow requests from Vite dev server

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAYER_STATE_PATH = os.path.join(BASE_DIR, "Web_ui", "public", "data", "player_state.json")
REPLAY_PATH = os.path.join(BASE_DIR, "Web_ui", "public", "data", "last_battle_replay.json")
SAVES_DIR = os.path.join(BASE_DIR, "brqse_engine", "Saves")
STAGED_CONFIG_PATH = os.path.join(BASE_DIR, "Web_ui", "public", "data", "staged_battle.json")

# --- PLAYER STATE ---

@app.route('/api/player', methods=['GET'])
def get_player():
    """Returns current player state"""
    try:
        with open(PLAYER_STATE_PATH, 'r') as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify({"error": "Player state not found"}), 404

@app.route('/api/player', methods=['POST'])
def update_player():
    """Updates player state (equipment, inventory, etc)"""
    try:
        data = request.get_json()
        with open(PLAYER_STATE_PATH, 'w') as f:
            json.dump(data, f, indent=4)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- CHARACTERS ---

@app.route('/api/characters', methods=['GET'])
def list_characters():
    """Returns list of available characters from Saves folder"""
    try:
        pattern = os.path.join(SAVES_DIR, "*.json")
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
        with open(REPLAY_PATH, 'r') as f:
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
        with open(STAGED_CONFIG_PATH, 'w') as f:
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
        with open(REPLAY_PATH, 'r') as f:
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
        
        filepath = os.path.join(SAVES_DIR, f"{safe_name}.json")
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return jsonify({"status": "ok", "path": filepath})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- HEALTH CHECK ---

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "online", "version": "2.0"})


if __name__ == '__main__':
    print("=" * 50)
    print("BRQSE API Server v2.0")
    print(f"Player State: {PLAYER_STATE_PATH}")
    print(f"Replay Path: {REPLAY_PATH}")
    print(f"Saves Dir: {SAVES_DIR}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5001, debug=True)

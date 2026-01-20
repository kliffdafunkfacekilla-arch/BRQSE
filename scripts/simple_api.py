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

app = Flask(__name__)
CORS(app)  # Allow requests from Vite dev server

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAYER_STATE_PATH = os.path.join(BASE_DIR, "Web_ui", "public", "data", "player_state.json")
REPLAY_PATH = os.path.join(BASE_DIR, "Web_ui", "public", "data", "last_battle_replay.json")

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

# --- HEALTH CHECK ---

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "online", "version": "1.0"})

if __name__ == '__main__':
    print("=" * 50)
    print("BRQSE API Server")
    print(f"Player State: {PLAYER_STATE_PATH}")
    print(f"Replay Path: {REPLAY_PATH}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5001, debug=True)

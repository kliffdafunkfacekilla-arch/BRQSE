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
# --- WORLD & LOOP ---
from scripts.world_engine import ChaosManager
from brqse_engine.core.game_loop import GameLoopController
from brqse_engine.core.sensory_layer import SensoryLayer

CHAOS_MANAGER = ChaosManager()
SENSORY_LAYER = SensoryLayer(model="qwen2.5:latest") # Detected user has qwen2.5
GAME_LOOP = GameLoopController(CHAOS_MANAGER, GAME_STATE, sensory_layer=SENSORY_LAYER)

@app.route('/api/player', methods=['GET'])
def get_player(): 
    p_data = GAME_STATE.get_player()
    
    # Enrich Powers/Skills with Active/Passive data
    from brqse_engine.abilities import engine_hooks
    
    enriched_powers = []
    for p_name in p_data.get("powers", []):
        data = engine_hooks.get_ability_data(p_name)
        # Default powers to active if not specified, or check for 'Action' type tags if available
        # For now, assume all "Powers" are active abilities
        enriched_powers.append({"name": p_name, "active": True, "type": "Power"})
        
    enriched_skills = []
    for s_name in p_data.get("skills", []):
        data = engine_hooks.get_ability_data(s_name)
        # Check if skill has an active effect or is a known active skill
        is_active = False
        if data:
            desc = data.get("Description", "").lower()
            if "action" in desc or "cast" in desc or "perform" in desc:
                is_active = True
        
        # Hardcoded overrides: Only strictly 'Action' skills (Utility/Tool)
        # "Motion" (Stealth), "Tinctures" (Heal), "Mechanism" (Unlock), "Scouting" (Search)
        if s_name in ["Motion", "Tinctures", "Mechanism", "Scouting"]: 
            is_active = True
            
        enriched_skills.append({"name": s_name, "active": is_active, "type": "Skill"})
        
    # Add Resource Pools from active combatant if available
    if GAME_LOOP.player_combatant:
        c = GAME_LOOP.player_combatant
        p_data.update({
            "sp": c.sp,
            "max_sp": c.max_sp,
            "fp": c.fp,
            "max_fp": c.max_fp,
            "cmp": c.cmp,
            "max_cmp": c.max_cmp,
            # Ensure sprite is consistent with active combatant
            "sprite": c.data.get("Sprite") or c.data.get("sprite") or p_data.get("sprite")
        })

    p_data["powers"] = enriched_powers
    p_data["skills"] = enriched_skills
    return jsonify(p_data)

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
    # Calculate progress
    stack_len = len(GAME_LOOP.scene_stack.stack)
    total = GAME_LOOP.scene_stack.total_steps
    
    return jsonify({
        "chaos_level": CHAOS_MANAGER.chaos_level,
        "chaos_clock": CHAOS_MANAGER.chaos_clock,
        "tension_threshold": CHAOS_MANAGER.tension_threshold,
        "atmosphere": CHAOS_MANAGER.get_atmosphere(),
        "daily_momentum": GAME_LOOP.game_state.daily_momentum if hasattr(GAME_LOOP.game_state, 'daily_momentum') else 0,
        "quest": {
            "title": GAME_LOOP.scene_stack.quest_title,
            "description": GAME_LOOP.scene_stack.quest_description,
            "progress": f"{total - stack_len}/{total}",
            "completed": stack_len == 0 and total > 0
        },
        "current_scene": {
            "text": GAME_LOOP.active_scene.text if GAME_LOOP.active_scene else "None",
            "type": GAME_LOOP.active_scene.encounter_type if GAME_LOOP.active_scene else "EMPTY",
            "remaining": stack_len
        }
    })

@app.route('/api/world/tension/roll', methods=['POST'])
def roll_tension_api():
    result = CHAOS_MANAGER.roll_tension()
    return jsonify({"result": result, "clock": CHAOS_MANAGER.chaos_clock})

@app.route('/api/world/quest/generate', methods=['POST'])
def generate_quest_api():
    GAME_LOOP.scene_stack.generate_quest()
    GAME_LOOP.advance_scene()
    return jsonify({
        "title": GAME_LOOP.scene_stack.quest_title,
        "steps": GAME_LOOP.scene_stack.total_steps
    })

@app.route('/api/world/scene/advance', methods=['POST'])
def advance_scene_api():
    scene = GAME_LOOP.advance_scene()
    return jsonify({
        "text": scene.text,
        "encounter_type": scene.encounter_type,
        "remaining": len(GAME_LOOP.scene_stack.stack)
    })

@app.route('/api/game/state', methods=['GET'])
def game_state(): 
    try:
        return jsonify(GAME_LOOP.get_state())
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "state": "CRASHED",
            "log": "CRITICAL: Game Loop State Error. See Server Logs."
        })

@app.route('/api/game/action', methods=['POST'])
def game_action():
    """Universal endpoint for all map interactions."""
    try:
        data = request.get_json()
        print(f"[API] Incoming Action: {json.dumps(data)}") # VERBOSE LOGGING
        action = data.get('action') # 'move', 'search', 'smash', etc.
        x, y = data.get('x'), data.get('y')
        
        result = GAME_LOOP.handle_action(action, x, y, **data)
        
        return jsonify({
            "result": result,
            "state": GAME_LOOP.get_state(),
            "world": {
                "chaos_clock": CHAOS_MANAGER.chaos_clock,
                "tension_threshold": CHAOS_MANAGER.tension_threshold
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "result": {"success": False, "log": f"SYSTEM ERROR: {str(e)}"},
            "state": GAME_LOOP.get_state() if GAME_LOOP else {},
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

@app.route('/api/debug/force_combat', methods=['POST'])
def debug_force_combat():
    return jsonify(GAME_LOOP.force_combat())

@app.route('/api/health', methods=['GET'])
def health(): return jsonify({"status": "online", "version": "2.8 - Omniscient GM"})

@app.route('/api/game/chat', methods=['POST'])
def game_chat():
    """
    Direct interface to the Dungeon Master (Oracle).
    """
    try:
        data = request.get_json()
        message = data.get("message", "")
        if not message:
            return jsonify({"response": "..."})

        # Call Oracle Chat
        # Logic: GameLoop -> Interaction -> Oracle -> Chat
        response = GAME_LOOP.interaction.oracle.chat(message)
        
        return jsonify({"response": response})
    except Exception as e:
        print(f"[API ERROR] Chat: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "response": "The spirits are silent."}), 500

@app.route('/generate', methods=['POST'])
def generate_text():
    """Generic text generation endpoint for Story Director."""
    try:
        data = request.get_json()
        prompt = data.get("prompt", "")
        # Route through SENSORY_LAYER which handles Ollama connection
        response_text = SENSORY_LAYER.consult_oracle("You are a creative game master.", prompt)
        return jsonify({"response": response_text})
    except Exception as e:
        print(f"[API ERROR] Generate: {e}")
        return jsonify({"error": str(e), "response": "The Oracle is silent."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

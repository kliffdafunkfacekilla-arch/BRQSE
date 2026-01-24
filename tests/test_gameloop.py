from brqse_engine.core.game_loop import GameLoopController
from scripts.world_engine import ChaosManager

cm = ChaosManager()
gl = GameLoopController(cm)

print(f"Initial Scene: {gl.current_scene_text}")
print(f"Mode: {gl.state}")
print(f"Player Start: {gl.player_pos}")
print(f"Walls Count: {len(gl.active_scene_data['walls'])}")

# Test Movement
res = gl.handle_move(gl.player_pos[0]+1, gl.player_pos[1])
print(f"Move Result: {res}")
print(f"New Pos: {gl.player_pos}")

# Test Interact (Force add a chest neighbor)
test_chest_pos = (gl.player_pos[0]+1, gl.player_pos[1])
gl.interactables[test_chest_pos] = {"type": "CHEST"}

ires = gl.handle_interact(*test_chest_pos)
print(f"Interact Result: {ires}")

# Test Combat Trigger (Force enemy neighbor)
gl.active_scene_data["spawn_points"] = [(gl.player_pos[0]+1, gl.player_pos[1])]
res = gl.handle_move(gl.player_pos[0]-1, gl.player_pos[1]) # Move away but still close
# Actually simpler: Move INTO range.
# But combat check runs AFTER move.
# Let's just print state to see if it changed logic
print(f"Mode Check (Aggro): {res.get('event', 'SAFE')}")

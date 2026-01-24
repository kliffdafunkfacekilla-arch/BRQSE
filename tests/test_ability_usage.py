import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "c:/Users/krazy/Desktop/BRQSE"))

from brqse_engine.core.game_loop import GameLoopController
from scripts.world_engine import ChaosManager
from brqse_engine.models.character import Character
from brqse_engine.combat.combatant import Combatant

def test_ability_usage():
    print("--- Testing Ability Usage ---")
    cm = ChaosManager()
    gl = GameLoopController(cm)
    
    # Mock a player with skills/powers
    char_data = {
        "Name": "Test Hero",
        "Powers": ["Heat", "Mend"],
        "Skills": ["Scouting", "Mechanism"],
        "Stats": {"Might": 10, "Vitality": 10, "Reflexes": 10}
    }
    gl.player_combatant = Combatant(Character(char_data))
    gl.player_combatant.hp = 10
    
    # Test Heal (Mend)
    print(f"Known abilities: {[a.lower() for a in gl.player_combatant.character.powers]}")
    print("Using 'mend'...")
    res = gl.handle_action("mend", 0, 0)
    log = res.get('log', "")
    print(f"Result keys: {res.keys()}")
    print(f"Log: '{log}'")
    print(f"HP after Mend: {gl.player_combatant.hp}")
    # Mend is "Heal minor wounds" -> resolved by existing _handle_minor_heal (1d8+2)
    assert "heals" in log and "Minor" in log
    assert gl.player_combatant.hp > 10
    
    # Test Scouting (Skill)
    print("Using 'scouting'...")
    res = gl.handle_action("scouting", 0, 0)
    print(f"Log: {res.get('log')}")
    print(f"Vision radius check (if possible): {getattr(gl, '_vision_radius', 'N/A')}")
    assert "perception sharpens" in res.get("log")
    
    # Test Unknown
    print("Using 'Unknown'...")
    res = gl.handle_action("flying kick", 0, 0)
    print(f"Success: {res.get('success')}, Reason: {res.get('reason')}")
    assert res.get("success") == False
    
    print("Pass: Ability usage logic is working.")

if __name__ == "__main__":
    import traceback
    try:
        test_ability_usage()
    except Exception as e:
        print("\n--- TEST FAILED ---")
        traceback.print_exc()
        exit(1)

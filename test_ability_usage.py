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
        "Powers": ["Fireball", "Heal Light"],
        "Skills": ["Search", "Sneak"],
        "Stats": {"Might": 10, "Vitality": 10, "Reflexes": 10}
    }
    gl.player_combatant = Combatant(Character(char_data))
    gl.player_combatant.hp = 10
    
    # Test Heal
    print(f"Known abilities: {[a.lower() for a in gl.player_combatant.character.powers]}")
    print("Using 'heal light'...")
    res = gl.handle_action("heal light", 0, 0)
    log = res.get('log', "")
    print(f"Log: '{log}'")
    assert "+10 HP" in log
    assert gl.player_combatant.hp == 20
    
    # Test Search
    print("Using 'Search'...")
    res = gl.handle_action("search", 0, 0)
    print(f"Log: {res.get('log')}")
    assert "You scour the area" in res.get("log")
    
    # Test Unknown
    print("Using 'Unknown'...")
    res = gl.handle_action("flying kick", 0, 0)
    print(f"Success: {res.get('success')}, Reason: {res.get('reason')}")
    assert res.get("success") == False
    
    print("Pass: Ability usage logic is working.")

if __name__ == "__main__":
    test_ability_usage()

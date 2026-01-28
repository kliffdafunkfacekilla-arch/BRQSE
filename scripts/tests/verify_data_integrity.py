
import sys
import os
import json

# Add project root to path
sys.path.append(os.getcwd())

from brqse_engine.core.game_state import GameState
from brqse_engine.combat.mechanics import Combatant

def verify():
    print("--- STARTING DATA INTEGRITY CHECK ---")
    
    # 1. Load Game State
    try:
        gs = GameState(os.getcwd())
        player_data = gs.get_player()
        print("Player Data Loaded OK.")
    except Exception as e:
        print(f"FATAL: GameState load failed: {e}")
        return

    # 2. Attempt Combatant Initialization (This triggered previous crashes)
    try:
        c = Combatant(data=player_data)
        print("Combatant Initialization OK.")
    except Exception as e:
        print(f"FATAL: Combatant init failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # 3. Deep Check of Fields
    print("\n--- DEEP FIELD ANALYSIS ---")
    
    # SKILLS
    print(f"Skills Type: {type(c.skills)}")
    if isinstance(c.skills, dict):
        print(f"Skill Count: {len(c.skills)}")
        for k, v in c.skills.items():
            if not isinstance(k, str): print(f"WARNING: Non-string skill key: {k} ({type(k)})")
            if not isinstance(v, (int, float)): print(f"WARNING: Non-numeric skill rank: {v} ({type(v)})")
    else:
        print("ERROR: Skills should be a dict after init.")

    # POWERS
    print(f"\nPowers Type: {type(c.powers)}")
    valid_powers = True
    for p in c.powers:
        if not isinstance(p, str):
            print(f"ERROR: Power is not string: {p} ({type(p)})")
            valid_powers = False
    if valid_powers: print("Powers structure OK.")

    # TRAITS
    print(f"\nTraits Type: {type(c.traits)}")
    valid_traits = True
    for t in c.traits:
        if not isinstance(t, str):
            # progression.py handles non-strings now, but mechanics.py init might leave them raw?
            # Let's check what Mechanics.py left in c.traits
            print(f"WARNING: Trait is not string in Combatant object: {t} ({type(t)})")
            # If mechanics.py left dicts here, other systems might choke later
            valid_traits = False
    if valid_traits: print("Traits structure OK.")

    # INVENTORY
    print(f"\nInventory Items: {len(c.inventory.items) if c.inventory else 'None'}")
    if c.inventory:
        for item in c.inventory.items:
             if not isinstance(item.name, str):
                 print(f"ERROR: Item name is not string: {item.name}")

    print("\n--- CHECK COMPLETE ---")

if __name__ == "__main__":
    verify()

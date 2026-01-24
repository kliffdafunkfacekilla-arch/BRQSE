
import sys
import os
import json
import traceback

# Setup Path
sys.path.append(os.getcwd())

def audit():
    print("=== BEGINNING PROJECT AUDIT ===")
    errors = []

    # 1. Dependency Check
    print("\n[Audit] Checking Dependencies...")
    try:
        from brqse_engine.core.game_loop import GameLoopController
        from brqse_engine.core.game_state import GameState
        from brqse_engine.combat.mechanics import CombatEngine
        from scripts.world_engine import ChaosManager
        print("  OK: Core modules imported.")
    except ImportError as e:
        errors.append(f"Import Error: {e}")
        print(f"  FAIL: {e}")
        return

    # 2. Data Loading Check
    print("\n[Audit] Checking Data Loader...")
    try:
        from brqse_engine.abilities.data_loader import DataLoader
        dl = DataLoader()
        print(f"  OK: Loaded {len(dl.talents)} Talents.") 
        # Note: EventEngine usually loads events, DataLoader loads CSVs.
        # Let's check a specific CSV load
        if not dl.talents:
             print("  WARN: No talents loaded (CSV missing or parsing failed?)")
    except Exception as e:
        errors.append(f"Data Loader Crash: {e}")
        print(f"  FAIL: {e}")

    # 3. Game Loop Initialization
    print("\n[Audit] Initializing Game Loop...")
    try:
        chaos = ChaosManager()
        gs = GameState(os.getcwd())
        loop = GameLoopController(chaos, gs)
        print("  OK: GameLoopController initialized.")
    except Exception as e:
        errors.append(f"Game Loop Init Crash: {e}")
        print(f"  FAIL: {e}")
        traceback.print_exc()
        return

    # 4. Player Integrity
    print("\n[Audit] Checking Player State...")
    if not loop.player_combatant:
        print("  WARN: No player loaded initially.")
    else:
        p = loop.player_combatant
        print(f"  OK: Player '{p.name}' loaded.")
        
        # Check Critical Attributes for GameLoop
        required_attrs = ['elevation', 'is_behind_cover', 'x', 'y', 'hp', 'max_hp']
        for attr in required_attrs:
            if not hasattr(p, attr):
                errors.append(f"Player missing attribute '{attr}' required by GameLoop")
                print(f"  FAIL: Missing {attr}")
            else:
                print(f"    - Has {attr}: {getattr(p, attr)}")

    # 5. Simulation: Explore Action
    print("\n[Audit] Simulating Explore Action...")
    try:
        loop.state = "EXPLORE"
        res = loop.handle_action("move", 6, 6) # Move somewhere
        print(f"  Result: {res}")
        if not res.get('success'):
             print(f"  WARN: Move failed: {res.get('reason')}")
    except Exception as e:
        errors.append(f"Explore Action Crash: {e}")
        print(f"  FAIL: {e}")
        traceback.print_exc()

    # 6. Simulation: Combat Transition
    print("\n[Audit] Simulating Combat Start...")
    try:
        # Spawn an enemy manually
        from brqse_engine.combat.mechanics import Combatant
        enemy = Combatant(data={"Name": "TestDummy", "Stats": {"Reflexes": 10}, "Traits": [], "Powers": []})
        enemy.team = "Enemies"
        loop.combat_engine.add_combatant(enemy, 7, 7)
        loop.state = "COMBAT"
        print("  OK: Combat state force-set.")
        
        # Attack Action
        print("  [Audit] Simulating Attack...")
        loop.player_combatant.x = 6
        loop.player_combatant.y = 7 # Adjacent
        res = loop.handle_action("attack", 7, 7) # Click on enemy tile
        print(f"  Result: {res}")
        
    except Exception as e:
        errors.append(f"Combat Simulation Crash: {e}")
        print(f"  FAIL: {e}")
        traceback.print_exc()

    # Summary
    print("\n=== AUDIT COMPLETE ===")
    if errors:
        print(f"Found {len(errors)} Critical Errors:")
        for err in errors:
            print(f" - {err}")
    else:
        print("No critical crashes detected during simulation.")

if __name__ == "__main__":
    audit()

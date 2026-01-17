import sys
import os

# Add path to scripts
sys.path.append(os.path.join(os.path.dirname(__file__), "combat simulator"))

try:
    from mechanics import CombatEngine, Combatant
    from abilities.effects_registry import EffectRegistry
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def run_debug():
    print("Initializing Engine...")
    engine = CombatEngine()
    registry = EffectRegistry()
    
    # Create Dummy Combatant
    c1 = Combatant(filepath=None, data={
        "Name": "Caster",
        "Species": "Human",
        "Stats": {"Might": 10, "Reflexes": 10},
        "Derived": {"HP": 20, "Speed": 30},
        "Skills": [], "Traits": [], "Powers": []
    })
    c1.x, c1.y = 5, 5
    engine.add_combatant(c1, 5, 5)
    print("Engine Initialized.")

    # --- TEST WALLS ---
    print("\n--- Testing Wall Creation ---")
    ctx = {"engine": engine, "attacker": c1, "log": []}
    registry.resolve("Create wall", ctx)
    
    wall_loc = (6, 5)
    if wall_loc in engine.walls:
        print(f"SUCCESS: Wall found at {wall_loc}")
    else:
        print(f"FAILURE: Wall NOT found at {wall_loc}. Walls: {engine.walls}")
        
    success, msg = engine.move_char(c1, 6, 5)
    if not success and "Blocked by Wall" in msg:
        print(f"SUCCESS: Movement blocked properly: {msg}")
    else:
        print(f"FAILURE: Movement NOT blocked: {success}, {msg}")

    # --- TEST SUMMONS ---
    print("\n--- Testing Summoning ---")
    ctx = {"engine": engine, "attacker": c1, "log": []}
    initial_count = len(engine.combatants)
    registry.resolve("summon Wolf", ctx)
    
    new_count = len(engine.combatants)
    if new_count == initial_count + 1:
        minion = engine.combatants[-1]
        print(f"SUCCESS: Summoned {minion.name} at {minion.x},{minion.y}")
        if minion in engine.turn_order:
             print("SUCCESS: Minion in Turn Order")
        else:
             print("FAILURE: Minion NOT in Turn Order")
    else:
        print(f"FAILURE: Summon count mismatch. Count: {new_count}")

    # --- TEST SPECIES ABILITIES ---
    print("\n--- Testing Species Abilities ---")
    
    # RESET ENGINE
    engine = CombatEngine()
    registry = EffectRegistry()
    c1 = Combatant(filepath=None, data={
        "Name": "Caster", "Species": "Human",
        "Stats": {"Might": 10}, "Derived": {"HP": 20, "Speed": 30}
    })
    c1.x, c1.y = 5, 5
    engine.add_combatant(c1, 5, 5)
    
    # Species Setup: Enemy at 6,5
    c2 = Combatant(filepath=None, data={
        "Name": "TargetDummy", "Species": "Goblin",
        "Stats": {"Might": 10}, "Derived": {"HP": 10, "Speed": 30}
    })
    c2.x, c2.y = 6, 5
    engine.add_combatant(c2, 6, 5)

    # 1. Spore Cloud
    ctx = {"engine": engine, "attacker": c1, "log": []}
    registry.resolve("Release spores", ctx)
    if c2.is_poisoned:
        print("SUCCESS: Target poisoned by Spore Cloud")
    else:
        print("FAILURE: Target NOT poisoned")

    # 2. Gust
    ctx = {"engine": engine, "attacker": c1, "target": c2, "log": []}
    # Gust pushes 2 squares (linear). From 6,5 -> 8,5
    registry.resolve("Gust", ctx)
    
    if c2.x == 8 and c2.y == 5:
        print(f"SUCCESS: Target pushed to {c2.x},{c2.y}")
    else:
        print(f"FAILURE: Target at {c2.x},{c2.y}, expected 8,5. Log: {ctx.get('log')}")

if __name__ == "__main__":
    run_debug()

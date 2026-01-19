import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from brqse_engine.combat.mechanics import CombatEngine, Combatant

def test_entangle():
    print("Initializing Engine...")
    engine = CombatEngine()
    
    # Load characters
    # Note: Assuming CWD is c:/Users/krazy/Desktop/BRQSE
    flower_path = "brqse_engine/Saves/flower.json"
    buggy_path = "brqse_engine/Saves/buggy.json"
    
    if not os.path.exists(flower_path):
        print(f"Error: {flower_path} not found.")
        return

    print("Loading Combatants...")
    flower = Combatant(filepath=flower_path)
    buggy = Combatant(filepath=buggy_path)
    
    flower.name = "Flower"
    buggy.name = "Buggy"
    
    engine.add_combatant(flower, 0, 0)
    engine.add_combatant(buggy, 0, 1) # Adjacent
    
    print(f"\nStats Check:")
    print(f"Flower Fortitude: {flower.get_stat('Fortitude')} (Mod: {flower.get_stat_modifier('Fortitude')})")
    print(f"Buggy Reflexes: {buggy.get_stat('Reflexes')} (Mod: {buggy.get_stat_modifier('Reflexes')})")
    print(f"Buggy Might: {buggy.get_stat('Might')} (Mod: {buggy.get_stat_modifier('Might')})")

    print("\n--- TEST: Casting Entangle ---")
    # Activate 'Entangle' directly
    log = engine.activate_ability(flower, "Entangle", target=buggy)
    
    for line in log:
        print(f"LOG: {line}")
        
    print(f"\nResult: Buggy Restrained? {buggy.is_restrained}")

if __name__ == "__main__":
    test_entangle()

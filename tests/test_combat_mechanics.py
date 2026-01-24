
import sys
import os
sys.path.append(os.getcwd())
from brqse_engine.combat.mechanics import CombatEngine, Combatant

def test_restoration():
    print("Testing Mechanics Engine Restoration...")
    
    # 1. Initialize Engine
    eng = CombatEngine(20, 20)
    print("Engine initialized.")
    
    # 2. Create Combatants
    p_data = {"Name": "Hero", "Stats": {"Might": 18, "Reflexes": 14}, "Sprite": "badger_front.png"}
    e_data = {"Name": "Villain", "Stats": {"Might": 16, "Reflexes": 12}, "Sprite": "wolf_front.png"}
    
    hero = Combatant(data=p_data)
    villain = Combatant(data=e_data)
    
    eng.add_combatant(hero, 5, 5)
    eng.add_combatant(villain, 6, 5) # Adjacent
    print(f"Combatants added: {hero.name} vs {villain.name}")
    
    # 3. Test Attack
    print("\nExecuting Attack...")
    log = eng.attack_target(hero, villain)
    print("Log Output:")
    for l in log: print(f" - {l}")
    
    # 4. Verify Log and Replay Log
    if not log:
        print("FAIL: No log output.")
        return
        
    print("\nReplay Log Check:")
    if eng.replay_log:
        print(eng.replay_log[-1])
    else:
        print("FAIL: No replay log.")
        
    # 5. Check Sprite Access for GameLoop
    sprite_check = hero.data.get("Sprite")
    print(f"\nSprite Check: {sprite_check}")
    if sprite_check != "badger_front.png":
        print("FAIL: Sprite mapping incorrect.")
    else:
        print("PASS: Sprite mapping correct.")

if __name__ == "__main__":
    test_restoration()

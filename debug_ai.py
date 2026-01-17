
import sys
import os

# Add path to scripts
sys.path.append(os.path.join(os.path.dirname(__file__), "combat simulator"))

try:
    from mechanics import CombatEngine, Combatant
    # Ensure AI is imported
    from ai_engine import AIDecisionEngine
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def run_debug():
    print("Initializing Engine for AI Debug...")
    engine = CombatEngine()
    
    # --- TEST 1: CASTER HEAL PRIORITY ---
    print("\n--- TEST 1: CASTER HEAL PRIORITY ---")
    
    # 1. Setup Caster (AI)
    caster = Combatant(filepath=None, data={
        "Name": "ClericBot", "Species": "Human",
        "Stats": {"Might": 10}, "Derived": {"HP": 20},
        "AI": "Caster",
        "Powers": ["Heal"] 
    })
    caster.team = "Empire"
    engine.add_combatant(caster, 5, 5)
    
    # 2. Setup Injured Ally
    ally = Combatant(filepath=None, data={
            "Name": "DyingSoldier", "Species": "Human",
            "Stats": {"Might": 10}, "Derived": {"HP": 20}
    })
    ally.hp = 2 
    ally.team = "Empire"
    engine.add_combatant(ally, 5, 6) # Adjacent
    
    # 3. Setup Enemy 
    enemy = Combatant(filepath=None, data={
        "Name": "TargetDummy", "Species": "Goblin",
        "Stats": {"Might": 10}, "Derived": {"HP": 10}
    })
    enemy.team = "Rebels"
    engine.add_combatant(enemy, 5, 8) 
    
    # 4. Run AI Turn
    log = engine.execute_ai_turn(caster)
    print("Log:")
    for l in log: print(f"  {l}")
    
    has_healed = any("Cast [Heal]" in l for l in log)
    if has_healed:
        print("SUCCESS: Caster healed ally.")
    else:
        print("FAILURE: Caster did not heal ally.")

    # --- TEST 2: CASTER AOE PRIORITY ---
    print("\n--- TEST 2: CASTER AOE PRIORITY ---")
    engine = CombatEngine() # Reset
    caster = Combatant(filepath=None, data={
        "Name": "MageBot", "Species": "Human",
        "Stats": {"Might": 10}, "Derived": {"HP": 20},
        "AI": "Caster",
        "Powers": ["Spore Cloud"] 
    })
    caster.team = "Empire"
    # Spore Cloud is self-centered (radius 2), so need to be close to target (5,5)
    engine.add_combatant(caster, 4, 4)
    
    # Create Cluster of Enemies
    for i in range(3):
        e = Combatant(filepath=None, data={"Name": f"Goblin{i}", "Stats": {}, "Derived": {"HP":10}})
        e.team = "Rebels"
        engine.add_combatant(e, 5, 5+i) 
        
    log = engine.execute_ai_turn(caster)
    print("Log:")
    for l in log: print(f"  {l}")
    
    # "poisoned by Spore Cloud" or similar logic from registry
    has_aoe = any("Spore Cloud" in l for l in log)
    if has_aoe:
        print("SUCCESS: Caster used AoE Spore Cloud.")
    else:
        print("FAILURE: Caster did not use AoE.")

if __name__ == "__main__":
    run_debug()

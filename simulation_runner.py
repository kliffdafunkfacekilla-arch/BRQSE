
import sys
import os
import time

sys.path.append('combat simulator')
import mechanics

def run_simulation(battles=50):
    print(f"--- Starting Combat Simulation ({battles} Battles) ---")
    
    wins = {"P1": 0, "P2": 0}
    total_turns = 0
    
    # Define Loadouts
    # We'll use mechanics.Combatant to load from Saves/Ironclad.json if available
    # Or create scratch characters
    
    save_path = "Saves/Ironclad.json"
    if not os.path.exists(save_path):
        print("Warning: Ironclad.json not found, using default stats.")
        save_path = None
        
    for i in range(battles):
        # 1. Setup Engine
        engine = mechanics.CombatEngine()
        
        # 2. Setup Fighters
        # Fighter 1: Ironclad (The Tank)
        f1 = mechanics.Combatant(filepath=save_path, data={"Name": "Ironclad", "AI": "Aggressive"} if not save_path else None)
        f1.name = "Ironclad"
        f1.data["AI"] = "Aggressive" # Force AI
        f1.team = "Team 1"

        # Fighter 2: Swiftblade (The DPS) - mocking a high dex fighter
        f2 = mechanics.Combatant(data={
            "Name": "Swiftblade", 
            "Stats": {"Reflexes": 18, "Finesse": 16, "Vitality": 12, "Might": 10, "Endurance": 10, "Fortitude": 10, "Knowledge":10,"Logic":10,"Awareness":10,"Intuition":10,"Charm":10,"Willpower":10},
            "Derived": {"HP": 20, "Speed": 7},
            "Inventory": ["Rapier", "Duelist Leathers"],
            "Skills": {"The Blades": 3, "Leather": 2},
            "AI": "Aggressive"
        })
        f2.team = "Team 2"
        
        # 3. Add to Battle
        engine.add_combatant(f1, 3, 5) # Left side
        engine.add_combatant(f2, 8, 5) # Right side
        
        # Initialize Turn Order
        engine.start_combat()
        
        # DEBUG: Check Start Condition
        # print(f"Start: {f1.name} HP: {f1.hp} | {f2.name} HP: {f2.hp}")
        
        # 4. Fight Loop
        combat_active = True
        turns = 0
        max_turns = 50 # Prevent infinite loops
        
        while combat_active and turns < max_turns:
            active = engine.get_active_char()
            if not active: break # Should not happen
            
            # Start Turn
            can_act, _ = engine.start_turn(active)
            
            if can_act:
                # AI Execution
                # Note: mechanics.execute_ai_turn returns a log list
                ailog = engine.execute_ai_turn(active)
                # if i == 0: print(f"T{turns} {active.name}: {ailog}")
            
            # End Turn
            engine.end_turn()
            
            # Check Death
            alive = [c for c in engine.combatants if c.is_alive()]
            if len(alive) <= 1:
                combat_active = False
                winner = alive[0] if alive else None
                if winner:
                    if winner == f1: wins["P1"] += 1
                    else: wins["P2"] += 1
            
            turns += 1
            
        total_turns += turns
        # Progress Bar
        if (i+1) % 10 == 0:
            print(f"Battle {i+1}/{battles} Complete...")
            
    print(f"\n\n--- Simulation Results ---")
    print(f"Total Battles: {battles}")
    print(f"Ironclad Wins: {wins['P1']} ({wins['P1']/battles*100:.1f}%)")
    print(f"Swiftblade Wins: {wins['P2']} ({wins['P2']/battles*100:.1f}%)")
    print(f"Avg Turns: {total_turns/battles:.1f}")
    print("--------------------------")

if __name__ == "__main__":
    run_simulation(100)

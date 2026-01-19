"""
Combat Simulation Runner
Runs AI vs AI battles with random characters to test behavior and mechanics.
"""
import sys
import os
import random
import time

from brqse_engine.combat.mechanics import CombatEngine, Combatant

def run_simulation(battles=10, verbose=True):
    """Run combat simulations with random fighters from Saves folder."""
    
    # Get all available saves
    saves_dir = "brqse_engine/Saves"
    # saves = [f for f in os.listdir(saves_dir) if f.endswith('.json')]
    saves = ["buggy.json", "flower.json"] # User Request
    
    if len(saves) < 2:
        print("Need at least 2 saved characters!")
        return
    
    print(f"\n{'='*60}")
    print(f"COMBAT SIMULATION - {battles} Battles")
    print(f"Available Fighters: {', '.join(s.replace('.json','') for s in saves)}")
    print(f"{'='*60}\n")
    
    wins = {}
    total_turns = 0
    
    for battle_num in range(1, battles + 1):
        # Pick two random different fighters
        f1_file, f2_file = random.sample(saves, 2)
        f1_path = os.path.join(saves_dir, f1_file)
        f2_path = os.path.join(saves_dir, f2_file)
        
        # Load fighters
        f1 = Combatant(filepath=f1_path)
        f2 = Combatant(filepath=f2_path)
        
        # Initialize win tracking
        if f1.name not in wins: wins[f1.name] = 0
        if f2.name not in wins: wins[f2.name] = 0
        
        # Setup engine
        engine = CombatEngine()
        
        # Place fighters on opposite sides
        engine.add_combatant(f1, 3, 5)
        engine.add_combatant(f2, 8, 5)
        
        # Set teams
        f1.team = "Team 1"
        f2.team = "Team 2"
        
        # Start combat
        engine.start_combat()
        
        if verbose:
            print(f"\n--- Battle {battle_num}: {f1.name} vs {f2.name} ---")
            print(f"{f1.name}: HP {f1.hp}/{f1.max_hp} | Powers: {f1.powers[:3] if f1.powers else 'None'}")
            print(f"{f2.name}: HP {f2.hp}/{f2.max_hp} | Powers: {f2.powers[:3] if f2.powers else 'None'}")
            print()
        
        # Fight loop
        turns = 0
        max_turns = 30
        combat_active = True
        
        while combat_active and turns < max_turns:
            turns += 1
            
            for combatant in engine.turn_order:
                if not combatant.is_alive():
                    continue
                
                # Reset turn
                combatant.action_used = False
                combatant.bonus_action_used = False
                combatant.movement_remaining = combatant.movement
                
                # Execute AI turn
                can_act, start_log = engine.start_turn(combatant) # Capture the start log too!
                if verbose and start_log:
                    for entry in start_log: print(f"  {entry}")

                if can_act:
                    ai_log = engine.execute_ai_turn(combatant)
                    
                    if verbose:
                        # Print important events
                        for entry in ai_log:
                            if any(kw in entry for kw in ['HIT', 'MISS', 'CLASH', 'uses', 'Consumed', 'Dealt', 'knocked', 'damage']):
                                print(f"  {entry}")
                    
                    # --- BURT'S CLASH FIX ---
                    if engine.clash_active:
                        # AI doesn't have a brain to choose "Push" or "Swap", so we random it
                        # Or better, we pass a dummy choice since mechanics.resolve_clash 
                        # currently calculates effects based on the STAT used, not the choice!
                        # (Your current resolve_clash ignores the 'choice' arg mostly)
                        clash_log = engine.resolve_clash("Aggressive") 
                        if verbose:
                            for entry in clash_log:
                                print(f"  [CLASH RESULT] {entry}")
                    # ------------------------
                
                engine.end_turn()
                
                # Check for death
                if not f1.is_alive() or not f2.is_alive():
                    combat_active = False
                    break
        
        # Determine winner
        if f1.is_alive() and not f2.is_alive():
            winner = f1.name
            wins[f1.name] += 1
        elif f2.is_alive() and not f1.is_alive():
            winner = f2.name
            wins[f2.name] += 1
        elif f1.hp > f2.hp:
            winner = f1.name + " (HP)"
        elif f2.hp > f1.hp:
            winner = f2.name + " (HP)"
        else:
            winner = "DRAW"
        
        total_turns += turns
        
        if verbose:
            print(f"\n  >> {winner} WINS in {turns} turns!")
            print(f"  Final: {f1.name} {max(0, f1.hp)}HP | {f2.name} {max(0, f2.hp)}HP")
    
    # Summary
    print(f"\n{'='*60}")
    print("RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"Total Battles: {battles}")
    print(f"Avg Turns: {total_turns/battles:.1f}")
    print("\nWin Rates:")
    for name, count in sorted(wins.items(), key=lambda x: -x[1]):
        if count > 0:
            print(f"  {name}: {count} wins")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    num_battles = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    run_simulation(battles=num_battles, verbose=True)

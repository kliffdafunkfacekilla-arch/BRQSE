import sys
import os
import random

# Ensure we can import from local
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brqse_engine.models.character import Character
from brqse_engine.combat.combatant import Combatant
from brqse_engine.combat.combat_engine import CombatEngine
import brqse_engine.abilities.engine_hooks as engine_hooks

def run_test(name, func):
    print(f"\n[{name}] Running...")
    try:
        func()
        print(f"[{name}] PASSED")
    except AssertionError as e:
        print(f"[{name}] FAILED: {e}")
    except Exception as e:
        print(f"[{name}] CRASHED: {e}")

def setup_engine():
    engine = CombatEngine(cols=10, rows=10)
    # Character with 10 HP, 10 SP
    # Stats: Might=10, Vitality=10 (MaxHP=20)
    char_data = {"Name": "TestSubject", "Stats": {"Might": 10, "Vitality": 10, "Endurance": 10, "Finesse": 10, "Fortitude": 10}, "Current_HP": 20}
    hero = Character(char_data)
    c_hero = Combatant(hero, x=0, y=0, team="Blue")
    engine.add_combatant(c_hero)
    engine.start_combat()
    return engine, c_hero

# --- TESTS ---

def test_hazard_death():
    """Verify entity dies and stops moving if killed by hazard mid-path."""
    engine, hero = setup_engine()
    hero.current_hp = 5 # Set low HP
    hero.character.current_hp = 5
    
    # Set 3 tiles of Fire (2d6 damage roughly 7 avg, should kill)
    engine.set_terrain(0, 1, "fire")
    engine.set_terrain(0, 2, "fire")
    
    # Try to move through fire
    print(f"  Hero HP: {hero.current_hp}. Moving into Fire...")
    moved = engine.move_entity(hero, 0, 1)
    
    assert moved, "Should be able to move into hazard initially"
    print(f"  Hero HP after step 1: {hero.current_hp}")
    
    if hero.current_hp == 0:
        print("  Hero died on step 1.")
        assert not hero.is_alive, "Hero should be dead"
        
        # Try moving dead hero
        moved_dead = engine.move_entity(hero, 0, 2)
        assert not moved_dead, "Dead hero should not move"
    else:
        # If survived (lucky roll), manual kill for test logic
        print("  Hero survived step 1 (Luck!). Killing manually to test dead movement.")
        hero.take_damage(100)
        moved_dead = engine.move_entity(hero, 0, 2)
        assert not moved_dead, "Dead hero should not move"

def test_resource_exhaustion():
    """Verify ability fails if resources are insufficient."""
    engine, hero = setup_engine()
    
    # Add ability with Cost: 20 SP (Hero has ~30 from stats? Let's check)
    # 10+10+10 = 30 SP. So let's cost 100 SP.
    mock_ability = {"Talent_Name": "Expensive Move", "Effect": "Cost: 100 SP. Heal 10 HP"}
    engine_hooks.loader.talents.append(mock_ability)
    
    print(f"  Hero SP: {hero.sp}")
    success = engine.activate_ability(hero, "Expensive Move", target=hero)
    
    assert not success, "Ability should fail due to lack of SP"
    print(f"  Ability failed as expected. SP: {hero.sp}")

def test_status_stacking():
    """Verify DOTs stack and apply damage."""
    engine, hero = setup_engine()
    hero.current_hp = 20
    
    # Add Bleed (1d4? depends on registry) and Poison (1d4?)
    # Registry: Bleed = Condition. Poison = Condition.
    # Where is the damage logic? It's usually in `Combatant.tick_effects` or `CombatEngine` needs to handle specific conditions?
    # Wait. `tick_effects` currently only decrements duration.
    # The PROPOSAL said: "CombatEngine/Combatant duration processing".
    # BUT `tick_effects` doesn't apply damage unless programmed to!
    # Deep Dive: Does `Combatant.tick_effects` apply DoT damage? NO. It just returns expired.
    # FIX NEEDED: Logic for DoT application is missing from `tick_effects` or `next_turn`.
    # This test is EXPECTED TO FAIL or expose the gap.
    
    hero.add_condition("Bleeding")
    hero.add_condition("Poisoned")
    
    # Manually adding timed effect so they don't expire instantly
    hero.add_timed_effect("Bleeding", 3)
    hero.add_timed_effect("Poisoned", 3)
    
    print("  Applying Bleed + Poison. Ticking turn...")
    start_hp = hero.current_hp
    
    # Tick loop
    # We need to simulate the engine processing the turn start events.
    # Current engine `next_turn` only calls `tick_effects`.
    # It does NOT verify if 'Bleeding' causes damage.
    # We expect this validation to show we need to add DoT logic.
    
    engine.next_turn() # Should trigger things
    
    # Assertion: Did HP drop?
    if hero.current_hp < start_hp:
        print(f"  HP Dropped to {hero.current_hp}. DoTs working.")
    else:
        print("  HP did not drop. DoTs NOT working (Expected finding).")
        # Don't crash test, just note failure
        raise AssertionError("DoT damage logic is missing.")

def test_action_denial():
    """Verify Stunned prevents Action."""
    engine, hero = setup_engine()
    
    hero.add_condition("Stunned")
    hero.add_timed_effect("Stunned", 2)
    
    # Engine does not strictly enforce "Can't act" in `activate_ability` yet.
    # It assumes the AI/UI checks `action_used`.
    # But for a robust engine, `activate_ability` should probably check Stunned.
    
    mock_ability = {"Talent_Name": "Simple Strike", "Effect": "Deal 5 Damage"}
    engine_hooks.loader.talents.append(mock_ability)
    
    print("  Hero is Stunned. Attempting ability...")
    # NOTE: The current `activate_ability` does NOT check for Stunned status.
    # This test expects to reveal that gap.
    
    success = engine.activate_ability(hero, "Simple Strike", target=hero)
    
    if success:
        print("  Ability Succeeded (Unexpected). Engine lacks Stun check.")
        raise AssertionError("Stunned entity was allowed to act.")
    else:
        print("  Ability Blocked (Correct).")

if __name__ == "__main__":
    print("=== STRESS TEST SUITE ===")
    run_test("Hazard Death", test_hazard_death)
    run_test("Resource Exhaustion", test_resource_exhaustion)
    # These two are expected to fail, revealing bugs to fix:
    run_test("Status Stacking (DoTs)", test_status_stacking)
    run_test("Action Denial (Stun)", test_action_denial)


import sys
import os
import csv

# Add path to root so we can import abilities
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

try:
    # Try importing the class and instantiating it
    from brqse_engine.abilities.effects_registry import EffectRegistry
    # Mock Combatant needs StatusManager?
    # Or just derived...
    from brqse_engine.combat.mechanics import Combatant 
    # Use real combatant if possible? No, stick to Mock for now or import real one.
    # Used imports above
    registry = EffectRegistry()
except ImportError:
    # Manual path handling if run from scripts/
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    try:
        from brqse_engine.abilities.effects_registry import EffectRegistry
        from brqse_engine.combat.mechanics import Combatant
        registry = EffectRegistry()
    except ImportError:
        print("CRITICAL: Could not import EffectRegistry from brqse_engine.abilities.effects_registry. Check your python path.")
        sys.exit(1)

# Dummy class to trick the registry into thinking it has a context
class MockCombatant:
    def __init__(self, name="Dummy"):
        self.name = name
        self.stats = {"Might": 10, "Knowledge": 10}
        self.hp = 10
        self.max_hp = 10
        # Mock status for effects that check flags
        self.status = None 
        # Or mock status manager methods?
        self.is_burning = False
        self.is_bleeding = False
        self.is_frozen = False
        self.is_staggered = False

    def apply_effect(self, *args, **kwargs):
        pass

def validate_csv(filepath):
    if not os.path.exists(filepath): return
    
    print(f"Scanning {os.path.basename(filepath)}...")
    issues = 0
    checked_count = 0
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            # force read to catch encoding errors early or handle BOM
            rows = list(reader)
    except Exception as e:
        print(f"  [ERROR] Check Failed for {os.path.basename(filepath)}: {e}")
        return

    for row in rows:
            # Check fields that might contain effects
            text_to_check = []
            if "Effect" in row and row["Effect"]: text_to_check.append(row["Effect"])
            if "Description" in row and row["Description"]: text_to_check.append(row["Description"])
            
            for text in text_to_check:
                checked_count += 1
                # Create a fake context
                ctx = {
                    "attacker": MockCombatant("Attacker"),
                    "target": MockCombatant("Target"),
                    "engine": None,
                    "log": [],
                    "tier": 1 # Default tier
                }
                
                # Attempt resolve
                try:
                    handled = registry.resolve(text, ctx)
                    if not handled:
                        # Common false positives? 
                        # Only warn if it looks like an effect (e.g. contains "Damage", "Apply", "Heal")
                        # But user wants STRICT validation.
                        print(f"  [FAIL] Unhandled Effect: '{text}' (in {row.get('Name', 'Unknown')})")
                        issues += 1
                except Exception as e:
                    print(f"  [ERROR] Crash on Effect: '{text}' -> {e}")
                    issues += 1

    if issues == 0:
        print(f"  [PASS] {os.path.basename(filepath)} ({checked_count} checks)")
    else:
        print(f"  [WARN] {os.path.basename(filepath)} had {issues} issues.")

def main():
    # Define your data directory
    # Script is in scripts/, so data is ../Data
    data_dir = os.path.join(os.path.dirname(__file__), "../Data")
    
    if not os.path.exists(data_dir):
        print(f"Data directory not found: {data_dir}")
        return

    files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
    for f in files:
        validate_csv(os.path.join(data_dir, f))

if __name__ == "__main__":
    main()

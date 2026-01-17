
import sys
import os

# Add the character builder directory to sys.path so we can import charcreate
sys.path.append(os.path.join(os.path.dirname(__file__), 'character builder'))

try:
    from charcreate import DataManager
except ImportError:
    # Fallback if running from within the directory
    sys.path.append(os.path.dirname(__file__))
    from charcreate import DataManager

def test_step_11_training(data):
    print("\n--- Testing Step 11: Training ---")
    weps = data.weapon_groups
    print(f"Loaded {len(weps)} weapon groups.")
    
    # Simulate logic
    try:
        melee = [r for r in weps if r.get("Type") == "Melee"]
        ranged = [r for r in weps if r.get("Type") == "Ranged"]
        
        print(f"Melee Groups: {len(melee)}")
        print(f"Ranged Groups: {len(ranged)}")
        
        for r in melee:
            print(f"Processing Melee: {r}")
            lbl = f"{r['Family Name']} ({r['Examples']})"
            tag = r['Family Name']
            
        for r in ranged:
            print(f"Processing Ranged: {r}")
            lbl = f"{r['Family Name']} ({r['Examples']})"
            tag = r['Family Name']
            
        print("Step 11 Logic: SUCCESS")
    except Exception as e:
        print(f"Step 11 Logic: FAILED - {e}")

def test_step_12_catalyst(data):
    try:
        utils = [r for r in data.all_skills if r.get("Type") == "Utility"]
        tools = data.tool_types
        
        with open("debug_log.txt", "w") as log:
            if tools:
                log.write(f"Tool[0] keys: {list(tools[0].keys())}\n")
            else:
                log.write("Zero tools loaded.\n")
            
            for r in utils:
                if 'Skill Name' not in r: log.write(f"WARNING: Missing 'Skill Name' in {r}\n")
                if 'Attribute' not in r: log.write(f"WARNING: Missing 'Attribute' in {r}\n")
                lbl = f"{r['Skill Name']} ({r['Attribute']})"
                
            for r in tools:
                if 'Tool_Name' not in r: log.write(f"WARNING: Missing 'Tool_Name' in {r}\n")
                if 'Attribute' not in r: log.write(f"WARNING: Missing 'Attribute' in {r}\n")
                lbl = f"{r['Tool_Name']} ({r['Attribute']})"
                
            log.write("Step 12 Logic: SUCCESS\n")
            print("Step 12 Logic: SUCCESS")
    except Exception as e:
        with open("debug_log.txt", "a") as log:
            log.write(f"Step 12 Logic: FAILED - {e}\n")
        print(f"Step 12 Logic: FAILED - {e}")

if __name__ == "__main__":
    print("Initializing DataManager...")
    dm = DataManager()
    test_step_11_training(dm)
    test_step_12_catalyst(dm)

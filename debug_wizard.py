
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
            # print(f"Processing Melee: {r}")
            lbl = f"{r['Family Name']} ({r['Examples']})"
            tag = r['Family Name']
            
        for r in ranged:
            # print(f"Processing Ranged: {r}")
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

def test_step_14_schools(data):
    try:
        schools = data.abilities["Schools"]
        with open("debug_log.txt", "a") as log:
            log.write("\n--- Testing Step 14: Schools ---\n")
            if schools:
                log.write(f"Schools[0] keys: {list(schools[0].keys())}\n")
            else:
                log.write("Zero schools loaded.\n")
            
            valid_schools = []
            seen_schools = set()
            
            # Mock stats for testing
            mock_stats = {"Might": 12, "Reflexes": 10, "Endurance": 14}
            
            for i, row in enumerate(schools):
                sch = row.get("School")
                if not sch:
                     log.write(f"Row {i} missing 'School'. Keys: {list(row.keys())}\n")
                     continue
                
                if sch in seen_schools: continue
                
                # Check Attribute Key
                if "Attribute" not in row:
                    log.write(f"Row {i} ({sch}) missing 'Attribute'\n")
                    continue
                
                attr = row["Attribute"]
                # Logic check
                if mock_stats.get(attr, 0) >= 12:
                    valid_schools.append(row)
                    seen_schools.add(sch)
            
            log.write(f"Found {len(valid_schools)} valid schools for mock stats.\n")
            log.write("Step 14 Logic: SUCCESS\n")
            print("Step 14 Logic: SUCCESS")
            
    except Exception as e:
        with open("debug_log.txt", "a") as log:
            log.write(f"Step 14 Logic: FAILED - {e}\n")
        print(f"Step 14 Logic: FAILED - {e}")

def test_step_15_gear(data):
    try:
        print("\n--- Testing Step 15: Gear ---")
        gear = data.gear
        print(f"Loaded {len(gear)} gear items.")
        
        # Determine valid items based on "Money" (100g)
        money = 100
        valid_items = []
        
        for i, item in enumerate(gear):
            if i == 0: print(f"Gear[0] Keys: {list(item.keys())}")
            # Check keys: "Item", "Cost", "Type"
            name = item.get("Item")
            cost_str = item.get("Cost", "999")
            wtype = item.get("Type")
            
            if not name:
                print(f"Row {i} missing 'Item'")
                continue
                
            try:
                cost = int(cost_str)
            except:
                # Handle "50 gp" or similar if present, though finding int is key
                cost = 999
            
            if cost <= money:
                 valid_items.append(item)
                 # Label generation check
                 label = f"{name} ({cost}g) - {wtype}"
        
        print(f"Valid Items found: {len(valid_items)}")
        print("Step 15 Logic: SUCCESS")

    except Exception as e:
        print(f"Step 15 Logic: FAILED - {e}")

    test_step_15_gear(dm)
    test_validation(dm)

def test_validation(data):
    print("\n--- Testing Validation Logic ---")
    from charcreate import CharacterBuilder
    builder = CharacterBuilder()
    
    # Test 1: Empty Name
    if builder.name == "Unknown":
        print("Validation Check: Name is initially 'Unknown'")
    
    # Mock validation logic check
    # Step 1 Requirement: Name != "Unknown" AND Species != ""
    valid_step_1 = builder.name != "Unknown" and builder.name != "" and builder.species != ""
    if not valid_step_1:
         print("Validation Logic Test: Correctly identified INVALID Step 1 (No Name/Species)")
    else:
         print("Validation Logic Test: FAILED (Allowed invalid Step 1)")

    # Test 2: Incomplete Evolution (Step 2)
    # Evo requires selecting 1 trait. 
    # Current trait count = 0
    valid_step_2 = len(builder.traits) >= 1 # Mocking logic for step 2
    if not valid_step_2:
        print("Validation Logic Test: Correctly identified INVALID Step 2 (No Traits)")

if __name__ == "__main__":
    print("Initializing DataManager...")
    dm = DataManager()
    # test_step_11_training(dm)
    # test_step_12_catalyst(dm)
    # test_step_14_schools(dm)
    # test_step_15_gear(dm)
    test_validation(dm)

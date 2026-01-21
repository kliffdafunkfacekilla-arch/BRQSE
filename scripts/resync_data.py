import csv
import json
import os
import glob

DATA_DIR = r"C:\Users\krazy\Desktop\BRQSE\Data"
OUTPUT_DIR = r"C:\Users\krazy\Desktop\BRQSE\Web_ui\public\data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Schema mapping for Right Side (Size) table
# Columns Q(16) to W(22) approx based on 0-index?
# 1_SIZE, SIZE 1, Tiny, ... 
# Let's verify index dynamically if possible, or hardcode based on inspection
# Recounting from inspection:
# 0:STEP, 1:Cat, 2:Name, 3:S1, 4:S2, 5:BP, 6:Mech
# 7,8,9: Empty?
# 10,11,12,13,14,15,16: References (Stat, Bio, Head...)
# 17: 1_SIZE (STEP)
# 18: SIZE 1 (Category)
# 19: Tiny (Option Name)
# 20: +2 Reflex... (Bio)
# 21: -2 Might... (Head)
# 22: Small Frame (Body Part)
# 23: Squeeze... (Mechanic)

# So Start Index = 17.

def read_csv_robust(path):
    encodings = ['utf-8', 'utf-8-sig', 'cp1252', 'latin1']
    for enc in encodings:
        try:
            with open(path, 'r', encoding=enc) as f:
                reader = csv.reader(f)
                return list(reader)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode {path} with any supported encoding.")

def convert_class_csv(input_path, output_path):
    print(f"Processing {os.path.basename(input_path)}...")
    items = []
    
    try:
        rows = read_csv_robust(input_path)
    except Exception as e:
        print(f"Error reading {input_path}: {e}")
        return

    if not rows:
        return

    # --- LEFT SIDE (Components) ---
    # Header is Row 0
    headers = rows[0][:7] # Take first 7 columns
        # Map headers to clean keys
        # STEP, Category, Option Name, Stat 1, Stat 2, Body Part, Mechanic / Trait
        
    # Process Left Side (Row 1+)
    for row in rows[1:]:
        if not row or not row[0].strip(): continue
        item = {}
        for i, h in enumerate(headers):
            if i < len(row):
                item[h.strip()] = row[i].strip()
        # Only add if STEP is valid
        if item.get('STEP'):
            items.append(item)

    # --- RIGHT SIDE (Sizes) ---
    # Data starts at Row 0!
    # Indices 16-22?
    # Spec is 15. 1_SIZE is 16.
    START_IDX = 16
    
    for row in rows:
        if len(row) <= START_IDX: continue
        
        # Check if there is data in the start column
        if not row[START_IDX].strip(): continue
        
        # Mapping
        size_item = {
            "STEP": row[START_IDX].strip(),
            "Category": row[START_IDX+1].strip() if len(row) > START_IDX+1 else "",
            "Option Name": row[START_IDX+2].strip() if len(row) > START_IDX+2 else "",
            "Bio": row[START_IDX+3].strip() if len(row) > START_IDX+3 else "", # +Stats
            "Head": row[START_IDX+4].strip() if len(row) > START_IDX+4 else "", # -Stats
            "Body Part": row[START_IDX+5].strip() if len(row) > START_IDX+5 else "",
            "Mechanic / Trait": row[START_IDX+6].strip() if len(row) > START_IDX+6 else ""
        }
        
        if size_item["STEP"]:
            items.append(size_item)

    # Save to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(items, f, indent=2)
    print(f"Saved {len(items)} items to {os.path.basename(output_path)}")

def convert_species_csv(input_path, output_path):
    # Simple direct conversion
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = list(reader)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"Saved Species data to {os.path.basename(output_path)}")


def main():
    # 1. Convert Species.csv
    convert_species_csv(
        os.path.join(DATA_DIR, "Species.csv"),
        os.path.join(OUTPUT_DIR, "Species.json")
    )
    
    # 2. Convert Class CSVs
    classes = ["Mammal", "Reptile", "Avian", "Insect", "Aquatic", "Plant"]
    for cls in classes:
        src = os.path.join(DATA_DIR, f"{cls}.csv")
        dst = os.path.join(OUTPUT_DIR, f"{cls}.json")
        if os.path.exists(src):
            convert_class_csv(src, dst)
        else:
            print(f"Warning: {src} not found")

if __name__ == "__main__":
    main()

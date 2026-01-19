import os
import csv
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "Data")
OUT_DIR = os.path.join(BASE_DIR, "Web_ui", "public", "data")

def convert_csv_to_json(filename):
    csv_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(csv_path):
        print(f"Skipping {filename}: Not found.")
        return

    json_filename = filename.replace(".csv", ".json")
    out_path = os.path.join(OUT_DIR, json_filename)

    data = []
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Basic cleaning: Remove empty keys
                clean_row = {k: v for k, v in row.items() if k and k.strip()}
                data.append(clean_row)
        
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
        print(f"Converted {filename} -> {json_filename} ({len(data)} records)")
    except Exception as e:
        print(f"Error converting {filename}: {e}")

def main():
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)
        
    print(f"Converting Data from {DATA_DIR} to {OUT_DIR}...")
    
    files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
    for f in files:
        convert_csv_to_json(f)
        
    print("Conversion Complete.")

if __name__ == "__main__":
    main()

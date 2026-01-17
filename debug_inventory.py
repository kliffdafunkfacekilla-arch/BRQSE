
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "combat simulator"))
from inventory_engine import Inventory

print("Initializing Inventory...")
inv = Inventory()
print(f"DB Size: {len(inv.db)}")
if len(inv.db) > 0:
    first_key = list(inv.db.keys())[0]
    print(f"Sample Key: '{first_key}'")
    print(f"Sample Data: {inv.db[first_key]}")
    
    print(f"Searching for 'Greatsword'...")
    if "Greatsword" in inv.db:
        print("Found Greatsword!")
    else:
        print("Greatsword NOT found. Keys start with:", list(inv.db.keys())[:5])

print("\nEquip Test:")
res = inv.equip("Greatsword")
print(f"Equip Result: {res}")
print(f"Main Hand: {inv.equipped['Main Hand']}")
if inv.equipped['Main Hand']:
    print(f"Item Name: {inv.equipped['Main Hand'].name}")

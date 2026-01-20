import os
import json
import glob

# Mapping of old names to new names
weapon_map = {
    'The Breakers': 'Great',
    'The Draw': 'Ballistics', 
    'The Blades': 'Small',
    'The Thrown': 'Thrown',
    'The Long Blade': 'Medium',
    'The Blast': 'Blast',
    'The Polearms': 'Large',
    'The Long Shot': 'Long Shot',
    'The Fist': 'Fist',
    'The Simple Shot': 'Simple',
    'The Shield': 'Shield',
    'Melee Exotics': 'Exotic Melee',
    'Ranged Exotics': 'Exotic Ranged',
}

armor_map = {
    'Plate': 'Heavy',
    'Leather': 'Light', 
    'Bio': 'Natural',
    'Robes': 'Cloth',
    'Rigs': 'Utility',
    'Mail': 'Medium',
}

all_maps = {**weapon_map, **armor_map}

# Files to update
files = [
    'Web_ui/public/data/weapons_and_armor.json',
    'Web_ui/public/data/Skills.json',
    'Data/chaos_core.json',
]

# Add character saves
saves = glob.glob('brqse_engine/Saves/*.json')
files.extend(saves)

for fpath in files:
    if not os.path.exists(fpath):
        print(f'SKIP: {fpath}')
        continue
    
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    changed = False
    for old, new in all_maps.items():
        if f'"{old}"' in content:
            content = content.replace(f'"{old}"', f'"{new}"')
            changed = True
    
    if changed:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'UPDATED: {fpath}')
    else:
        print(f'NO CHANGES: {fpath}')

print('Done!')

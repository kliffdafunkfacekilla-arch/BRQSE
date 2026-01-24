import os

files = [
    r"c:\Users\krazy\Desktop\BRQSE\Web_ui\public\objects\barrel.png",
    r"c:\Users\krazy\Desktop\BRQSE\Web_ui\public\objects\crate.png",
    r"c:\Users\krazy\Desktop\BRQSE\Web_ui\public\objects\chest.png",
    r"c:\Users\krazy\Desktop\BRQSE\Web_ui\public\objects\table.png",
]

for f in files:
    if not os.path.exists(f):
        print(f"MISSING: {f}")
        continue
        
    size = os.path.getsize(f)
    print(f"{os.path.basename(f)}: {size} bytes")
    
    with open(f, 'rb') as img:
        header = img.read(8)
        # PNG signature: 89 50 4E 47 0D 0A 1A 0A
        if header == b'\x89PNG\r\n\x1a\n':
            print("  Header: VALID PNG")
        else:
            print(f"  Header: INVALID ({header})")

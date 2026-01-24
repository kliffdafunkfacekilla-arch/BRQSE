from PIL import Image
import os

def make_transparent(input_path, output_path):
    try:
        img = Image.open(input_path)
        img = img.convert("RGBA")
        datas = img.getdata()
        
        # Assumption: Background is white-ish or black-ish or checkerboard?
        # Since they were generated pixel art, they might have a solid color.
        # Let's verify the corner pixel.
        bg_color = img.getpixel((0, 0))
        
        new_data = []
        for item in datas:
            # Simple tolerance check
            if abs(item[0] - bg_color[0]) < 15 and abs(item[1] - bg_color[1]) < 15 and abs(item[2] - bg_color[2]) < 15:
                new_data.append((255, 255, 255, 0)) # Transparent
            else:
                new_data.append(item)
                
        img.putdata(new_data)
        img.save(output_path, "PNG")
        print(f"Processed {os.path.basename(input_path)} -> PNG")
    except Exception as e:
        print(f"Failed to process {input_path}: {e}")

base_dir = r"c:\Users\krazy\Desktop\BRQSE\Web_ui\public\objects"
files = ["barrel.jpg", "crate.jpg", "chest.jpg", "table.jpg"]

for f in files:
    in_p = os.path.join(base_dir, f)
    out_p = os.path.join(base_dir, f.replace(".jpg", ".png"))
    if os.path.exists(in_p):
        make_transparent(in_p, out_p)
    else:
        print(f"Not found: {in_p}")

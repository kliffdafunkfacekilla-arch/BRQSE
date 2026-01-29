from PIL import Image
import os
import sys
import argparse

def process_spritesheet(input_path, output_dir, target_w=1024, target_h=2048, sprite_size=128):
    """
    Normalizes a spritesheet to a specific size and slices it into uniform tiles.
    """
    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        # Load
        img = Image.open(input_path).convert("RGBA")
        orig_w, orig_h = img.size
        print(f"Original Size: {orig_w}x{orig_h}")

        # Transparency Check (Sample a 64x64 block for checkerboard colors)
        sample_size = 64
        sample_patch = list(img.crop((0, 0, sample_size, sample_size)).getdata())
        from collections import Counter
        # Take the top 2 most common colors (the two checkerboard tones)
        bg_candidates = [c[0] for c in Counter(sample_patch).most_common(2)]
        
        print(f"Applying transparency based on detected checkerboard tones: {bg_candidates}")
        datas = img.getdata()
        new_data = []
        tolerance = 45 
        
        # Memoization set for performance
        is_bg_cache = {}

        for item in datas:
            rgb = item[:3]
            if rgb in is_bg_cache:
                is_bg = is_bg_cache[rgb]
            else:
                is_bg = False
                for bg_color in bg_candidates:
                    if all(abs(rgb[i] - bg_color[i]) < tolerance for i in range(3)):
                        is_bg = True
                        break
                is_bg_cache[rgb] = is_bg
            
            if is_bg:
                new_data.append((0, 0, 0, 0))
            else:
                new_data.append(item)
        img.putdata(new_data)
        
        # Resize AFTER transparency
        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        print(f"Normalized to: {img.size}")

        # Slicing
        cols = target_w // sprite_size
        rows = target_h // sprite_size
        print(f"Slicing into {cols}x{rows} grid ({sprite_size}px tiles)...")

        base_name = os.path.splitext(os.path.basename(input_path))[0]
        count = 0

        for r in range(rows):
            for c in range(cols):
                left = c * sprite_size
                top = r * sprite_size
                right = left + sprite_size
                bottom = top + sprite_size
                
                sprite = img.crop((left, top, right, bottom))
                
                # Only save if the sprite isn't completely empty (optional)
                # if sprite.getextrema()[3][1] > 0: 
                
                fpath = os.path.join(output_dir, f"{base_name}_{count:03d}.png")
                sprite.save(fpath, "PNG")
                count += 1

        print(f"Successfully exported {count} sprites to: {output_dir}")

    except Exception as e:
        print(f"System Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BRQSE Sprite Sheet Processor")
    parser.add_argument("input", help="Path to input sprite sheet image")
    parser.add_argument("--output", default="output_sprites", help="Directory to save slices")
    parser.add_argument("--width", type=int, default=1024, help="Target Sheet Width")
    parser.add_argument("--height", type=int, default=2048, help="Target Sheet Height")
    parser.add_argument("--size", type=int, default=128, help="Sprite Tile Size")

    args = parser.parse_args()
    process_spritesheet(args.input, args.output, args.width, args.height, args.size)

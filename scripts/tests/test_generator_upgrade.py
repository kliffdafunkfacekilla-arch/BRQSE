
import unittest
import sys
import os

# Add project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from brqse_engine.world.donjon_generator import DonjonGenerator, Cell

class TestGeneratorUpgrade(unittest.TestCase):
    def test_feature_presence(self):
        print("\n=== Testing Donjon Generator Features ===")
        dg = DonjonGenerator()
        
        # Test 10 maps
        feature_counts = {
            "ARCH": 0, "DOOR": 0, "LOCKED": 0, "TRAPPED": 0, "SECRET": 0, "PORTC": 0,
            "STAIR_UP": 0, "STAIR_DN": 0
        }
        
        for i in range(10):
            data = dg.generate(width=31, height=31)
            grid = data["grid"]
            rows = data["height"]
            cols = data["width"]
            
            for r in range(rows):
                for c in range(cols):
                    cell = grid[r][c]
                    if cell & Cell.ARCH: feature_counts["ARCH"] += 1
                    if cell & Cell.DOOR and not (cell & Cell.LOCKED): feature_counts["DOOR"] += 1
                    if cell & Cell.LOCKED: feature_counts["LOCKED"] += 1
                    if cell & Cell.TRAPPED: feature_counts["TRAPPED"] += 1
                    if cell & Cell.SECRET: feature_counts["SECRET"] += 1
                    if cell & Cell.PORTC: feature_counts["PORTC"] += 1
                    if cell & Cell.STAIR_UP: feature_counts["STAIR_UP"] += 1
                    if cell & Cell.STAIR_DN: feature_counts["STAIR_DN"] += 1
        
        print("Feature Counts over 10 Maps:")
        for k, v in feature_counts.items():
            print(f"  - {k}: {v}")
            # We expect at least SOME of each, usually.
            # Locked/Trapped might be rare? 15% of doors.
            # Stairs should be approx 10 each (1 up/1 down per map)
            
        self.assertGreater(feature_counts["DOOR"], 0, "Should have doors")
        self.assertGreater(feature_counts["STAIR_UP"], 0, "Should have Up Stairs")
        self.assertGreater(feature_counts["STAIR_DN"], 0, "Should have Down Stairs")

if __name__ == '__main__':
    unittest.main()

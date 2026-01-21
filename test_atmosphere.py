"""Test atmosphere modifiers"""
import sys
sys.path.insert(0, ".")
from scripts.world_engine import ChaosManager

cm = ChaosManager()
print(f"Clock 0: {cm.get_atmosphere()['tone']}")

cm.chaos_clock = 5
print(f"Clock 5: {cm.get_atmosphere()['tone']}")

cm.chaos_clock = 10
print(f"Clock 10: {cm.get_atmosphere()['tone']}")

cm.chaos_clock = 12
print(f"Clock 12: {cm.get_atmosphere()['tone']}")
print(f"Is Doomed: {cm.is_doomed}")
print(f"Descriptor: {cm.get_atmosphere()['descriptor']}")

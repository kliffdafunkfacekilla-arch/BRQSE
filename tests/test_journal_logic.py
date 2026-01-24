import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "c:/Users/krazy/Desktop/BRQSE"))

from scripts.world_engine import SceneStack, ChaosManager

def test_quest_metadata():
    print("--- Testing Quest Metadata ---")
    cm = ChaosManager()
    ss = SceneStack(cm)
    
    ss.generate_quest("CAVES")
    
    print(f"Quest Title: {ss.quest_title}")
    print(f"Quest Description: {ss.quest_description}")
    print(f"Total Steps: {ss.total_steps}")
    
    assert "Caves" in ss.quest_title
    assert len(ss.quest_description) > 10
    assert ss.total_steps > 0
    
    # Test progress
    initial_stack_size = len(ss.stack)
    ss.advance()
    new_stack_size = len(ss.stack)
    
    print(f"Steps Remaining: {new_stack_size} / {ss.total_steps}")
    assert new_stack_size == initial_stack_size - 1
    
    print("Pass: Quest metadata and progress tracking are valid.")

if __name__ == "__main__":
    test_quest_metadata()

import sys
import os
import unittest
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from brqse_engine.models.entity import Entity
from brqse_engine.core.interaction import InteractionEngine

class MockLogger:
    def log(self, *args, **kwargs):
        pass

class TestTagSystem(unittest.TestCase):
    def setUp(self):
        self.logger = MockLogger()
        self.engine = InteractionEngine(self.logger)
        
        # ACTOR
        self.actor = Entity("Hero", 0, 0)
        self.actor.inventory = [] # Duck typing for ActorWrapper
    
    def test_pickup(self):
        gold = Entity("Gold Coin", 5, 5)
        gold.add_tag("pickup")
        
        result = self.engine.interact(self.actor, gold)
        
        self.assertIn("picked up", result)
        self.assertTrue(gold.has_tag("carried"))
        self.assertIn(gold, self.actor.inventory)

    def test_locked_container_fail(self):
        chest = Entity("Chest", 10, 10)
        chest.add_tag("container")
        chest.add_tag("locked", required_key="key_1")
        
        result = self.engine.interact(self.actor, chest)
        
        self.assertIn("locked", result)
        self.assertFalse(chest.has_tag("open"))

    def test_locked_container_success(self):
        # 1. Create Chest
        chest = Entity("Chest", 10, 10)
        chest.add_tag("container")
        chest.add_tag("locked", required_key="key_1")
        
        # 2. Give Key
        key = Entity("Iron Key", 0, 0)
        key.add_tag("key_1") # ID matches required_key
        key.data["id"] = "key_1"
        self.actor.inventory.append(key)
        
        # 3. Simulate unlocking
        # Note: InteractionEngine expects inventory items to be capable of checking against key_id
        # Our engine looks for: 
        #   any(i.data.get("id") == key_id for i in actor.inventory)
        #   OR any(i.has_tag(key_id) ...)
        
        result = self.engine.interact(self.actor, chest)
        
        self.assertIn("unlock", result)
        self.assertTrue(chest.has_tag("open"))
        self.assertFalse(chest.has_tag("locked"))

if __name__ == "__main__":
    unittest.main()

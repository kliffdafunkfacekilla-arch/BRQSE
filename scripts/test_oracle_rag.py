import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brqse_engine.core.oracle import DungeonOracle
from brqse_engine.core.sensory_layer import SensoryLayer
from brqse_engine.models.entity import Entity

class MockGameState:
    def __init__(self):
        self.player = Entity("Hero", 10, 10, data={"hp": 20, "max_hp": 20})
        self.current_depth = 1
        self.inventory = [Entity("Rusty Key", 0,0), Entity("Torch", 0,0)]
        self.objects = [
            Entity("Chest", 12, 12, tags={"container", "locked"}),
            Entity("Goblin", 15, 15, tags={"enemy"})
        ]
        self.logger = MagicMock()
        self.logger.get_context.return_value = [
            {"text": "You hear a growl.", "tags": {"room": 1}},
            {"text": "You see a chest.", "tags": {"room": 1}}
        ]

class TestOracleRAG(unittest.TestCase):
    def setUp(self):
        self.sensory = SensoryLayer()
        # Mock the requests.post method on the sensory layer (or rather the module it uses)
        # But consult_oracle imports requests inside the method.
        # We'll mock consult_oracle directly to verify prompt construction if we want, 
        # or we can patch requests.
        self.oracle = DungeonOracle(self.sensory)
        self.game_state = MockGameState()

    @patch('brqse_engine.core.sensory_layer.requests.post')
    def test_consult_rag_prompt(self, mock_post):
        # Setup Mock Response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "The key is in the chest."}}
        mock_post.return_value = mock_response

        # Execute
        response = self.oracle.consult("Where is the key?", self.game_state)
        
        # Verify
        print(f"\n[Test] Oracle Response: {response}")
        self.assertEqual(response, "The key is in the chest.")
        
        # Check Prompt Content
        args, kwargs = mock_post.call_args
        payload = kwargs['json']
        system_prompt = payload['messages'][0]['content']
        
        print(f"[Test] Generated Prompt:\n{system_prompt}")
        
        # Assertions
        self.assertIn("Rusty Key", system_prompt)
        self.assertIn("Chest", system_prompt)
        self.assertIn("Goblin", system_prompt)
        self.assertIn("You hear a growl", system_prompt)

    def test_inspect_entity(self):
        entity = Entity("Mysterious Orb", 0, 0, tags={"valuable", "magic"})
        desc = self.oracle.inspect_entity(entity, [{"text": "The Orb glows.", "tags": {"item_id": entity.data["id"]}}])
        print(f"\n[Test] Inspect Description: {desc}")
        self.assertIn("glitters with value", desc)
        self.assertIn("The Orb glows", desc)

if __name__ == '__main__':
    unittest.main()

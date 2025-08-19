"""
Essential RAG helper tests.
Kept only the most critical functionality tests.
"""
import unittest
from counter_strike_ag2_agent.rag import RagTerroristHelper
from counter_strike_ag2_agent.game_state import GameState


class TestRagTerroristHelper(unittest.TestCase):
    """Test essential RAG helper functionality."""
    
    def setUp(self):
        self.state = GameState()
    
    def test_build_facts_basic(self):
        """Test fact building works."""
        facts = RagTerroristHelper.build_facts(self.state)
        self.assertIn("💣 Bomb not planted.", facts)
        self.assertTrue(any(f.startswith("T alive:") for f in facts))
    
    def test_answer_basic_queries(self):
        """Test basic query responses."""
        # Bomb location
        answer = RagTerroristHelper.answer("where is the bomb?", self.state)
        self.assertIn("not planted", answer.lower())
        
        # Strategy
        answer = RagTerroristHelper.answer("what should we do?", self.state)
        self.assertIn("plant", answer.lower())
        
        # Fallback
        answer = RagTerroristHelper.answer("random question", self.state)
        self.assertIn("Facts:", answer)
    
    def test_state_adaptation(self):
        """Test RAG adapts to game state changes."""
        # Before bomb plant
        answer1 = RagTerroristHelper.answer("strategy?", self.state)
        
        # After bomb plant
        self.state.bomb_planted = True
        self.state.bomb_site = "A-site"
        answer2 = RagTerroristHelper.answer("strategy?", self.state)
        
        self.assertNotEqual(answer1, answer2)
        self.assertIn("crossfire", answer2.lower())


if __name__ == "__main__":
    unittest.main()

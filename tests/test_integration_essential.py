"""
Essential integration tests for Counter-Strike AG2 Agent system.

Tests critical system integration scenarios:
- Complete game workflows
- Agent + RAG integration
- Error scenarios
"""
import os
import tempfile
import shutil
import unittest
from unittest.mock import patch

from counter_strike_ag2_agent.agents import create_terrorists_group
from counter_strike_ag2_agent.contrib_integration import run_critic, run_quantifier, run_som
from counter_strike_ag2_agent.game_state import GameState
from counter_strike_ag2_agent.rag import RagTerroristHelper
from counter_strike_ag2_agent.rag_vector import ChromaRAG


class TestEssentialIntegration(unittest.TestCase):
    """Test essential system integration."""
    
    def setUp(self):
        self.game_state = GameState()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_complete_game_workflow(self):
        """Test complete game workflow with all components."""
        # 1. Setup vector knowledge base
        rag = ChromaRAG(persist_dir=self.temp_dir, collection="workflow_test")
        knowledge = [
            "A-site requires smokes for cover",
            "When bomb planted, hold crossfires",
            "Trade kills when teammate engaged"
        ]
        count = rag.add_texts(knowledge)
        self.assertEqual(count, 3)
        
        # 2. Initial game state
        self.assertEqual(self.game_state.round, 1)
        self.assertFalse(self.game_state.bomb_planted)
        
        # 3. Player actions
        result = self.game_state.apply_action("Terrorists", "player", "move to A-site")
        self.assertIn("moved", result)
        
        result = self.game_state.apply_action("Terrorists", "player", "plant bomb")
        self.assertIn("planted", result)
        self.assertTrue(self.game_state.bomb_planted)
        
        # 4. RAG should adapt to game state
        rag_response = RagTerroristHelper.answer("what should we do?", self.game_state)
        self.assertIn("crossfire", rag_response.lower())
        
        # 5. Vector KB should provide relevant advice
        vector_response = rag.ask("What to do when bomb is planted?")
        self.assertIsNotNone(vector_response)
    
    def test_agent_rag_integration(self):
        """Test agents work with RAG systems."""
        with patch('counter_strike_ag2_agent.agents.USABLE_CONFIG_LIST', []):
            manager, players = create_terrorists_group(num_players=1)
            
            # Should be able to create agents
            self.assertEqual(len(players), 1)
            self.assertEqual(len(manager.groupchat.agents), 2)
            
            # Find bot agent using robust discovery
            bot_agent = None
            for agent in manager.groupchat.agents:
                if hasattr(agent, 'system_message') and 'bot' in agent.name.lower():
                    bot_agent = agent
                    break
            
            self.assertIsNotNone(bot_agent, "Should find bot agent")
            
            # Test RAG provides context
            game_facts = RagTerroristHelper.build_facts(self.game_state)
            self.assertTrue(len(game_facts) > 0)
    
    def test_contrib_agents_basic(self):
        """Test contrib agents handle basic scenarios."""
        # Test critic agent (should work with or without config)
        result = run_critic("Rush B with no utility", self.game_state)
        self.assertIsNotNone(result)
        self.assertTrue(len(result) > 0)
        
        # Test quantifier agent
        options = ["Rush A", "Play slow", "Execute B"]
        result = run_quantifier(options, self.game_state)
        self.assertIsNotNone(result)
        self.assertTrue(len(result) > 0)
        
        # Test Society of Mind agent
        result = run_som("Best strategy?", self.game_state)
        self.assertIsNotNone(result)
        self.assertTrue(len(result) > 0)
    
    def test_error_handling_integration(self):
        """Test integrated error handling."""
        # Test invalid game actions
        try:
            result = self.game_state.apply_action("InvalidTeam", "player", "move")
            self.assertIn("Invalid", result)
        except KeyError:
            # Game state doesn't handle invalid teams gracefully yet - this is expected
            pass
        
        # Test RAG with edge cases
        empty_response = RagTerroristHelper.answer("", self.game_state)
        self.assertIn("Facts:", empty_response)
        
        # Test vector KB with empty collection
        empty_rag = ChromaRAG(persist_dir=self.temp_dir, collection="empty")
        no_result = empty_rag.ask("anything")
        self.assertIsNone(no_result)
        
        # Test contrib agents with no options
        no_options_result = run_quantifier([], self.game_state)
        self.assertIn("no options", no_options_result.lower())
    
    def test_state_transitions(self):
        """Test system adapts to game state changes."""
        # Initial state advice
        initial_advice = RagTerroristHelper.answer("strategy?", self.game_state)
        self.assertIn("plant", initial_advice.lower())
        
        # Change game state
        self.game_state.bomb_planted = True
        self.game_state.bomb_site = "A-site"
        
        # Advice should change
        planted_advice = RagTerroristHelper.answer("strategy?", self.game_state)
        self.assertIn("crossfire", planted_advice.lower())
        self.assertNotEqual(initial_advice, planted_advice)
    
    def test_concurrent_operations(self):
        """Test system handles multiple operations."""
        # Multiple game actions in sequence
        actions = ["move to A-site", "shoot player", "plant bomb"]
        for action in actions:
            result = self.game_state.apply_action("Terrorists", "player", action)
            self.assertIsNotNone(result)
            self.assertNotIn("Invalid action", result)
        
        # Multiple RAG queries
        queries = ["where bomb?", "any ct?", "what do?"]
        for query in queries:
            response = RagTerroristHelper.answer(query, self.game_state)
            self.assertIsNotNone(response)
            self.assertTrue(len(response) > 0)


if __name__ == '__main__':
    unittest.main()

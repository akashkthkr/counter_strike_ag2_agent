"""
Essential AG2 agent tests for Counter-Strike AG2 Agent system.

Tests only the most critical agent functionality:
- Agent creation and configuration
- Basic agent interactions
- Error handling
"""
import os
import unittest
from unittest.mock import patch

from counter_strike_ag2_agent.agents import (
    create_team, create_terrorists_group, get_user_agent,
    _load_config_list, get_active_providers
)
from counter_strike_ag2_agent.game_state import GameState


class TestEssentialAgents(unittest.TestCase):
    """Test essential AG2 agent functionality."""
    
    def setUp(self):
        self.game_state = GameState()
        # Clear environment for clean testing
        self.original_env = {}
        for key in ['OAI_CONFIG_LIST', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY']:
            self.original_env[key] = os.environ.get(key)
            if key in os.environ:
                del os.environ[key]
    
    def tearDown(self):
        # Restore original environment
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]
    
    def test_config_loading_basic(self):
        """Test basic configuration loading."""
        # Test with no config
        config = _load_config_list()
        self.assertEqual(config, [])
        
        # Test with Anthropic key
        os.environ['ANTHROPIC_API_KEY'] = 'test-key'
        config = _load_config_list()
        self.assertEqual(len(config), 1)
        self.assertEqual(config[0]['api_type'], 'anthropic')
    
    def test_team_creation_basic(self):
        """Test basic team creation works."""
        with patch('counter_strike_ag2_agent.agents.USABLE_CONFIG_LIST', []):
            manager = create_team("Terrorists", is_terrorists=True)
            
            self.assertIsNotNone(manager)
            self.assertEqual(len(manager.groupchat.agents), 2)  # player + bot
            
            # Test user agent exists
            user_agent = get_user_agent(manager)
            self.assertIsNotNone(user_agent)
            self.assertEqual(user_agent.human_input_mode, "NEVER")
    
    def test_terrorists_group_creation(self):
        """Test terrorists group creation with multiple players."""
        with patch('counter_strike_ag2_agent.agents.USABLE_CONFIG_LIST', []):
            manager, players = create_terrorists_group(num_players=2)
            
            self.assertIsNotNone(manager)
            self.assertEqual(len(players), 2)
            self.assertEqual(len(manager.groupchat.agents), 3)  # 2 players + 1 bot
            
            # All players should be UserProxyAgent
            for player in players:
                self.assertEqual(player.human_input_mode, "NEVER")
    
    def test_agent_discovery_robust(self):
        """Test robust agent discovery (not hardcoded indices)."""
        with patch('counter_strike_ag2_agent.agents.USABLE_CONFIG_LIST', []):
            manager, _ = create_terrorists_group(num_players=3)
            
            # Test that we can find bot agent by characteristics, not index
            bot_agent = None
            for agent in manager.groupchat.agents:
                if hasattr(agent, 'system_message') and 'bot' in agent.name.lower():
                    bot_agent = agent
                    break
            
            self.assertIsNotNone(bot_agent, "Should be able to find bot agent by name/properties")
    
    def test_active_providers(self):
        """Test getting active providers."""
        providers = get_active_providers()
        self.assertIsInstance(providers, list)
        
        # With API key should have providers
        os.environ['ANTHROPIC_API_KEY'] = 'test-key'
        providers = get_active_providers()
        self.assertGreater(len(providers), 0)
    
    def test_agent_system_messages(self):
        """Test agents have appropriate system messages."""
        with patch('counter_strike_ag2_agent.agents.USABLE_CONFIG_LIST', []):
            manager = create_team("Terrorists", is_terrorists=True)
            
            # Find bot agent
            bot_agent = None
            for agent in manager.groupchat.agents:
                if hasattr(agent, 'system_message'):
                    bot_agent = agent
                    break
            
            self.assertIsNotNone(bot_agent)
            # System message should exist and be concise (if configured)
            if bot_agent.system_message:
                self.assertIn("short", bot_agent.system_message.lower())


class TestAgentErrorHandling(unittest.TestCase):
    """Test agent error handling and fallbacks."""
    
    def test_no_config_fallback(self):
        """Test system works without LLM configuration."""
        # Ensure no config available
        for key in ['OAI_CONFIG_LIST', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY']:
            if key in os.environ:
                del os.environ[key]
        
        config = _load_config_list()
        self.assertEqual(config, [])
        
        # Should still be able to create agents (they just won't have LLM access)
        manager = create_team("Terrorists", is_terrorists=True)
        self.assertIsNotNone(manager)
    
    def test_minimum_players(self):
        """Test minimum player requirements."""
        manager, players = create_terrorists_group(num_players=0)
        self.assertEqual(len(players), 1)  # Should default to 1
        
        manager, players = create_terrorists_group(num_players=1)
        self.assertEqual(len(players), 1)


if __name__ == '__main__':
    unittest.main()

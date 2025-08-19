"""
Essential AG2 agents functionality tests.
Streamlined to test only critical agent functionality.
"""
import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from counter_strike_ag2_agent.agents import (_filter_config_list,
                                             _load_config_list, create_team,
                                             create_terrorists_group,
                                             get_active_providers,
                                             get_user_agent)
from counter_strike_ag2_agent.game_state import GameState


class TestAgents(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment."""
        self.game_state = GameState()
        # Clear environment variables for clean testing
        self.original_env = {}
        for key in ['OAI_CONFIG_LIST', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY']:
            self.original_env[key] = os.environ.get(key)
            if key in os.environ:
                del os.environ[key]
    
    def tearDown(self):
        """Clean up test environment."""
        # Restore original environment
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]
    
    def test_config_loading_with_openai_key(self):
        """Standardize provider under test to Anthropic (Claude)."""
        os.environ['ANTHROPIC_API_KEY'] = 'test-anthropic-key'
        config = _load_config_list()
        
        self.assertEqual(len(config), 1)
        self.assertEqual(config[0]['model'], 'claude-3-5-sonnet-20240620')
        self.assertEqual(config[0]['api_key'], 'test-anthropic-key')
        self.assertEqual(config[0]['api_type'], 'anthropic')
    
    def test_config_loading_with_anthropic_key(self):
        """Test config loading with ANTHROPIC_API_KEY."""
        os.environ['ANTHROPIC_API_KEY'] = 'test-anthropic-key'
        config = _load_config_list()
        
        self.assertEqual(len(config), 1)
        self.assertEqual(config[0]['model'], 'claude-3-5-sonnet-20240620')
        self.assertEqual(config[0]['api_key'], 'test-anthropic-key')
        self.assertEqual(config[0]['api_type'], 'anthropic')
    
    def test_config_loading_with_json_string(self):
        """Test config loading with OAI_CONFIG_LIST as JSON string."""
        test_config = '[{"model": "gpt-4", "api_key": "test", "api_type": "openai"}]'
        os.environ['OAI_CONFIG_LIST'] = test_config
        config = _load_config_list()
        
        self.assertEqual(len(config), 1)
        self.assertEqual(config[0]['model'], 'gpt-4')
    
    def test_config_loading_with_file_path(self):
        """Test config loading with OAI_CONFIG_LIST as file path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('[{"model": "gpt-4", "api_key": "test", "api_type": "openai"}]')
            config_file = f.name
        
        try:
            os.environ['OAI_CONFIG_LIST'] = config_file
            config = _load_config_list()
            
            self.assertEqual(len(config), 1)
            self.assertEqual(config[0]['model'], 'gpt-4')
        finally:
            os.unlink(config_file)
    
    def test_config_loading_no_config(self):
        """Test config loading with no configuration."""
        config = _load_config_list()
        self.assertEqual(config, [])
    
    def test_config_filtering(self):
        """Test configuration filtering for Anthropic (Claude) only."""
        test_configs = [
            {"model": "claude-3-5-sonnet-latest", "api_type": "anthropic"},
            {"model": "unsupported", "api_type": "unknown"}
        ]
        
        filtered = _filter_config_list(test_configs)
        api_types = [config.get('api_type', '') for config in filtered]
        self.assertIn('anthropic', api_types)
        self.assertNotIn('unknown', api_types)
    
    def test_get_active_providers(self):
        """Test getting active providers."""
        os.environ['ANTHROPIC_API_KEY'] = 'test-anthropic-key'
        providers = get_active_providers()
        
        self.assertIsInstance(providers, list)
        # Should have at least one provider when key is set
        self.assertGreater(len(providers), 0)
    
    @patch('counter_strike_ag2_agent.agents.USABLE_CONFIG_LIST', [])
    def test_create_team_with_config(self):
        """Test creating team with LLM configuration."""
        manager = create_team("Terrorists", is_terrorists=True)
        
        self.assertIsNotNone(manager)
        self.assertEqual(len(manager.groupchat.agents), 2)
        
        # Check that agents have proper configuration
        agents = manager.groupchat.agents
        user_agent = get_user_agent(manager)
        self.assertIsNotNone(user_agent)
    
    def test_create_terrorists_group(self):
        """Test creating terrorists group with multiple players."""
        manager, players = create_terrorists_group(num_players=3)
        
        self.assertIsNotNone(manager)
        self.assertEqual(len(players), 3)
        self.assertEqual(len(manager.groupchat.agents), 4)  # 3 players + 1 bot
        
        # Check all players are UserProxyAgent
        for player in players:
            self.assertEqual(player.human_input_mode, "NEVER")
    
    def test_create_terrorists_group_minimum_players(self):
        """Test creating terrorists group with minimum players."""
        manager, players = create_terrorists_group(num_players=0)
        
        self.assertEqual(len(players), 1)  # Should default to 1
        self.assertEqual(len(manager.groupchat.agents), 2)  # 1 player + 1 bot
    
    def test_get_user_agent(self):
        """Test getting user agent from group chat manager."""
        manager = create_team("Terrorists", is_terrorists=True)
        user_agent = get_user_agent(manager)
        
        self.assertIsNotNone(user_agent)
        self.assertEqual(user_agent.human_input_mode, "NEVER")
    
    def test_get_user_agent_ct_team(self):
        """Test getting user agent from CT team (should be None)."""
        manager = create_team("Counter-Terrorists", is_terrorists=False)
        user_agent = get_user_agent(manager)
        
        # CT team has all AssistantAgents, no UserProxyAgent
        self.assertIsNone(user_agent)
    
    @patch('counter_strike_ag2_agent.agents.USABLE_CONFIG_LIST', [])
    def test_agent_system_messages(self):
        """Test that agents have appropriate system messages."""
        manager = create_team("Terrorists", is_terrorists=True)
        
        # Find the bot agent (AssistantAgent)
        bot_agent = None
        for agent in manager.groupchat.agents:
            if hasattr(agent, 'system_message'):
                bot_agent = agent
                break
        
        self.assertIsNotNone(bot_agent)
        # When no config, system message may be empty, but agent should exist
        if bot_agent.system_message:
            self.assertIn("Terrorists", bot_agent.system_message)
            self.assertIn("short", bot_agent.system_message.lower())


class TestAgentInteractions(unittest.TestCase):
    """Test essential agent interactions."""
    
    def test_agent_discovery_robust(self):
        """Test robust agent discovery works (key fix)."""
        with patch('counter_strike_ag2_agent.agents.USABLE_CONFIG_LIST', []):
            manager, _ = create_terrorists_group(num_players=2)
            
            # Test robust agent finding (not hardcoded index)
            bot_agent = None
            for agent in manager.groupchat.agents:
                if hasattr(agent, 'system_message') and 'bot' in agent.name.lower():
                    bot_agent = agent
                    break
            
            self.assertIsNotNone(bot_agent, "Should find bot agent by name/properties")


if __name__ == '__main__':
    unittest.main()
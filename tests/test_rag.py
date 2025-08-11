import unittest
from unittest.mock import Mock, patch
from counter_strike_ag2_agent.rag import RagTerroristHelper
from counter_strike_ag2_agent.game_state import GameState


class TestRagTerroristHelper(unittest.TestCase):
    
    def setUp(self):
        self.state = GameState()
        
    def test_build_facts_initial_state(self):
        facts = RagTerroristHelper.build_facts(self.state)
        self.assertIn("💣 Bomb not planted.", facts)
        self.assertTrue(any(f.startswith("T alive:") for f in facts))
        self.assertTrue(any(f.startswith("CT alive:") for f in facts))
        
    def test_build_facts_bomb_planted(self):
        self.state.bomb_planted = True
        self.state.bomb_site = "A-site"
        facts = RagTerroristHelper.build_facts(self.state)
        self.assertIn("💣 BOMB PLANTED at A-site!", facts)
        
    def test_build_facts_players_dead(self):
        self.state.player_health["Terrorists"]["player"] = 0
        self.state.player_health["Counter-Terrorists"]["bot"] = 0
        facts = RagTerroristHelper.build_facts(self.state)
        self.assertIn("T alive: bot(100HP)", facts)
        self.assertIn("CT alive: player(100HP)", facts)
        self.assertIn("T dead: player", facts)
        self.assertIn("CT dead: bot", facts)
        
    def test_build_facts_all_dead(self):
        self.state.player_health["Terrorists"]["player"] = 0
        self.state.player_health["Terrorists"]["bot"] = 0
        facts = RagTerroristHelper.build_facts(self.state)
        self.assertIn("T dead: player, bot", facts)
        self.assertTrue(not any(f.startswith("T alive:") for f in facts))
        
    def test_answer_bomb_site_question_not_planted(self):
        answer = RagTerroristHelper.answer("where is the bomb?", self.state)
        self.assertIn("not planted", answer.lower())
        
    def test_answer_bomb_site_question_planted(self):
        self.state.bomb_planted = True
        self.state.bomb_site = "B-site"
        answer = RagTerroristHelper.answer("where is bomb planted?", self.state)
        self.assertIn("B-site", answer)
        
    def test_answer_ct_threat_no_cts(self):
        self.state.player_health["Counter-Terrorists"]["player"] = 0
        self.state.player_health["Counter-Terrorists"]["bot"] = 0
        answer = RagTerroristHelper.answer("are there any CTs near?", self.state)
        self.assertIn("No CTs alive", answer)
        
    def test_answer_ct_threat_bomb_planted(self):
        self.state.bomb_planted = True
        answer = RagTerroristHelper.answer("where are the counter terrorists?", self.state)
        self.assertIn("converging on bomb site", answer.lower())
        
    def test_answer_ct_threat_unknown(self):
        answer = RagTerroristHelper.answer("enemy close?", self.state)
        self.assertIn("presence unknown", answer.lower())
        
    def test_answer_strategy_no_bomb(self):
        answer = RagTerroristHelper.answer("what should we do?", self.state)
        self.assertIn("smoke", answer.lower())
        
    def test_answer_strategy_after_plant(self):
        self.state.bomb_planted = True
        answer = RagTerroristHelper.answer("suggest strategy", self.state)
        self.assertIn("crossfire", answer.lower())
        
    def test_answer_upgrade_question(self):
        answer = RagTerroristHelper.answer("any tips?", self.state)
        self.assertTrue(len(answer) > 0)
        
    def test_answer_default_fallback(self):
        answer = RagTerroristHelper.answer("random unrelated question", self.state)
        self.assertIn("Facts:", answer)
        
    def test_answer_multiple_keywords(self):
        answer = RagTerroristHelper.answer("bomb site where plant", self.state)
        self.assertIn("not planted", answer.lower())
        
    def test_answer_case_insensitive(self):
        answer1 = RagTerroristHelper.answer("WHERE IS BOMB?", self.state)
        answer2 = RagTerroristHelper.answer("where is bomb?", self.state)
        self.assertEqual(answer1.lower(), answer2.lower())


if __name__ == "__main__":
    unittest.main()

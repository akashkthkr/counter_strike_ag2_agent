import unittest
import tempfile
import shutil
import os
from counter_strike_ag2_agent.rag import RagTerroristHelper
from counter_strike_ag2_agent.rag_vector import ChromaRAG
from counter_strike_ag2_agent.game_state import GameState


class TestRAGIntegration(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.vector_rag = ChromaRAG(persist_dir=self.temp_dir, collection="test_cs")
        self.game_state = GameState()
        
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_combined_rag_workflow(self):
        cs_knowledge = [
            "Always check corners before entering a site",
            "Smoke grenades block vision for 15 seconds",
            "The bomb takes 40 seconds to detonate",
            "Flashbangs blind enemies for 2-3 seconds",
            "A-site has two entry points: long and short",
            "B-site is more enclosed with fewer angles"
        ]
        self.vector_rag.add_texts(cs_knowledge)
        
        answer = self.vector_rag.ask("How long does smoke last?")
        self.assertIsNotNone(answer)
        self.assertIn("15 seconds", answer)
        
        state_answer = RagTerroristHelper.answer("what should we do?", self.game_state)
        self.assertIsNotNone(state_answer)
        
    def test_rag_with_game_state_changes(self):
        self.vector_rag.add_texts([
            "When bomb is planted, defend from multiple angles",
            "Without bomb planted, coordinate team pushes"
        ])
        
        no_bomb_answer = RagTerroristHelper.answer("strategy?", self.game_state)
        self.assertIn("plant", no_bomb_answer.lower())
        
        self.game_state.bomb_planted = True
        self.game_state.bomb_site = "A-site"
        
        bomb_answer = RagTerroristHelper.answer("strategy?", self.game_state)
        self.assertIn("crossfire", bomb_answer.lower())
        
    def test_vector_rag_with_file_and_query(self):
        strategy_file = os.path.join(self.temp_dir, "strategies.txt")
        with open(strategy_file, "w") as f:
            f.write("""Rush Strategy - Execute fast with smokes and flashes

                    Default Strategy - Play slow and gather information

                    Eco Round - Save money and play passive""")
        
        count = self.vector_rag.add_file(strategy_file)
        self.assertEqual(count, 3)
        
        rush_answer = self.vector_rag.ask("How to rush?")
        self.assertIsNotNone(rush_answer)
        
    def test_rag_helper_with_critical_game_states(self):
        self.game_state.player_health["Counter-Terrorists"]["player"] = 0
        self.game_state.player_health["Counter-Terrorists"]["bot"] = 0
        
        no_ct_answer = RagTerroristHelper.answer("any threats?", self.game_state)
        self.assertIn("No CTs alive", no_ct_answer)
        
        self.game_state.reset_round()
        self.game_state.bomb_planted = True
        self.game_state.bomb_site = "B-site"
        
        planted_answer = RagTerroristHelper.answer("where bomb?", self.game_state)
        self.assertIn("B-site", planted_answer)
        
    def test_multiple_knowledge_sources(self):
        game_rules = ["Economy: Win round = $3250, Lose = $1400"]
        tactics = ["Crossfire setup requires 2+ players"]
        callouts = ["Mid to B through window and connector"]
        
        self.vector_rag.add_texts(game_rules)
        self.vector_rag.add_texts(tactics)
        self.vector_rag.add_texts(callouts)
        
        eco_answer = self.vector_rag.ask("How much money for winning?")
        self.assertIsNotNone(eco_answer)
        
        tactic_answer = self.vector_rag.ask("What is crossfire?")
        self.assertIsNotNone(tactic_answer)
        
    def test_rag_helper_all_question_types(self):
        test_cases = [
            ("bomb site?", "bomb"),
            ("ct near?", "ct"),
            ("what should we do?", "strategy"),
            ("unrelated question", "Facts")
        ]
        
        for question, expected_type in test_cases:
            answer = RagTerroristHelper.answer(question, self.game_state)
            self.assertIsNotNone(answer)
            self.assertTrue(len(answer) > 0)
            
    def test_vector_rag_persistence(self):
        self.vector_rag.add_texts(["Persistent data test"])
        
        new_rag = ChromaRAG(persist_dir=self.temp_dir, collection="test_cs")
        answer = new_rag.ask("persistent data")
        self.assertIsNotNone(answer)
        self.assertIn("Persistent data test", answer)
        
    def test_edge_cases_combined(self):
        empty_answer = self.vector_rag.ask("")
        self.assertIsNone(empty_answer)
        
        self.game_state.player_health["Terrorists"]["player"] = 0
        self.game_state.player_health["Terrorists"]["bot"] = 0
        facts = RagTerroristHelper.build_facts(self.game_state)
        self.assertIn("T dead: player, bot", facts)
        self.assertTrue(not any(f.startswith("T alive:") for f in facts))
        
        nonexistent_file = self.vector_rag.add_file("/does/not/exist.txt")
        self.assertEqual(nonexistent_file, 0)
        
    def test_performance_with_many_documents(self):
        for i in range(100):
            self.vector_rag.add_texts([f"Document {i}: Strategy number {i}"])
        
        answer = self.vector_rag.ask("Strategy number 42")
        self.assertIsNotNone(answer)
        
    def test_rag_helper_state_transitions(self):
        initial_answer = RagTerroristHelper.answer("status?", self.game_state)
        self.assertIn("not planted", initial_answer.lower())
        
        self.game_state.apply_action("Terrorists", "player", "plant bomb")
        
        if self.game_state.bomb_planted:
            planted_answer = RagTerroristHelper.answer("status?", self.game_state)
            self.assertIn("planted", planted_answer.lower())
            
        self.game_state.apply_action("Counter-Terrorists", "player", "defuse bomb")
        
        if not self.game_state.bomb_planted:
            defused_answer = RagTerroristHelper.answer("status?", self.game_state)
            self.assertIn("not planted", defused_answer.lower())


if __name__ == "__main__":
    unittest.main()

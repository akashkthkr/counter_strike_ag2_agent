import unittest
import tempfile
import shutil
import os
from unittest.mock import Mock, patch, MagicMock
from counter_strike_ag2_agent.rag_vector import ChromaRAG


class TestChromaRAG(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.rag = ChromaRAG(persist_dir=self.temp_dir, collection="test_collection")
        
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        self.assertIsNotNone(self.rag.client)
        self.assertIsNotNone(self.rag.col)
        
    def test_add_single_text(self):
        count = self.rag.add_texts(["This is a test document"])
        self.assertEqual(count, 1)
        
    def test_add_multiple_texts(self):
        texts = ["First document", "Second document", "Third document"]
        count = self.rag.add_texts(texts)
        self.assertEqual(count, 3)
        
    def test_add_empty_texts_list(self):
        # ChromaDB doesn't allow empty lists, so we expect 0 return
        # but need to handle the empty case in the method
        count = self.rag.add_texts([])
        self.assertEqual(count, 0)
        
    def test_add_file_success(self):
        test_file = os.path.join(self.temp_dir, "test.txt")
        content = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
        with open(test_file, "w") as f:
            f.write(content)
        count = self.rag.add_file(test_file)
        self.assertEqual(count, 3)
        
    def test_add_file_single_paragraph(self):
        test_file = os.path.join(self.temp_dir, "single.txt")
        with open(test_file, "w") as f:
            f.write("Single paragraph without breaks")
        count = self.rag.add_file(test_file)
        self.assertEqual(count, 1)
        
    def test_add_file_empty(self):
        test_file = os.path.join(self.temp_dir, "empty.txt")
        with open(test_file, "w") as f:
            f.write("")
        count = self.rag.add_file(test_file)
        self.assertEqual(count, 0)
        
    def test_add_file_whitespace_only(self):
        test_file = os.path.join(self.temp_dir, "whitespace.txt")
        with open(test_file, "w") as f:
            f.write("\n\n\n   \n\n")
        count = self.rag.add_file(test_file)
        self.assertEqual(count, 0)
        
    def test_add_file_nonexistent(self):
        count = self.rag.add_file("/nonexistent/file.txt")
        self.assertEqual(count, 0)
        
    def test_ask_with_content(self):
        self.rag.add_texts(["The bomb site is at location A"])
        answer = self.rag.ask("Where is the bomb site?")
        self.assertIsNotNone(answer)
        
    def test_ask_empty_question(self):
        answer = self.rag.ask("")
        self.assertIsNone(answer)
        
    def test_ask_whitespace_question(self):
        answer = self.rag.ask("   ")
        self.assertIsNone(answer)
        
    def test_ask_no_documents(self):
        answer = self.rag.ask("Where is the bomb?")
        self.assertIsNone(answer)
        
    @patch('counter_strike_ag2_agent.rag_vector.chromadb.PersistentClient')
    def test_embedding_function_openai_fallback(self, mock_client):
        with patch('counter_strike_ag2_agent.rag_vector.embedding_functions.OpenAIEmbeddingFunction', 
                   side_effect=Exception("No API key")):
            with patch('counter_strike_ag2_agent.rag_vector.embedding_functions.DefaultEmbeddingFunction') as mock_default:
                rag = ChromaRAG()
                mock_default.assert_called_once()
                
    def test_unique_document_ids(self):
        self.rag.add_texts(["Doc 1"])
        initial_count = self.rag.col.count()
        self.rag.add_texts(["Doc 2"])
        final_count = self.rag.col.count()
        self.assertEqual(final_count, initial_count + 1)
        
    def test_add_file_with_mixed_spacing(self):
        test_file = os.path.join(self.temp_dir, "mixed.txt")
        content = "Para 1\n\n\nPara 2\n\n\n\n\nPara 3"
        with open(test_file, "w") as f:
            f.write(content)
        count = self.rag.add_file(test_file)
        self.assertEqual(count, 3)
        
    def test_add_file_strips_whitespace(self):
        test_file = os.path.join(self.temp_dir, "spaces.txt")
        content = "  Para 1  \n\n  Para 2  \n\n  Para 3  "
        with open(test_file, "w") as f:
            f.write(content)
        count = self.rag.add_file(test_file)
        self.assertEqual(count, 3)
        
    def test_ask_handles_query_exception(self):
        # Mock the collection's query method to raise an exception
        with patch.object(self.rag.col, 'query', side_effect=Exception("Query failed")):
            answer = self.rag.ask("Test question")
            self.assertIsNone(answer)
        
    def test_ask_handles_malformed_results(self):
        # Mock the collection's query method to return malformed results
        with patch.object(self.rag.col, 'query', return_value={"wrong_key": []}):
            answer = self.rag.ask("Test question")
            self.assertIsNone(answer)


if __name__ == "__main__":
    unittest.main()

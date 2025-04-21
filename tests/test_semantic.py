import sys
import os
import unittest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import with mock to avoid loading the actual model during tests
with patch('sentence_transformers.SentenceTransformer'):
    import mcp_email_client.semantic as semantic
    import mcp_email_client.db as db

class TestSemanticOperations(unittest.TestCase):
    """Test semantic search operations."""
    
    def setUp(self):
        """Set up test environment."""
        # Use a test database file
        self.original_db_file = db.DB_FILE
        semantic.DB_FILE = Path("test_emails.duckdb")
        db.DB_FILE = Path("test_emails.duckdb")
        db.init_db()
        
        # Mock the embedding model
        self.model_patcher = patch('semantic.model')
        self.mock_model = self.model_patcher.start()
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove test database
        if Path("test_emails.duckdb").exists():
            os.remove("test_emails.duckdb")
        
        # Restore original DB file
        db.DB_FILE = self.original_db_file
        semantic.DB_FILE = self.original_db_file
        
        # Stop model patcher
        self.model_patcher.stop()
    
    def test_generate_embedding(self):
        """Test generating embeddings from text."""
        # Setup mock to return a fixed embedding
        mock_embedding = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
        self.mock_model.encode.return_value = mock_embedding
        
        # Call the function
        result = semantic.generate_embedding("test text")
        
        # Verify the model was called correctly
        self.mock_model.encode.assert_called_once_with("test text", show_progress_bar=False)
        
        # Verify result is bytes
        self.assertIsInstance(result, bytes)
        
        # Convert bytes back to array and verify it matches the original
        result_array = np.frombuffer(result, dtype=np.float32)
        np.testing.assert_array_equal(result_array, mock_embedding)
    
    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        # Create test vectors
        vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)  # Unit vector along x
        vec2 = np.array([0.0, 1.0, 0.0], dtype=np.float32)  # Unit vector along y
        vec3 = np.array([1.0, 1.0, 0.0], dtype=np.float32)  # 45 degrees between x and y
        
        # Test orthogonal vectors (90 degrees, cos=0)
        similarity = semantic.cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, 0.0, places=6)
        
        # Test identical vectors (0 degrees, cos=1)
        similarity = semantic.cosine_similarity(vec1, vec1)
        self.assertAlmostEqual(similarity, 1.0, places=6)
        
        # Test 45 degree angle (cos=0.7071)
        norm_vec3 = vec3 / np.linalg.norm(vec3)  # Normalize vec3
        similarity = semantic.cosine_similarity(vec1, vec3)
        self.assertAlmostEqual(similarity, 0.7071, places=4)
        
        # Test with None vectors
        self.assertEqual(semantic.cosine_similarity(None, vec1), 0.0)
        self.assertEqual(semantic.cosine_similarity(vec1, None), 0.0)
    
    def test_semantic_search(self):
        """Test semantic search functionality."""
        # Setup mock embeddings
        query_embedding = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        email1_embedding = np.array([0.9, 0.1, 0.0], dtype=np.float32)  # Very similar to query
        email2_embedding = np.array([0.2, 0.8, 0.0], dtype=np.float32)  # Less similar
        email3_embedding = np.array([0.0, 1.0, 0.0], dtype=np.float32)  # Not similar
        
        # Mock the text_to_embedding function
        with patch('semantic.text_to_embedding') as mock_text_to_embedding:
            mock_text_to_embedding.return_value = query_embedding
            
            # Mock the database connection and query
            with patch('duckdb.connect') as mock_connect:
                mock_conn = MagicMock()
                mock_connect.return_value.__enter__.return_value = mock_conn
                
                # Mock the result of the query with three emails
                mock_conn.execute.return_value.fetchall.return_value = [
                    (1, 'config1', 'Email 1', 'Body 1', 'sender1@example.com', 'recipient1@example.com', 
                     None, None, '2025-04-15 12:00:00', None, email1_embedding.tobytes()),
                    (2, 'config1', 'Email 2', 'Body 2', 'sender2@example.com', 'recipient2@example.com', 
                     None, None, '2025-04-16 12:00:00', None, email2_embedding.tobytes()),
                    (3, 'config2', 'Email 3', 'Body 3', 'sender3@example.com', 'recipient3@example.com', 
                     None, None, '2025-04-17 12:00:00', None, email3_embedding.tobytes()),
                ]
                
                # Mock the description to return column names
                mock_conn.description = [
                    ('id', None), ('config_name', None), ('subject', None), ('body', None),
                    ('sender', None), ('recipients', None), ('cc', None), ('bcc', None),
                    ('date', None), ('raw_content', None), ('embedding', None)
                ]
                
                # Call semantic_search
                results = semantic.semantic_search('test query', similarity_threshold=0.5)
                
                # Should return 2 results (emails 1 and 2) since email 3 is below threshold
                self.assertEqual(len(results), 2)
                
                # First result should be email 1 (most similar)
                self.assertEqual(results[0]['id'], 1)
                self.assertEqual(results[0]['subject'], 'Email 1')
                
                # Second result should be email 2 (less similar)
                self.assertEqual(results[1]['id'], 2)
                self.assertEqual(results[1]['subject'], 'Email 2')
                
                # Email 3 should not be in results (below threshold)
                self.assertTrue(all(r['id'] != 3 for r in results))
                
                # Verify scores are in descending order and above threshold
                self.assertTrue(results[0]['similarity_score'] > results[1]['similarity_score'])
                self.assertTrue(results[0]['similarity_score'] >= 0.5)
                self.assertTrue(results[1]['similarity_score'] >= 0.5)

if __name__ == "__main__":
    unittest.main()
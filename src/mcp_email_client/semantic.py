import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Union, Optional
import duckdb
from pathlib import Path

# Path to the database file
DB_FILE = Path("emails.duckdb")

# Initialize the sentence transformer model for creating embeddings
# Using a smaller and faster model that's still effective for semantic search
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

def generate_embedding(text: str) -> bytes:
    """Generate an embedding vector for the given text."""
    # Generate embeddings
    embedding = model.encode(text, show_progress_bar=False)
    # Convert to bytes for storage in DuckDB
    return embedding.tobytes()

def text_to_embedding(text: str) -> np.ndarray:
    """Convert text to embedding vector."""
    return model.encode(text, show_progress_bar=False)

def bytes_to_embedding(embedding_bytes: bytes) -> np.ndarray:
    """Convert bytes back to numpy array for similarity calculations."""
    if embedding_bytes is None:
        return None
    return np.frombuffer(embedding_bytes, dtype=np.float32)

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    if vec1 is None or vec2 is None:
        return 0.0
    vec1_norm = vec1 / np.linalg.norm(vec1)
    vec2_norm = vec2 / np.linalg.norm(vec2)
    return np.dot(vec1_norm, vec2_norm)

def update_email_with_embedding(email_id: int, combined_text: str) -> None:
    """Update an existing email with its embedding vector."""
    embedding = generate_embedding(combined_text)
    with duckdb.connect(str(DB_FILE)) as conn:
        conn.execute(
            "UPDATE emails SET embedding = ? WHERE id = ?",
            (embedding, email_id)
        )

def semantic_search(
    query: str, 
    config_name: Optional[str] = None, 
    similarity_threshold: float = 0.3,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search emails using semantic similarity with embeddings.
    
    Args:
        query: The search query
        config_name: Optional email configuration name for filtering
        similarity_threshold: Minimum similarity score (0-1) to include in results
        limit: Maximum number of results to return
        
    Returns:
        List of email dictionaries with similarity scores, sorted by score
    """
    # Generate embedding for the query
    query_embedding = text_to_embedding(query)
    
    # Get all emails (could be optimized for large datasets)
    with duckdb.connect(str(DB_FILE)) as conn:
        sql_query = "SELECT * FROM emails WHERE embedding IS NOT NULL"
        params = []
        
        if config_name:
            sql_query += " AND config_name = ?"
            params.append(config_name)
        
        result = conn.execute(sql_query, params).fetchall()
        columns = [desc[0] for desc in conn.description]
        
        # Convert result to list of dictionaries
        emails = [dict(zip(columns, row)) for row in result]
    
    # Calculate similarity for each email
    scored_emails = []
    for email in emails:
        # Convert stored embedding bytes back to numpy array
        email_embedding = bytes_to_embedding(email.get('embedding'))
        if email_embedding is not None:
            # Calculate similarity score
            similarity = cosine_similarity(query_embedding, email_embedding)
            #if similarity >= similarity_threshold:
            # Add similarity score to email dictionary
            if similarity >= similarity_threshold:
                email_with_score = email.copy()
                del email_with_score['body']
                del email_with_score['embedding']
                del email_with_score['raw_content']  # Remove embedding from output
                email_with_score['similarity_score'] = float(similarity)
                scored_emails.append(email_with_score)
    
    # Sort by similarity score (highest first) and limit results
    sorted_emails = sorted(scored_emails, key=lambda x: x.get('similarity_score', 0), reverse=True)
    return sorted_emails[:limit]

def generate_embeddings_for_all(batch_size: int = 100) -> Dict[str, Any]:
    """
    Generate embeddings for all emails that don't have them yet.
    Returns statistics about the process.
    """
    with duckdb.connect(str(DB_FILE)) as conn:
        # Get count of emails without embeddings
        missing_count = conn.execute(
            "SELECT COUNT(*) FROM emails WHERE embedding IS NULL"
        ).fetchone()[0]
        
        # Get emails without embeddings
        result = conn.execute(
            "SELECT id, subject, body FROM emails WHERE embedding IS NULL"
        ).fetchall()
        
        processed = 0
        
        # Process in batches
        for row in result:
            email_id, subject, body = row
            # Combine subject and body for better semantic context
            combined_text = f"{subject} {body}" if subject and body else subject or body or ""
            
            # Generate and store embedding
            if combined_text.strip():
                embedding = generate_embedding(combined_text)
                conn.execute(
                    "UPDATE emails SET embedding = ? WHERE id = ?",
                    (embedding, email_id)
                )
                processed += 1
                
                # Log progress for large datasets
                if processed % batch_size == 0:
                    print(f"Processed {processed}/{missing_count} emails")
        
        # Get total count of emails with embeddings
        total_with_embeddings = conn.execute(
            "SELECT COUNT(*) FROM emails WHERE embedding IS NOT NULL"
        ).fetchone()[0]
        
        return {
            "processed_in_this_run": processed,
            "total_with_embeddings": total_with_embeddings,
            "total_emails": processed + total_with_embeddings
        }
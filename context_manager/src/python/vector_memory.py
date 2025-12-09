"""
Vector Memory Module
Implements vector storage and retrieval using LanceDB for semantic search
"""
import lancedb
import pyarrow as pa
from typing import List, Dict, Any, Optional, Union
import numpy as np
from datetime import datetime
import json
import asyncio
from sentence_transformers import SentenceTransformer


class VectorMemory:
    def __init__(self, db_path: str = "./vector_memory.lancedb", model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize vector memory with LanceDB
        
        Args:
            db_path: Path to the LanceDB database
            model_name: Name of the sentence transformer model to use
        """
        self.db = lancedb.connect(db_path)
        self.model = SentenceTransformer(model_name)
        
        # Create table schema for storing dialog messages
        self.table_name = "dialog_memory"
        self._init_table()
    
    def _init_table(self):
        """Initialize the dialog memory table with appropriate schema"""
        try:
            # Try to open existing table
            self.table = self.db.open_table(self.table_name)
        except:
            # Create new table if it doesn't exist
            schema = pa.schema([
                pa.field("id", pa.string()),
                pa.field("text", pa.string()),
                pa.field("role", pa.string()),  # user, assistant, system
                pa.field("character_id", pa.string()),  # for character-specific memory
                pa.field("user_id", pa.string()),  # for user-specific memory
                pa.field("timestamp", pa.timestamp('us')),
                pa.field("importance_score", pa.float32()),
                pa.field("embedding", pa.list_(pa.float32(), 384)),  # 384-dim for all-MiniLM-L6-v2
                pa.field("metadata", pa.string()),  # JSON metadata
            ])
            
            # Create table with embedding index
            self.table = self.db.create_table(self.table_name, schema=schema)
            
            # Create vector index for fast semantic search
            self.table.create_index(
                metric="cosine",
                num_partitions=256,
                num_sub_vectors=96
            )
    
    def _generate_id(self) -> str:
        """Generate unique ID for memory entries"""
        import uuid
        return str(uuid.uuid4())
    
    def store_message(
        self, 
        text: str, 
        role: str = "user", 
        character_id: str = None, 
        user_id: str = None,
        importance_score: float = 0.0,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Store a message in vector memory
        
        Args:
            text: The message text
            role: Role of the message sender (user, assistant, system)
            character_id: ID of the character this message is associated with
            user_id: ID of the user this message is associated with
            importance_score: Calculated importance score for this message
            metadata: Additional metadata to store with the message
            
        Returns:
            ID of the stored message
        """
        # Generate embedding for the text
        embedding = self.model.encode([text])[0].tolist()
        
        # Create record
        record = {
            "id": self._generate_id(),
            "text": text,
            "role": role,
            "character_id": character_id or "default",
            "user_id": user_id or "default",
            "timestamp": datetime.utcnow(),
            "importance_score": float(importance_score),
            "embedding": embedding,
            "metadata": json.dumps(metadata or {})
        }
        
        # Insert into table
        self.table.add([record])
        
        return record["id"]
    
    def store_messages(self, messages: List[Dict[str, Any]]) -> List[str]:
        """
        Store multiple messages in vector memory
        
        Args:
            messages: List of message dictionaries with text, role, etc.
            
        Returns:
            List of IDs of stored messages
        """
        records = []
        texts = [msg["text"] for msg in messages]
        
        # Generate embeddings in batch for efficiency
        embeddings = self.model.encode(texts)
        
        for i, msg in enumerate(messages):
            record = {
                "id": self._generate_id(),
                "text": msg["text"],
                "role": msg.get("role", "user"),
                "character_id": msg.get("character_id", "default"),
                "user_id": msg.get("user_id", "default"),
                "timestamp": msg.get("timestamp", datetime.utcnow()),
                "importance_score": float(msg.get("importance_score", 0.0)),
                "embedding": embeddings[i].tolist(),
                "metadata": json.dumps(msg.get("metadata", {}))
            }
            records.append(record)
        
        # Insert all records at once
        self.table.add(records)
        
        return [record["id"] for record in records]
    
    def semantic_search(
        self, 
        query: str, 
        character_id: str = None, 
        user_id: str = None, 
        limit: int = 10,
        min_importance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search in vector memory
        
        Args:
            query: Query text to search for
            character_id: Filter by character ID (optional)
            user_id: Filter by user ID (optional)
            limit: Maximum number of results to return
            min_importance: Minimum importance score threshold
            
        Returns:
            List of matching messages with similarity scores
        """
        # Generate embedding for query
        query_embedding = self.model.encode([query])[0].tolist()
        
        # Build search query
        search = self.table.search(query_embedding)
        
        # Apply filters
        filter_conditions = []
        if character_id:
            filter_conditions.append(f"character_id = '{character_id}'")
        if user_id:
            filter_conditions.append(f"user_id = '{user_id}'")
        if min_importance > 0:
            filter_conditions.append(f"importance_score >= {min_importance}")
        
        if filter_conditions:
            search = search.where(" AND ".join(filter_conditions))
        
        # Execute search
        results = search.limit(limit).to_list()
        
        # Convert results to expected format
        formatted_results = []
        for result in results:
            formatted_result = {
                "id": result["id"],
                "text": result["text"],
                "role": result["role"],
                "character_id": result["character_id"],
                "user_id": result["user_id"],
                "timestamp": result["timestamp"],
                "importance_score": result["importance_score"],
                "metadata": json.loads(result["metadata"]),
                "similarity_score": result["_distance"]  # LanceDB returns distance, lower = more similar
            }
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    def hybrid_search(
        self, 
        query: str, 
        keyword_filter: str = None,
        character_id: str = None, 
        user_id: str = None, 
        limit: int = 10,
        min_importance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining semantic and keyword search
        
        Args:
            query: Query text for semantic search
            keyword_filter: Additional keyword filter for exact matches
            character_id: Filter by character ID (optional)
            user_id: Filter by user ID (optional)
            limit: Maximum number of results to return
            min_importance: Minimum importance score threshold
            
        Returns:
            List of matching messages with similarity scores
        """
        # For now, we'll implement as semantic search with additional keyword filtering
        # In a more advanced implementation, we could combine both semantic and keyword scores
        
        # First, perform semantic search
        semantic_results = self.semantic_search(
            query=query,
            character_id=character_id,
            user_id=user_id,
            limit=limit * 2,  # Get more results to allow for keyword filtering
            min_importance=min_importance
        )
        
        # If keyword filter is provided, filter results
        if keyword_filter:
            filtered_results = []
            keyword_lower = keyword_filter.lower()
            for result in semantic_results:
                if keyword_lower in result["text"].lower():
                    filtered_results.append(result)
            semantic_results = filtered_results[:limit]
        else:
            semantic_results = semantic_results[:limit]
        
        return semantic_results
    
    def get_memory_stats(self, character_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """
        Get statistics about stored memories
        
        Args:
            character_id: Filter by character ID (optional)
            user_id: Filter by user ID (optional)
            
        Returns:
            Dictionary with memory statistics
        """
        # Build filter conditions
        conditions = []
        if character_id:
            conditions.append(f"character_id = '{character_id}'")
        if user_id:
            conditions.append(f"useruser_id = '{user_id}'")
        
        condition_str = " AND ".join(conditions) if conditions else None
        
        # Get count
        count = len(self.table.to_pandas(filter=condition_str)) if condition_str else len(self.table.to_pandas())
        
        # Get average importance
        df = self.table.to_pandas(filter=condition_str) if condition_str else self.table.to_pandas()
        avg_importance = float(df["importance_score"].mean()) if not df.empty else 0.0
        
        # Get time range
        if not df.empty:
            min_time = df["timestamp"].min().isoformat()
            max_time = df["timestamp"].max().isoformat()
        else:
            min_time = max_time = None
        
        return {
            "total_memories": count,
            "average_importance": avg_importance,
            "time_range": {"min": min_time, "max": max_time},
            "character_id": character_id,
            "user_id": user_id
        }
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a specific memory by ID
        
        Args:
            memory_id: ID of the memory to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            self.table.delete(f"id = '{memory_id}'")
            return True
        except Exception as e:
            print(f"Error deleting memory {memory_id}: {e}")
            return False
    
    def delete_memories_by_character(self, character_id: str) -> int:
        """
        Delete all memories associated with a character
        
        Args:
            character_id: ID of the character whose memories to delete
            
        Returns:
            Number of deleted memories
        """
        try:
            # First, get count of memories to delete
            old_count = len(self.table.to_pandas(filter=f"character_id = '{character_id}'"))
            self.table.delete(f"character_id = '{character_id}'")
            return old_count
        except Exception as e:
            print(f"Error deleting memories for character {character_id}: {e}")
            return 0
    
    def update_importance_score(self, memory_id: str, new_score: float) -> bool:
        """
        Update the importance score of a memory
        
        Args:
            memory_id: ID of the memory to update
            new_score: New importance score
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            # LanceDB doesn't support direct updates, so we need to delete and re-add
            # Get the original record
            original_records = self.table.to_pandas(filter=f"id = '{memory_id}'")
            
            if len(original_records) == 0:
                return False
            
            original = original_records.iloc[0]
            
            # Delete the old record
            self.delete_memory(memory_id)
            
            # Re-add with updated importance score
            updated_record = {
                "id": memory_id,
                "text": original["text"],
                "role": original["role"],
                "character_id": original["character_id"],
                "user_id": original["user_id"],
                "timestamp": original["timestamp"],
                "importance_score": float(new_score),
                "embedding": original["embedding"].tolist(),
                "metadata": original["metadata"]
            }
            
            self.table.add([updated_record])
            return True
        except Exception as e:
            print(f"Error updating importance score for memory {memory_id}: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Initialize vector memory
    vm = VectorMemory()
    
    # Store some sample messages
    sample_messages = [
        {
            "text": "I really enjoy hiking in the mountains during autumn.",
            "role": "user",
            "character_id": "char1",
            "user_id": "user1",
            "importance_score": 0.8,
            "metadata": {"topic": "hobbies", "emotion": "positive"}
        },
        {
            "text": "The weather forecast shows rain for the next three days.",
            "role": "assistant", 
            "character_id": "char1",
            "user_id": "user1",
            "importance_score": 0.6,
            "metadata": {"topic": "weather", "type": "information"}
        },
        {
            "text": "I'm feeling quite frustrated with the current project timeline.",
            "role": "user",
            "character_id": "char2", 
            "user_id": "user2",
            "importance_score": 0.9,
            "metadata": {"topic": "work", "emotion": "negative"}
        }
    ]
    
    ids = vm.store_messages(sample_messages)
    print(f"Stored {len(ids)} messages with IDs: {ids}")
    
    # Perform semantic search
    results = vm.semantic_search("outdoor activities", character_id="char1", limit=5)
    print(f"Semantic search results: {len(results)} found")
    for result in results:
        print(f"  - {result['text']} (score: {result['similarity_score']:.3f})")
    
    # Get memory stats
    stats = vm.get_memory_stats(character_id="char1")
    print(f"Memory stats for character1: {stats}")
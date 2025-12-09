"""
Advanced Context Manager
Integrates semantic compression and vector memory for efficient context management
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio
import threading
from .semantic_compression import SemanticCompressor
from .vector_memory import VectorMemory


class ContextManager:
    def __init__(
        self, 
        model_name: str = "all-MiniLM-L6-v2", 
        db_path: str = "./context_memory.lancedb"
    ):
        """
        Initialize context manager with semantic compression and vector memory
        
        Args:
            model_name: Name of the sentence transformer model to use
            db_path: Path to the LanceDB database for vector memory
        """
        self.semantic_compressor = SemanticCompressor(model_name=model_name)
        self.vector_memory = VectorMemory(db_path=db_path, model_name=model_name)
        
        # Cache for frequently accessed contexts
        self.context_cache = {}
        self.cache_lock = threading.Lock()
    
    def add_message_to_memory(
        self, 
        text: str, 
        role: str = "user", 
        character_id: str = None, 
        user_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Add a message to both short-term context and long-term vector memory
        
        Args:
            text: The message text
            role: Role of the message sender (user, assistant, system)
            character_id: ID of the character this message is associated with
            user_id: ID of the user this message is associated with
            metadata: Additional metadata to store with the message
            
        Returns:
            ID of the stored message
        """
        # Calculate importance score using semantic compressor
        temp_message = {
            "text": text,
            "role": role,
            "timestamp": datetime.utcnow().isoformat()
        }
        importance_score = self.semantic_compressor.calculate_importance_scores([temp_message])[0]
        
        # Store in vector memory
        memory_id = self.vector_memory.store_message(
            text=text,
            role=role,
            character_id=character_id,
            user_id=user_id,
            importance_score=importance_score,
            metadata=metadata
        )
        
        return memory_id
    
    def add_messages_to_memory(
        self, 
        messages: List[Dict[str, Any]], 
        character_id: str = None, 
        user_id: str = None
    ) -> List[str]:
        """
        Add multiple messages to vector memory
        
        Args:
            messages: List of message dictionaries
            character_id: ID of the character these messages are associated with
            user_id: ID of the user these messages are associated with
            
        Returns:
            List of IDs of stored messages
        """
        # Calculate importance scores for all messages
        importance_scores = self.semantic_compressor.calculate_importance_scores(messages)
        
        # Add metadata to messages if needed and set importance scores
        processed_messages = []
        for i, msg in enumerate(messages):
            processed_msg = msg.copy()
            processed_msg["importance_score"] = importance_scores[i]
            processed_msg["character_id"] = character_id or processed_msg.get("character_id", "default")
            processed_msg["user_id"] = user_id or processed_msg.get("user_id", "default")
            processed_msg["timestamp"] = processed_msg.get("timestamp", datetime.utcnow().isoformat())
            processed_messages.append(processed_msg)
        
        # Store in vector memory
        return self.vector_memory.store_messages(processed_messages)
    
    def compress_context(
        self, 
        messages: List[Dict[str, Any]], 
        target_length: int = None,
        compression_ratio: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Compress context using semantic compression
        
        Args:
            messages: List of message dictionaries
            target_length: Target number of messages after compression (optional)
            compression_ratio: Ratio of messages to keep (default 0.5 = 50%)
            
        Returns:
            Compressed list of messages
        """
        return self.semantic_compressor.compress_context(
            messages, 
            target_length=target_length, 
            compression_ratio=compression_ratio
        )
    
    def adaptive_compress(
        self, 
        messages: List[Dict[str, Any]], 
        max_context_size: int = 2000,
        current_tokens: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Adaptively compress context based on current load and size constraints
        
        Args:
            messages: List of message dictionaries
            max_context_size: Maximum allowed context size in tokens/characters
            current_tokens: Current token count
            
        Returns:
            Adaptively compressed list of messages
        """
        return self.semantic_compressor.adaptive_compress(
            messages, 
            max_context_size=max_context_size, 
            current_tokens=current_tokens
        )
    
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
        return self.vector_memory.semantic_search(
            query=query,
            character_id=character_id,
            user_id=user_id,
            limit=limit,
            min_importance=min_importance
        )
    
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
        return self.vector_memory.hybrid_search(
            query=query,
            keyword_filter=keyword_filter,
            character_id=character_id,
            user_id=user_id,
            limit=limit,
            min_importance=min_importance
        )
    
    def get_relevant_context(
        self, 
        current_query: str, 
        character_id: str = None, 
        user_id: str = None,
        max_context_messages: int = 10,
        include_current_context: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get contextually relevant messages from memory to augment current context
        
        Args:
            current_query: Current user query to find relevant context for
            character_id: Filter by character ID (optional)
            user_id: Filter by user ID (optional)
            max_context_messages: Maximum number of context messages to retrieve
            include_current_context: Current context to consider for relevance
            
        Returns:
            List of relevant messages from memory
        """
        # First, search in vector memory for relevant information
        relevant_memories = self.semantic_search(
            query=current_query,
            character_id=character_id,
            user_id=user_id,
            limit=max_context_messages,
            min_importance=0.3  # Only get moderately important memories
        )
        
        # Convert to message format
        relevant_messages = []
        for memory in relevant_memories:
            relevant_messages.append({
                "text": memory["text"],
                "role": memory["role"],
                "timestamp": memory["timestamp"],
                "importance_score": memory["importance_score"],
                "source": "memory"
            })
        
        return relevant_messages
    
    def cluster_messages(
        self, 
        messages: List[Dict[str, Any]], 
        threshold: float = 0.7,
        max_clusters: int = None
    ) -> List[List[Dict[str, Any]]]:
        """
        Cluster semantically similar messages together
        
        Args:
            messages: List of message dictionaries
            threshold: Similarity threshold for clustering
            max_clusters: Maximum number of clusters (None for automatic)
            
        Returns:
            List of clusters, each containing a list of messages
        """
        return self.semantic_compressor.cluster_messages(
            messages, 
            threshold=threshold, 
            max_clusters=max_clusters
        )
    
    def get_memory_stats(self, character_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """
        Get statistics about stored memories
        
        Args:
            character_id: Filter by character ID (optional)
            user_id: Filter by user ID (optional)
            
        Returns:
            Dictionary with memory statistics
        """
        return self.vector_memory.get_memory_stats(character_id=character_id, user_id=user_id)
    
    def update_importance_score(self, memory_id: str, new_score: float) -> bool:
        """
        Update the importance score of a memory
        
        Args:
            memory_id: ID of the memory to update
            new_score: New importance score
            
        Returns:
            True if update was successful, False otherwise
        """
        return self.vector_memory.update_importance_score(memory_id, new_score)
    
    def save_context_session(self, session_id: str, messages: List[Dict[str, Any]]) -> bool:
        """
        Save a context session to persistent storage
        
        Args:
            session_id: Unique identifier for the session
            messages: List of messages in the session
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            import pickle
            import os
            
            # Create sessions directory if it doesn't exist
            sessions_dir = "./sessions"
            os.makedirs(sessions_dir, exist_ok=True)
            
            session_file = os.path.join(sessions_dir, f"{session_id}.pkl")
            
            with open(session_file, 'wb') as f:
                pickle.dump(messages, f)
            
            return True
        except Exception as e:
            print(f"Error saving context session {session_id}: {e}")
            return False
    
    def load_context_session(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Load a context session from persistent storage
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            List of messages in the session, or None if not found
        """
        try:
            import pickle
            import os
            
            session_file = os.path.join("./sessions", f"{session_id}.pkl")
            
            if not os.path.exists(session_file):
                return None
            
            with open(session_file, 'rb') as f:
                messages = pickle.load(f)
            
            return messages
        except Exception as e:
            print(f"Error loading context session {session_id}: {e}")
            return None


# Example usage
if __name__ == "__main__":
    # Initialize context manager
    cm = ContextManager()
    
    # Sample conversation
    conversation = [
        {"text": "Hello, how are you today?", "role": "user"},
        {"text": "I'm doing well, thank you for asking!", "role": "assistant"},
        {"text": "Let's discuss the weather forecast for tomorrow.", "role": "user"},
        {"text": "Tomorrow will be sunny with a high of 25°C.", "role": "assistant"},
        {"text": "That sounds great! I love sunny days.", "role": "user"},
        {"text": "Yes, sunny weather is perfect for outdoor activities.", "role": "assistant"},
        {"text": "I enjoy hiking in the mountains during autumn.", "role": "user"},
        {"text": "That sounds like a wonderful hobby! The fall colors must be beautiful.", "role": "assistant"}
    ]
    
    # Add messages to memory
    message_ids = cm.add_messages_to_memory(conversation, character_id="char1", user_id="user1")
    print(f"Added {len(message_ids)} messages to memory")
    
    # Compress context
    compressed = cm.compress_context(conversation, compression_ratio=0.5)
    print(f"Original: {len(conversation)} messages, Compressed: {len(compressed)} messages")
    
    # Search for relevant context
    relevant = cm.get_relevant_context("outdoor activities", character_id="char1", max_context_messages=5)
    print(f"Found {len(relevant)} relevant messages from memory")
    
    # Get memory stats
    stats = cm.get_memory_stats(character_id="char1")
    print(f"Memory stats: {stats}")
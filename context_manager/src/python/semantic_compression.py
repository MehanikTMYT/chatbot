"""
Semantic Compression Module
Implements context compression using semantic clustering and importance evaluation
"""
import numpy as np
from typing import List, Dict, Tuple, Any
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os
from datetime import datetime


class SemanticCompressor:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_dir: str = "./cache"):
        """
        Initialize semantic compressor with sentence transformer model
        
        Args:
            model_name: Name of the sentence transformer model to use
            cache_dir: Directory to cache embeddings
        """
        self.model = SentenceTransformer(model_name)
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Cache for embeddings to avoid recomputation
        self.embedding_cache_file = os.path.join(cache_dir, "embeddings_cache.pkl")
        self.embedding_cache = self._load_embedding_cache()
    
    def _load_embedding_cache(self) -> Dict[str, np.ndarray]:
        """Load embedding cache from disk"""
        if os.path.exists(self.embedding_cache_file):
            try:
                with open(self.embedding_cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_embedding_cache(self):
        """Save embedding cache to disk"""
        try:
            with open(self.embedding_cache_file, 'wb') as f:
                pickle.dump(self.embedding_cache, f)
        except Exception as e:
            print(f"Error saving embedding cache: {e}")
    
    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Get embeddings for a list of texts, using cache when possible
        
        Args:
            texts: List of text strings to encode
            
        Returns:
            Array of embeddings
        """
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        # Check cache for existing embeddings
        for i, text in enumerate(texts):
            text_hash = hash(text)
            if text_hash in self.embedding_cache:
                embeddings.append(self.embedding_cache[text_hash])
            else:
                embeddings.append(None)  # Placeholder
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Generate embeddings for uncached texts
        if uncached_texts:
            new_embeddings = self.model.encode(uncached_texts)
            for idx, emb in zip(uncached_indices, new_embeddings):
                text_hash = hash(texts[idx])
                self.embedding_cache[text_hash] = emb
                embeddings[idx] = emb
        
        # Save cache periodically
        if len(uncached_texts) > 0:
            self._save_embedding_cache()
        
        return np.array(embeddings)
    
    def calculate_importance_scores(
        self, 
        messages: List[Dict[str, Any]]
    ) -> List[float]:
        """
        Calculate importance scores for messages based on multiple factors
        
        Args:
            messages: List of message dictionaries with 'text', 'role', 'timestamp', etc.
            
        Returns:
            List of importance scores for each message
        """
        scores = []
        for msg in messages:
            score = 0.0
            
            # Factor 1: Emotional intensity (keywords indicating emotion)
            emotional_keywords = [
                'excited', 'happy', 'sad', 'angry', 'frustrated', 'grateful',
                'surprised', 'shocked', 'disappointed', 'thrilled', 'worried',
                'concerned', 'amazed', 'disgusted', 'furious', 'delighted'
            ]
            text_lower = msg.get('text', '').lower()
            emotional_score = sum(1 for word in emotional_keywords if word in text_lower)
            
            # Factor 2: Factual content (numbers, dates, names)
            factual_score = 0
            words = text_lower.split()
            for word in words:
                if any(c.isdigit() for c in word):  # Contains numbers
                    factual_score += 0.5
                elif len(word) > 4 and word.istitle():  # Likely proper noun
                    factual_score += 0.3
            
            # Factor 3: Message length (longer messages might contain more info)
            length_score = min(len(msg.get('text', '')) / 100.0, 1.0)  # Cap at 1.0
            
            # Factor 4: Recency (more recent messages might be more relevant)
            timestamp = msg.get('timestamp')
            recency_score = 0.0
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        msg_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        msg_time = timestamp
                    time_diff = (datetime.now(msg_time.tzinfo) - msg_time).total_seconds()
                    # More recent = higher score (inverse relationship with time difference)
                    recency_score = max(0, 1 - time_diff / (24 * 3600))  # Normalize over 24 hours
                except:
                    recency_score = 0.5  # Default if parsing fails
            
            # Factor 5: Role importance (system/user messages often more important than bot)
            role_score = 0.5
            if msg.get('role') == 'system':
                role_score = 1.0
            elif msg.get('role') == 'user':
                role_score = 0.8
            elif msg.get('role') == 'assistant':
                role_score = 0.6
            
            # Combine all factors with weights
            score = (
                0.2 * emotional_score +
                0.2 * factual_score +
                0.15 * length_score +
                0.15 * recency_score +
                0.3 * role_score
            )
            
            scores.append(score)
        
        # Normalize scores to 0-1 range
        max_score = max(scores) if scores else 1.0
        if max_score > 0:
            scores = [s / max_score for s in scores]
        
        return scores
    
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
        if not messages:
            return []
        
        # Extract texts for embedding
        texts = [msg.get('text', '') for msg in messages]
        
        # Get embeddings
        embeddings = self.get_embeddings(texts)
        
        # Perform clustering
        if max_clusters is None:
            # Determine optimal number of clusters based on similarity threshold
            distances = 1 - cosine_similarity(embeddings)
            clustering = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=1-threshold,
                linkage='average',
                metric='cosine',
                connectivity=distances
            )
        else:
            clustering = AgglomerativeClustering(
                n_clusters=max_clusters,
                linkage='average',
                metric='cosine'
            )
        
        labels = clustering.fit_predict(embeddings)
        
        # Group messages by cluster
        clusters = [[] for _ in range(max(labels) + 1)]
        for msg, label in zip(messages, labels):
            clusters[label].append(msg)
        
        # Filter out empty clusters
        clusters = [cluster for cluster in clusters if cluster]
        
        return clusters
    
    def compress_context(
        self, 
        messages: List[Dict[str, Any]], 
        target_length: int = None,
        compression_ratio: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Compress context by clustering and selecting important messages
        
        Args:
            messages: List of message dictionaries
            target_length: Target number of messages after compression (optional)
            compression_ratio: Ratio of messages to keep (default 0.5 = 50%)
            
        Returns:
            Compressed list of messages
        """
        if not messages:
            return []
        
        if target_length is None:
            target_length = max(1, int(len(messages) * compression_ratio))
        
        if len(messages) <= target_length:
            return messages  # No compression needed
        
        # Calculate importance scores
        importance_scores = self.calculate_importance_scores(messages)
        
        # Create pairs of (message, importance_score, original_index)
        indexed_messages = [
            (msg, score, idx) 
            for idx, (msg, score) in enumerate(zip(messages, importance_scores))
        ]
        
        # Sort by importance score (descending)
        indexed_messages.sort(key=lambda x: x[1], reverse=True)
        
        # Select top N messages based on importance
        selected_messages = indexed_messages[:target_length]
        
        # Restore original order based on index
        selected_messages.sort(key=lambda x: x[2])
        
        # Return just the messages
        compressed_messages = [msg for msg, _, _ in selected_messages]
        
        return compressed_messages
    
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
        # Estimate current context size (approximate characters)
        current_size = sum(len(msg.get('text', '')) for msg in messages)
        
        if current_size <= max_context_size:
            return messages  # No compression needed
        
        # Calculate compression ratio
        compression_ratio = max_context_size / current_size
        compression_ratio = max(0.1, min(0.9, compression_ratio))  # Keep between 10-90%
        
        return self.compress_context(messages, compression_ratio=compression_ratio)


# Example usage
if __name__ == "__main__":
    compressor = SemanticCompressor()
    
    # Sample messages
    sample_messages = [
        {"text": "Hello, how are you today?", "role": "user", "timestamp": datetime.now().isoformat()},
        {"text": "I'm doing well, thank you for asking!", "role": "assistant", "timestamp": datetime.now().isoformat()},
        {"text": "Let's discuss the weather forecast for tomorrow.", "role": "user", "timestamp": datetime.now().isoformat()},
        {"text": "Tomorrow will be sunny with a high of 25°C.", "role": "assistant", "timestamp": datetime.now().isoformat()},
        {"text": "That sounds great! I love sunny days.", "role": "user", "timestamp": datetime.now().isoformat()}
    ]
    
    # Test compression
    compressed = compressor.compress_context(sample_messages, compression_ratio=0.6)
    print(f"Original: {len(sample_messages)} messages, Compressed: {len(compressed)} messages")
    
    # Test clustering
    clusters = compressor.cluster_messages(sample_messages, threshold=0.5)
    print(f"Number of clusters: {len(clusters)}")
    
    # Test importance scoring
    scores = compressor.calculate_importance_scores(sample_messages)
    print(f"Importance scores: {scores}")
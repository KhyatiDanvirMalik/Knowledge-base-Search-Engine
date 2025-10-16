from typing import List
import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from ..utils.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Handles text embedding generation using SentenceTransformers"""
    
    def __init__(self):
        """Initialize the embedding model"""
        try:
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Loaded embedding model {settings.EMBEDDING_MODEL} with dimension {self.embedding_dimension}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise Exception(f"Failed to initialize embedding service: {str(e)}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text to embed
            
        Returns:
            List of float values representing the embedding
        """
        try:
            if not text.strip():
                raise ValueError("Empty text provided for embedding")
            
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise Exception(f"Failed to generate embedding: {str(e)}")
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings (each embedding is a list of floats)
        """
        try:
            if not texts:
                return []
            
            # Filter out empty texts
            valid_texts = [text for text in texts if text.strip()]
            if not valid_texts:
                raise ValueError("No valid texts provided for embedding")
            
            embeddings = self.model.encode(valid_texts, convert_to_numpy=True, show_progress_bar=True)
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            raise Exception(f"Failed to generate batch embeddings: {str(e)}")
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Compute cosine similarity
            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error computing similarity: {str(e)}")
            raise Exception(f"Failed to compute similarity: {str(e)}")
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by the model
        
        Returns:
            Embedding dimension
        """
        return self.embedding_dimension
from typing import List, Dict, Optional
import logging
import chromadb
from chromadb.utils import embedding_functions
import uuid
from ..utils.config import settings

logger = logging.getLogger(__name__)

class VectorStore:
    """Handles vector storage and retrieval using ChromaDB"""
    
    def __init__(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
            
            # Create or get collection
            self.collection_name = "documents"
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=settings.EMBEDDING_MODEL
                )
            )
            
            logger.info(f"Initialized vector store with collection '{self.collection_name}'")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}")
            raise Exception(f"Failed to initialize vector store: {str(e)}")
    
    def add_documents(self, chunks: List[Dict], document_id: str) -> bool:
        """
        Add document chunks to the vector store
        
        Args:
            chunks: List of document chunks with text and metadata
            document_id: Unique identifier for the document
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not chunks:
                logger.warning("No chunks provided for indexing")
                return False
            
            # Prepare data for ChromaDB
            ids = []
            texts = []
            metadatas = []
            
            for chunk in chunks:
                chunk_id = f"{document_id}_{chunk['chunk_index']}"
                ids.append(chunk_id)
                texts.append(chunk['text'])
                
                metadata = {
                    'document_id': document_id,
                    'chunk_index': chunk['chunk_index'],
                    'word_count': chunk['word_count'],
                    'chunk_id': chunk['id']
                }
                metadatas.append(metadata)
            
            # Add to ChromaDB
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(chunks)} chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            return False
    
    def search_similar(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search for similar documents using vector similarity
        
        Args:
            query: Search query text
            max_results: Maximum number of results to return
            
        Returns:
            List of similar documents with metadata and scores
        """
        try:
            if not query.strip():
                logger.warning("Empty query provided for search")
                return []
            
            # Query the collection
            results = self.collection.query(
                query_texts=[query],
                n_results=max_results
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    result = {
                        'text': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'][0] else {},
                        'distance': results['distances'][0][i] if results['distances'][0] else 0.0,
                        'id': results['ids'][0][i] if results['ids'][0] else ""
                    }
                    formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} similar documents for query")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete all chunks of a document from the vector store
        
        Args:
            document_id: Unique identifier for the document
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all chunks for the document
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            if results['ids']:
                # Delete the chunks
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
                return True
            else:
                logger.warning(f"No chunks found for document {document_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting document from vector store: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict:
        """
        Get statistics about the vector store collection
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            return {
                'total_chunks': count,
                'collection_name': self.collection_name
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {'total_chunks': 0, 'collection_name': self.collection_name}
    
    def list_documents(self) -> List[str]:
        """
        List all unique document IDs in the vector store
        
        Returns:
            List of document IDs
        """
        try:
            # Get all metadata
            results = self.collection.get()
            
            if results['metadatas']:
                document_ids = list(set(
                    metadata.get('document_id') 
                    for metadata in results['metadatas'] 
                    if metadata.get('document_id')
                ))
                return document_ids
            
            return []
            
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return []
from fastapi import APIRouter, HTTPException
from typing import List
import logging
import time

from ..models.schemas import QueryRequest, QueryResponse
from ..services.vector_store import VectorStore
from ..services.llm_service import LLMService
from ..utils.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Global instances (in production, use dependency injection)
vector_store = VectorStore()
llm_service = LLMService()

# In-memory storage for query history (use database in production)
query_history = []

@router.post("/", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Query the knowledge base and get an answer using RAG
    """
    start_time = time.time()
    
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Search for similar documents
        max_results = min(request.max_results or settings.MAX_RESULTS, 10)
        similar_docs = vector_store.search_similar(request.question, max_results)
        
        if not similar_docs:
            # No relevant documents found
            answer = "I couldn't find any relevant information in the uploaded documents to answer your question. Please make sure you have uploaded relevant documents or try rephrasing your question."
            sources = []
        else:
            # Generate answer using LLM
            answer = llm_service.generate_answer(request.question, similar_docs)
            
            # Format sources
            sources = []
            for doc in similar_docs:
                source = {
                    'text': doc['text'][:200] + "..." if len(doc['text']) > 200 else doc['text'],
                    'document_id': doc['metadata'].get('document_id', 'unknown'),
                    'chunk_index': doc['metadata'].get('chunk_index', 0),
                    'similarity_score': 1 - doc['distance']  # Convert distance to similarity
                }
                sources.append(source)
        
        processing_time = time.time() - start_time
        
        # Create response
        response = QueryResponse(
            question=request.question,
            answer=answer,
            sources=sources,
            processing_time=processing_time
        )
        
        # Store in history
        query_history.append({
            'timestamp': time.time(),
            'question': request.question,
            'answer': answer,
            'sources_count': len(sources),
            'processing_time': processing_time
        })
        
        # Keep only last 100 queries in memory
        if len(query_history) > 100:
            query_history.pop(0)
        
        logger.info(f"Processed query in {processing_time:.2f}s, found {len(sources)} sources")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")

@router.get("/history")
async def get_query_history(limit: int = 10):
    """
    Get recent query history
    """
    try:
        # Return last N queries
        recent_queries = query_history[-limit:] if len(query_history) > limit else query_history
        return {
            'queries': recent_queries,
            'total_count': len(query_history)
        }
    except Exception as e:
        logger.error(f"Error getting query history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get query history")

@router.delete("/history")
async def clear_query_history():
    """
    Clear query history
    """
    try:
        global query_history
        query_history = []
        return {"message": "Query history cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing query history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear query history")

@router.post("/test")
async def test_query_system(question: str = "What is this document about?"):
    """
    Test the query system with a sample question
    """
    try:
        # Get collection stats
        stats = vector_store.get_collection_stats()
        
        if stats['total_chunks'] == 0:
            return {
                "message": "No documents found in the knowledge base. Please upload some PDF documents first.",
                "stats": stats
            }
        
        # Test search
        test_results = vector_store.search_similar(question, 3)
        
        return {
            "message": "Query system is working",
            "stats": stats,
            "test_question": question,
            "test_results_count": len(test_results),
            "sample_results": test_results[:2] if test_results else []
        }
        
    except Exception as e:
        logger.error(f"Error testing query system: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query system test failed: {str(e)}")
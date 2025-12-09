"""
Context Management API Server
Provides REST API endpoints for the context management system
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
import time
from .context_manager import ContextManager


# Initialize context manager
context_manager = ContextManager()

# Initialize FastAPI app
app = FastAPI(
    title="Context Management API",
    description="API for advanced context management with semantic compression and vector memory",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, configure this properly
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class Message(BaseModel):
    id: Optional[str] = None
    text: str = Field(..., min_length=1, max_length=10000)
    role: str = Field(..., regex="^(user|assistant|system)$")
    timestamp: Optional[str] = None
    importance_score: Optional[float] = 0.0
    character_id: Optional[str] = "default"
    user_id: Optional[str] = "default"
    metadata: Optional[Dict[str, Any]] = {}


class MessageRequest(BaseModel):
    text: str
    role: str = Field(..., regex="^(user|assistant|system)$")
    character_id: Optional[str] = "default"
    user_id: Optional[str] = "default"
    metadata: Optional[Dict[str, Any]] = {}


class MessagesRequest(BaseModel):
    messages: List[MessageRequest]
    character_id: Optional[str] = "default"
    user_id: Optional[str] = "default"


class CompressRequest(BaseModel):
    messages: List[Message]
    target_length: Optional[int] = None
    compression_ratio: float = 0.5


class CompressResponse(BaseModel):
    original_length: int
    compressed_length: int
    compressed_messages: List[Message]
    execution_time: float


class SearchRequest(BaseModel):
    query: str
    character_id: Optional[str] = None
    user_id: Optional[str] = None
    limit: int = 10
    min_importance: float = 0.0
    keyword_filter: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    results: List[Message]
    execution_time: float


class SessionRequest(BaseModel):
    messages: List[Message]


class UpdateImportanceRequest(BaseModel):
    importance_score: float = Field(..., ge=0.0, le=1.0)


class MemoryStatsResponse(BaseModel):
    total_memories: int
    average_importance: float
    time_range: Dict[str, Optional[str]]
    character_id: Optional[str]
    user_id: Optional[str]


# API endpoints
@app.post("/api/context/message", response_model=str)
async def add_message(request: MessageRequest):
    """Add a single message to the context memory"""
    try:
        message_id = context_manager.add_message_to_memory(
            text=request.text,
            role=request.role,
            character_id=request.character_id,
            user_id=request.user_id,
            metadata=request.metadata
        )
        return message_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/context/messages", response_model=List[str])
async def add_messages(request: MessagesRequest):
    """Add multiple messages to the context memory"""
    try:
        # Convert MessageRequest objects to dictionaries
        messages = []
        for msg_req in request.messages:
            messages.append({
                "text": msg_req.text,
                "role": msg_req.role,
                "timestamp": time.time()
            })
        
        message_ids = context_manager.add_messages_to_memory(
            messages=messages,
            character_id=request.character_id,
            user_id=request.user_id
        )
        return message_ids
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/context/compress", response_model=CompressResponse)
async def compress_context(request: CompressRequest):
    """Compress the context using semantic compression"""
    start_time = time.time()
    
    try:
        # Convert Pydantic models to dictionaries for processing
        message_dicts = []
        for msg in request.messages:
            msg_dict = msg.dict()
            if msg_dict["id"] is None:
                msg_dict["id"] = str(uuid.uuid4())
            message_dicts.append(msg_dict)
        
        compressed_messages = context_manager.compress_context(
            messages=message_dicts,
            target_length=request.target_length,
            compression_ratio=request.compression_ratio
        )
        
        execution_time = time.time() - start_time
        
        # Convert back to Message objects
        compressed_message_objects = [Message(**msg) for msg in compressed_messages]
        
        return CompressResponse(
            original_length=len(request.messages),
            compressed_length=len(compressed_message_objects),
            compressed_messages=compressed_message_objects,
            execution_time=execution_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/context/search", response_model=SearchResponse)
async def semantic_search(
    query: str = Query(..., min_length=1, max_length=1000),
    character_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    min_importance: float = Query(0.0, ge=0.0, le=1.0),
    keyword_filter: Optional[str] = Query(None)
):
    """Perform semantic search in the context memory"""
    start_time = time.time()
    
    try:
        if keyword_filter:
            results = context_manager.hybrid_search(
                query=query,
                keyword_filter=keyword_filter,
                character_id=character_id,
                user_id=user_id,
                limit=limit,
                min_importance=min_importance
            )
        else:
            results = context_manager.semantic_search(
                query=query,
                character_id=character_id,
                user_id=user_id,
                limit=limit,
                min_importance=min_importance
            )
        
        execution_time = time.time() - start_time
        
        # Convert results to Message objects
        message_results = []
        for result in results:
            msg = Message(
                id=result["id"],
                text=result["text"],
                role=result["role"],
                timestamp=result["timestamp"].isoformat() if hasattr(result["timestamp"], 'isoformat') else str(result["timestamp"]),
                importance_score=result["importance_score"],
                character_id=result.get("character_id", "default"),
                user_id=result.get("user_id", "default"),
                metadata=result.get("metadata", {}),
                source=result.get("source", "memory")
            )
            message_results.append(msg)
        
        return SearchResponse(
            query=query,
            results=message_results,
            execution_time=execution_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/context/hybrid-search", response_model=SearchResponse)
async def hybrid_search(
    query: str = Query(..., min_length=1, max_length=1000),
    keyword_filter: Optional[str] = Query(None),
    character_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    min_importance: float = Query(0.0, ge=0.0, le=1.0)
):
    """Perform hybrid search (semantic + keyword) in the context memory"""
    start_time = time.time()
    
    try:
        results = context_manager.hybrid_search(
            query=query,
            keyword_filter=keyword_filter,
            character_id=character_id,
            user_id=user_id,
            limit=limit,
            min_importance=min_importance
        )
        
        execution_time = time.time() - start_time
        
        # Convert results to Message objects
        message_results = []
        for result in results:
            msg = Message(
                id=result["id"],
                text=result["text"],
                role=result["role"],
                timestamp=result["timestamp"].isoformat() if hasattr(result["timestamp"], 'isoformat') else str(result["timestamp"]),
                importance_score=result["importance_score"],
                character_id=result.get("character_id", "default"),
                user_id=result.get("user_id", "default"),
                metadata=result.get("metadata", {}),
                source=result.get("source", "memory")
            )
            message_results.append(msg)
        
        return SearchResponse(
            query=query,
            results=message_results,
            execution_time=execution_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/context/stats", response_model=MemoryStatsResponse)
async def get_memory_stats(
    character_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None)
):
    """Get statistics about the context memory"""
    try:
        stats = context_manager.get_memory_stats(
            character_id=character_id,
            user_id=user_id
        )
        
        return MemoryStatsResponse(
            total_memories=stats["total_memories"],
            average_importance=stats["average_importance"],
            time_range=stats["time_range"],
            character_id=stats["character_id"],
            user_id=stats["user_id"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/context/session/{session_id}")
async def save_session(session_id: str, request: SessionRequest):
    """Save a context session"""
    try:
        success = context_manager.save_context_session(session_id, [msg.dict() for msg in request.messages])
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save session")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/context/session/{session_id}")
async def load_session(session_id: str):
    """Load a context session"""
    try:
        messages = context_manager.load_context_session(session_id)
        if messages is None:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Convert to Message objects
        message_objects = [Message(**msg) for msg in messages]
        
        return {
            "id": session_id,
            "messages": message_objects,
            "createdAt": time.time(),
            "updatedAt": time.time()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/context/memory/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a specific memory entry"""
    try:
        success = context_manager.vector_memory.delete_memory(memory_id)
        if not success:
            raise HTTPException(status_code=404, detail="Memory not found")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/context/memory/{memory_id}/importance")
async def update_importance_score(memory_id: str, request: UpdateImportanceRequest):
    """Update the importance score of a memory"""
    try:
        success = context_manager.update_importance_score(memory_id, request.importance_score)
        if not success:
            raise HTTPException(status_code=404, detail="Memory not found")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "context-manager",
        "timestamp": time.time()
    }


# Run the server if this file is executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
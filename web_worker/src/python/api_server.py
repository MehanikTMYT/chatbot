"""
API Server for the Secure Web Worker
Provides REST endpoints for search and content fetching
"""

import asyncio
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
import uvicorn
from datetime import datetime

try:
    from .web_worker import web_worker, SearchResult
except ImportError:
    # Handle when run from the same directory
    from web_worker import web_worker, SearchResult

app = FastAPI(
    title="Secure Web Worker API",
    description="API for secure internet access with content filtering",
    version="1.0.0"
)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    character_id: str = "default"


class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    character_id: str
    timestamp: datetime


class FetchRequest(BaseModel):
    url: str = Field(..., description="URL to fetch content from")
    character_id: str = "default"


class FetchResponse(BaseModel):
    content: Optional[str]
    url: str
    character_id: str
    timestamp: datetime


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    config: Dict
    stats: Dict


class CharacterPermissionRequest(BaseModel):
    character_id: str
    allow_internet_access: bool = True
    max_request_per_hour: int = 100
    allowed_domains_only: List[str] = []
    blocked_domains: List[str] = []


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return web_worker.get_health_status()


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Perform a secure search"""
    try:
        results = await web_worker.search(request.query, request.character_id)
        return SearchResponse(
            results=results,
            query=request.query,
            character_id=request.character_id,
            timestamp=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/fetch", response_model=FetchResponse)
async def fetch_content(request: FetchRequest):
    """Fetch content from a URL"""
    try:
        content = await web_worker.fetch_content(request.url, request.character_id)
        return FetchResponse(
            content=content,
            url=request.url,
            character_id=request.character_id,
            timestamp=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fetch failed: {str(e)}")


@app.get("/search/history")
async def get_search_history():
    """Get search history for monitoring"""
    return {"history": web_worker.search_history}


@app.post("/permissions")
async def set_character_permission(request: CharacterPermissionRequest):
    """Set permissions for a character"""
    try:
        perm_manager = web_worker.permission_manager
        with perm_manager._lock:
            perm_manager.permissions[request.character_id] = perm_manager.permissions.get(
                request.character_id,
                type('CharacterPermission', (), {})  # Create a basic object
            )
            # Update the permission object
            perm = perm_manager.get_permission(request.character_id)
            perm.allow_internet_access = request.allow_internet_access
            perm.max_request_per_hour = request.max_request_per_hour
            perm.allowed_domains_only = request.allowed_domains_only
            perm.blocked_domains = request.blocked_domains
            
        return {"status": "success", "character_id": request.character_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Setting permissions failed: {str(e)}")


@app.get("/permissions/{character_id}")
async def get_character_permission(character_id: str):
    """Get permissions for a character"""
    try:
        perm = web_worker.permission_manager.get_permission(character_id)
        return {
            "character_id": perm.character_id,
            "allow_internet_access": perm.allow_internet_access,
            "max_request_per_hour": perm.max_request_per_hour,
            "allowed_domains_only": perm.allowed_domains_only,
            "blocked_domains": perm.blocked_domains
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Getting permissions failed: {str(e)}")


@app.on_event('startup')
async def startup_event():
    """Initialize the web worker on startup"""
    print("Starting up Secure Web Worker API...")


@app.on_event('shutdown')
async def shutdown_event():
    """Clean up resources on shutdown"""
    print("Shutting down Secure Web Worker API...")
    await web_worker.close()


if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="info"
    )
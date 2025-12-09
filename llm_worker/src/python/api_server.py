"""
API Server for LLM Worker
Provides REST and WebSocket endpoints for interacting with the LLM
"""
import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import threading

from llm_worker import LLMWorker, GenerationConfig, Request as LLMRequest
from config.config import get_default_config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Worker API", version="1.0.0")

# Global worker instance
llm_worker: Optional[LLMWorker] = None
config = get_default_config()

class GenerateRequest(BaseModel):
    """Request model for text generation"""
    prompt: str = Field(..., description="Input prompt for generation")
    max_new_tokens: Optional[int] = Field(default=1024, description="Maximum number of tokens to generate")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: Optional[float] = Field(default=0.9, ge=0.0, le=1.0, description="Top-p sampling parameter")
    top_k: Optional[int] = Field(default=50, ge=0, le=200, description="Top-k sampling parameter")
    repetition_penalty: Optional[float] = Field(default=1.1, ge=0.0, description="Repetition penalty")
    do_sample: Optional[bool] = Field(default=True, description="Whether to use sampling")
    stream: Optional[bool] = Field(default=False, description="Whether to stream the response")
    priority: Optional[int] = Field(default=2, description="Request priority (0=system, 1=high, 2=normal, 3=low)")

class GenerateResponse(BaseModel):
    """Response model for text generation"""
    id: str
    text: str
    tokens_generated: int
    generation_time: float
    timestamp: str

@app.on_event("startup")
async def startup_event():
    """Initialize the LLM worker on startup"""
    global llm_worker
    
    logger.info("Starting LLM Worker API server...")
    
    try:
        # Initialize the LLM worker
        # In a real implementation, these would be actual TensorRT model paths
        model_path = config.model_config.tensorrt_model_path
        tokenizer_path = config.model_config.tokenizer_path
        
        logger.info(f"Initializing LLM worker with model: {model_path}")
        
        # Create and start the worker
        llm_worker = LLMWorker(model_path, tokenizer_path)
        llm_worker.start()
        
        logger.info("LLM Worker started successfully")
    except Exception as e:
        logger.error(f"Failed to start LLM worker: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of the LLM worker"""
    global llm_worker
    
    logger.info("Shutting down LLM Worker API server...")
    
    if llm_worker:
        llm_worker.stop()
        logger.info("LLM Worker stopped")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "LLM Worker API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if llm_worker:
        health_status = llm_worker.health_check()
        return health_status
    else:
        return {"status": "unhealthy", "error": "LLM worker not initialized"}

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Generate text from a prompt"""
    if not llm_worker:
        raise HTTPException(status_code=503, detail="LLM worker not available")
    
    # Validate input
    if len(request.prompt) > config.system_config.max_prompt_length:
        raise HTTPException(status_code=400, detail="Prompt too long")
    
    # Create generation config
    gen_config = GenerationConfig(
        max_new_tokens=request.max_new_tokens,
        temperature=request.temperature,
        top_p=request.top_p,
        top_k=request.top_k,
        repetition_penalty=request.repetition_penalty,
        do_sample=request.do_sample,
        stream=request.stream
    )
    
    # Submit request to worker
    start_time = time.time()
    
    try:
        if request.stream:
            # Handle streaming request
            return StreamingResponse(
                stream_generate(request.prompt, gen_config),
                media_type="text/plain"
            )
        else:
            # Handle regular request
            result = await llm_worker.generate_async(request.prompt, gen_config)
            
            end_time = time.time()
            
            response = GenerateResponse(
                id=f"gen_{uuid.uuid4()}",
                text=result,
                tokens_generated=len(result.split()),  # Approximate token count
                generation_time=end_time - start_time,
                timestamp=datetime.utcnow().isoformat()
            )
            
            return response
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

async def stream_generate(prompt: str, config: GenerationConfig):
    """Generator function for streaming responses"""
    # In a real implementation, this would stream tokens as they're generated
    # For now, we'll simulate streaming by yielding parts of the response
    
    # Submit request to worker (non-streaming for now since our worker doesn't support streaming yet)
    result = await llm_worker.generate_async(prompt, config)
    
    # Simulate streaming by breaking the result into chunks
    chunk_size = 50  # Number of characters per chunk
    for i in range(0, len(result), chunk_size):
        chunk = result[i:i+chunk_size]
        yield f"data: {json.dumps({'text': chunk})}\n\n"
        await asyncio.sleep(0.01)  # Small delay to simulate real streaming

@app.post("/generate_stream")
async def generate_stream(request: GenerateRequest):
    """Stream text generation"""
    if not llm_worker:
        raise HTTPException(status_code=503, detail="LLM worker not available")
    
    # Validate input
    if len(request.prompt) > config.system_config.max_prompt_length:
        raise HTTPException(status_code=400, detail="Prompt too long")
    
    # Create generation config
    gen_config = GenerationConfig(
        max_new_tokens=request.max_new_tokens,
        temperature=request.temperature,
        top_p=request.top_p,
        top_k=request.top_k,
        repetition_penalty=request.repetition_penalty,
        do_sample=request.do_sample,
        stream=True
    )
    
    return StreamingResponse(
        stream_generate(request.prompt, gen_config),
        media_type="text/event-stream"
    )

@app.get("/stats")
async def get_stats():
    """Get generation statistics"""
    if llm_worker:
        return llm_worker.generation_stats
    else:
        return {"error": "LLM worker not available"}

@app.post("/cancel/{request_id}")
async def cancel_generation(request_id: str):
    """Cancel a pending generation request"""
    # In a real implementation, this would cancel the specific request
    # For now, we'll just return a success message
    return {"message": f"Request {request_id} cancellation requested", "status": "not_implemented"}

# Additional endpoints for managing the worker
@app.post("/pause")
async def pause_worker():
    """Pause the LLM worker (stop processing new requests)"""
    # This would implement pausing functionality
    return {"message": "Worker pause functionality not implemented", "status": "not_implemented"}

@app.post("/resume")
async def resume_worker():
    """Resume the LLM worker (continue processing requests)"""
    # This would implement resuming functionality
    return {"message": "Worker resume functionality not implemented", "status": "not_implemented"}

@app.get("/queue")
async def get_queue_status():
    """Get queue status and pending requests"""
    if llm_worker:
        return {
            "queue_size": llm_worker.request_queue.size(),
            "workers_active": len(llm_worker.workers),
            "is_running": llm_worker.is_running
        }
    else:
        return {"error": "LLM worker not available"}

def run_api_server(host: str = "127.0.0.1", port: int = 8000):
    """Run the API server"""
    logger.info(f"Starting API server at {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    # Run the API server
    run_api_server(config.system_config.api_host, config.system_config.api_port)
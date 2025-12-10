from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from typing import Dict, Any, Optional
import json
import logging
from contextlib import asynccontextmanager

from .model_loader import model_loader
from .auto_config import auto_config

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected. Total: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)
    
    async def broadcast(self, message: str):
        disconnected_clients = []
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except:
                disconnected_clients.append(client_id)
        
        for client_id in disconnected_clients:
            self.disconnect(client_id)

connection_manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Загрузка конфигурации при запуске
    config = auto_config.generate_config()
    logger.info("Local LLM server started with auto-detected configuration")
    
    # Загрузка модели при запуске (если требуется)
    # model = model_loader.load_model("default_model_path")  # Путь к модели будет задан в конфиге
    
    yield
    
    # Очистка при завершении
    logger.info("Local LLM server shutting down")

app = FastAPI(
    title="Local LLM Inference Server",
    description="High-performance local inference server with Rust optimization",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене нужно указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Local LLM Inference Server", "status": "running"}

@app.get("/health")
async def health_check():
    """Проверка работоспособности сервера"""
    return {
        "status": "healthy",
        "rust_acceleration": model_loader.rust_acceleration,
        "rust_module_loaded": model_loader.rust_module is not None,
        "cuda_available": auto_config.cuda_info.get('available', False)
    }

@app.get("/config")
async def get_config():
    """Получение текущей конфигурации"""
    if not auto_config.config:
        auto_config.generate_config()
    return auto_config.config

@app.post("/infer")
async def inference_endpoint(data: Dict[str, Any]):
    """HTTP endpoint для инференса"""
    try:
        # Загружаем модель (в реальной реализации модель будет загружена заранее)
        # model = model_loader.load_model(data.get('model_path', 'default'))
        
        # Выполняем инференс
        result = model_loader.run_inference(None, data)  # В реальной реализации передаем модель
        
        return {
            "success": True,
            "result": result,
            "engine": result.get('engine', 'unknown')
        }
    except Exception as e:
        logger.error(f"Inference error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint для реального времени взаимодействия"""
    await connection_manager.connect(websocket, client_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Обработка сообщения
            if message_data.get("type") == "chat":
                # Выполняем инференс
                result = model_loader.run_inference(None, message_data)
                
                response = {
                    "type": "response",
                    "content": result.get('result', 'Error occurred'),
                    "engine": result.get('engine', 'unknown'),
                    "timestamp": message_data.get("timestamp", "")
                }
                
                await connection_manager.send_personal_message(json.dumps(response), client_id)
            elif message_data.get("type") == "ping":
                # Ответ на ping для проверки соединения
                await connection_manager.send_personal_message(
                    json.dumps({"type": "pong", "timestamp": message_data.get("timestamp", "")}), 
                    client_id
                )
    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        connection_manager.disconnect(client_id)

@app.get("/benchmark")
async def benchmark():
    """Тест производительности"""
    try:
        results = model_loader.benchmark_performance(50)  # 50 итераций для теста
        return {
            "benchmark_results": results,
            "rust_acceleration": model_loader.rust_acceleration,
            "message": f"Performance improvement: {results['improvement']:.2f}%"
        }
    except Exception as e:
        logger.error(f"Benchmark error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def start_server():
    """Запуск сервера"""
    config = auto_config.generate_config()
    port = config['network_settings']['local_port']
    
    logger.info(f"Starting local LLM server on port {port}")
    
    uvicorn.run(
        "local-inference.llm_server:app",  # Путь к приложению
        host="0.0.0.0",  # Слушаем на всех интерфейсах
        port=port,
        reload=False,  # В продакшене отключаем автоперезагрузку
        log_level="info"
    )

if __name__ == "__main__":
    start_server()
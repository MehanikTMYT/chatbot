from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
from typing import Dict, Any

from .config.network_config import NetworkConfig
from .services.connection_manager import ConnectionManager
from .first_run_setup import run_first_setup

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Загрузка конфигурации сети при запуске
    logger.info("Detecting network configuration...")
    network_config = NetworkConfig()
    detected_ip = network_config.detect_local_ip()
    network_mode = network_config.get_network_mode()
    
    logger.info(f"Detected local IP: {detected_ip}")
    logger.info(f"Network mode: {network_mode}")
    
    # Запуск процедуры первой настройки при необходимости
    if not os.path.exists('.first_run_complete'):
        run_first_setup()
    
    # Подключение к локальному inference серверу
    await connection_manager.connect_local_inference()
    
    yield
    
    logger.info("Shutting down application...")

# Создание FastAPI приложения
app = FastAPI(
    title="Hybrid Chatbot API Gateway",
    description="API Gateway for the hybrid chatbot system with adaptive networking",
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

# Создание менеджера соединений
connection_manager = ConnectionManager()

@app.get("/")
async def root():
    return {
        "message": "Hybrid Chatbot API Gateway",
        "status": "running",
        "network_mode": connection_manager.network_mode
    }

@app.get("/health")
async def health_check():
    """Проверка работоспособности API-шлюза"""
    return {
        "status": "healthy",
        "network_mode": connection_manager.network_mode,
        "local_inference_connected": connection_manager.local_inference_connected,
        "active_connections": len(connection_manager.active_connections)
    }

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint для взаимодействия с клиентами"""
    await connection_manager.connect_client(websocket, client_id)

@app.post("/api/chat")
async def chat_endpoint(data: Dict[str, Any]):
    """HTTP endpoint для чата (альтернатива WebSocket)"""
    try:
        # Обработка сообщения через менеджер соединений
        response = await connection_manager.process_message(data, "http_client")
        return response
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
async def get_network_config():
    """Получение текущей конфигурации сети"""
    config = NetworkConfig()
    return {
        "local_ip": config.detect_local_ip(),
        "network_mode": config.get_network_mode(),
        "connection_manager_status": {
            "local_inference_connected": connection_manager.local_inference_connected,
            "network_mode": connection_manager.network_mode
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('API_GATEWAY_PORT', '8000'))
    uvicorn.run(app, host="0.0.0.0", port=port)
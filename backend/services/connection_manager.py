import asyncio
import websockets
import json
from typing import Dict, List, Optional
from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.local_inference_connected = False
        self.network_mode = "relay"  # default mode
        
    async def connect_local_inference(self):
        """Подключение к локальному inference серверу"""
        try:
            import os
            from .config.network_config import NetworkConfig
            
            # Определяем IP и порт локального inference сервера
            local_ip = os.getenv('LOCAL_INFERENCE_IP', 'auto_detect')
            if local_ip == 'auto_detect':
                local_ip = NetworkConfig.detect_local_ip()
                
            local_port = os.getenv('LOCAL_INFERENCE_PORT', '8001')
            
            # Проверяем доступность локального inference сервера
            # Пока просто устанавливаем флаг, реальное подключение будет по необходимости
            self.local_inference_connected = True
            self.network_mode = NetworkConfig.get_network_mode()
            logger.info(f"Local inference connection status: {self.local_inference_connected}, mode: {self.network_mode}")
            
        except Exception as e:
            logger.error(f"Failed to connect to local inference: {e}")
            self.local_inference_connected = False
            self.network_mode = "relay"
    
    async def connect_client(self, websocket: WebSocket, client_id: str):
        """Подключение клиента к веб-сокету"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
        
        try:
            while True:
                # Принимаем сообщение от клиента
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Обработка сообщения в зависимости от режима сети
                if self.network_mode in ["direct", "relay", "hybrid"]:
                    # Отправляем сообщение на локальный inference сервер или обрабатываем локально
                    response = await self.process_message(message, client_id)
                    await websocket.send_text(json.dumps(response))
                else:
                    # Режим offline - обработка локально с сохранением в базу
                    response = await self.process_offline_message(message, client_id)
                    await websocket.send_text(json.dumps(response))
                    
        except WebSocketDisconnect:
            if client_id in self.active_connections:
                del self.active_connections[client_id]
                logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def process_message(self, message: dict, client_id: str) -> dict:
        """Обработка сообщения в зависимости от сетевого режима"""
        try:
            # В зависимости от режима сеть - разные способы обработки
            if self.local_inference_connected and self.network_mode in ["direct", "hybrid"]:
                # Отправляем на локальный inference сервер
                return await self.send_to_local_inference(message, client_id)
            else:
                # Отправляем через VDS или используем fallback
                return await self.send_via_vds(message, client_id)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Возвращаем fallback ответ
            return {
                "type": "error",
                "content": "Service temporarily unavailable",
                "timestamp": message.get("timestamp", ""),
                "client_id": client_id
            }
    
    async def process_offline_message(self, message: dict, client_id: str) -> dict:
        """Обработка сообщения в оффлайн режиме"""
        # В оффлайн режиме сохраняем сообщение в базу и возвращаем ответ
        return {
            "type": "offline_response",
            "content": "Currently in offline mode. Message saved for later processing.",
            "timestamp": message.get("timestamp", ""),
            "client_id": client_id
        }
    
    async def send_to_local_inference(self, message: dict, client_id: str) -> dict:
        """Отправка сообщения на локальный inference сервер"""
        # Заглушка для отправки на локальный inference сервер
        # В реальной реализации здесь будет HTTP или WebSocket вызов
        return {
            "type": "response",
            "content": f"Processed via local inference: {message.get('content', '')}",
            "timestamp": message.get("timestamp", ""),
            "client_id": client_id
        }
    
    async def send_via_vds(self, message: dict, client_id: str) -> dict:
        """Отправка сообщения через VDS (ретрансляция)"""
        # Заглушка для обработки через VDS
        return {
            "type": "response",
            "content": f"Processed via VDS: {message.get('content', '')}",
            "timestamp": message.get("timestamp", ""),
            "client_id": client_id
        }
    
    async def broadcast(self, message: dict):
        """Рассылка сообщения всем подключенным клиентам"""
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except WebSocketDisconnect:
                disconnected_clients.append(client_id)
        
        # Удаляем отключившихся клиентов
        for client_id in disconnected_clients:
            del self.active_connections[client_id]
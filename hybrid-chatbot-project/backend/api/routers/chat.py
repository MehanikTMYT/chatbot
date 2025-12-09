"""
Chat router for the Hybrid Chatbot System
Handles real-time chat communication via WebSockets and REST endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Optional
import json
import asyncio
import logging
from datetime import datetime

from database.session import get_db
from database.models import User, Conversation, Message
from api.schemas.auth import TokenData
from core.security import verify_token
from core.config import settings

router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # user_id -> websocket
        self.user_conversations: Dict[str, List[str]] = {}  # user_id -> list of conversation_ids

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_text(message)

    async def broadcast_to_user(self, message: str, user_id: str):
        await self.send_personal_message(message, user_id)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

manager = ConnectionManager()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time chat communication"""
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process the message based on type
            message_type = message_data.get("type", "message")
            
            if message_type == "message":
                # Handle chat message
                conversation_id = message_data.get("conversation_id")
                content = message_data.get("content")
                
                if not content:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "error",
                            "message": "Message content is required"
                        }),
                        user_id
                    )
                    continue
                
                # Here we would process the message through the worker system
                # For now, we'll just echo back a response
                response = {
                    "type": "message_response",
                    "conversation_id": conversation_id,
                    "sender": "bot",
                    "content": f"Echo: {content}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await manager.send_personal_message(json.dumps(response), user_id)
            
            elif message_type == "join_conversation":
                # User joins a specific conversation
                conversation_id = message_data.get("conversation_id")
                if user_id not in manager.user_conversations:
                    manager.user_conversations[user_id] = []
                if conversation_id not in manager.user_conversations[user_id]:
                    manager.user_conversations[user_id].append(conversation_id)
                
                response = {
                    "type": "joined_conversation",
                    "conversation_id": conversation_id,
                    "message": f"Joined conversation {conversation_id}"
                }
                await manager.send_personal_message(json.dumps(response), user_id)
            
            elif message_type == "ping":
                # Heartbeat/keepalive
                response = {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await manager.send_personal_message(json.dumps(response), user_id)
            
            else:
                # Unknown message type
                response = {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }
                await manager.send_personal_message(json.dumps(response), user_id)
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        # Remove user from conversations
        if user_id in manager.user_conversations:
            del manager.user_conversations[user_id]


@router.post("/conversations")
async def create_conversation(
    conversation_data: Dict,
    current_user: TokenData = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Create a new conversation"""
    try:
        title = conversation_data.get("title", "New Conversation")
        character_id = conversation_data.get("character_id")
        
        new_conversation = Conversation(
            title=title,
            user_id=current_user.get("sub"),  # user_id from token
            character_id=character_id,
            is_active=True
        )
        
        db.add(new_conversation)
        await db.commit()
        await db.refresh(new_conversation)
        
        return {
            "id": new_conversation.id,
            "title": new_conversation.title,
            "user_id": new_conversation.user_id,
            "character_id": new_conversation.character_id,
            "created_at": new_conversation.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating conversation: {str(e)}"
        )


@router.get("/conversations")
async def get_conversations(
    current_user: TokenData = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get all conversations for the current user"""
    try:
        user_id = int(current_user.get("sub"))
        
        from sqlalchemy import select
        result = await db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
        conversations = result.scalars().all()
        
        return {
            "conversations": [
                {
                    "id": conv.id,
                    "title": conv.title,
                    "character_id": conv.character_id,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                    "is_active": conv.is_active
                }
                for conv in conversations
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting conversations: {str(e)}"
        )


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: int,
    message_data: Dict,
    current_user: TokenData = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Send a message in a conversation"""
    try:
        content = message_data.get("content")
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message content is required"
            )
        
        # Verify conversation belongs to user
        from sqlalchemy import select
        result = await db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.user_id == int(current_user.get("sub")))
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or doesn't belong to user"
            )
        
        # Create user message
        user_message = Message(
            conversation_id=conversation_id,
            sender_type="user",
            content=content
        )
        
        db.add(user_message)
        await db.commit()
        await db.refresh(user_message)
        
        # Here we would process the message through the worker system
        # For now, we'll just create a simple echo response
        bot_response = Message(
            conversation_id=conversation_id,
            sender_type="bot",
            content=f"Echo response to: {content}"
        )
        
        db.add(bot_response)
        await db.commit()
        await db.refresh(bot_response)
        
        # Broadcast to WebSocket if user is connected
        user_id = str(current_user.get("sub"))
        if user_id in manager.active_connections:
            response = {
                "type": "message_response",
                "conversation_id": conversation_id,
                "messages": [
                    {
                        "id": user_message.id,
                        "sender_type": user_message.sender_type,
                        "content": user_message.content,
                        "timestamp": user_message.timestamp.isoformat()
                    },
                    {
                        "id": bot_response.id,
                        "sender_type": bot_response.sender_type,
                        "content": bot_response.content,
                        "timestamp": bot_response.timestamp.isoformat()
                    }
                ]
            }
            await manager.send_personal_message(json.dumps(response), user_id)
        
        return {
            "messages": [
                {
                    "id": user_message.id,
                    "sender_type": user_message.sender_type,
                    "content": user_message.content,
                    "timestamp": user_message.timestamp.isoformat()
                },
                {
                    "id": bot_response.id,
                    "sender_type": bot_response.sender_type,
                    "content": bot_response.content,
                    "timestamp": bot_response.timestamp.isoformat()
                }
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending message: {str(e)}"
        )


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: int,
    current_user: TokenData = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get all messages in a conversation"""
    try:
        # Verify conversation belongs to user
        from sqlalchemy import select
        result = await db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.user_id == int(current_user.get("sub")))
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or doesn't belong to user"
            )
        
        # Get messages
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.timestamp.asc())
        )
        messages = result.scalars().all()
        
        return {
            "messages": [
                {
                    "id": msg.id,
                    "sender_type": msg.sender_type,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in messages
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting messages: {str(e)}"
        )


@router.get("/status")
async def chat_status():
    """Get chat system status"""
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "timestamp": datetime.utcnow().isoformat()
    }
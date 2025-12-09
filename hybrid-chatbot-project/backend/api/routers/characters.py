"""
Characters router for the Hybrid Chatbot System
Handles character creation, management, and retrieval
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
import json

from database.session import get_db
from database.models import User, Character
from api.schemas.auth import TokenData
from core.security import verify_token

router = APIRouter()


@router.post("/")
async def create_character(
    character_data: Dict[str, Any],
    current_user: TokenData = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Create a new character"""
    try:
        name = character_data.get("name")
        description = character_data.get("description", "")
        system_prompt = character_data.get("system_prompt", "")
        is_public = character_data.get("is_public", False)
        metadata = character_data.get("metadata", {})
        
        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Character name is required"
            )
        
        new_character = Character(
            name=name,
            description=description,
            system_prompt=system_prompt,
            creator_id=int(current_user.get("sub")),  # user_id from token
            owner_id=int(current_user.get("sub")),    # character owner
            is_public=is_public,
            metadata=json.dumps(metadata) if metadata else None
        )
        
        db.add(new_character)
        await db.commit()
        await db.refresh(new_character)
        
        return {
            "id": new_character.id,
            "name": new_character.name,
            "description": new_character.description,
            "system_prompt": new_character.system_prompt,
            "creator_id": new_character.creator_id,
            "owner_id": new_character.owner_id,
            "is_public": new_character.is_public,
            "created_at": new_character.created_at.isoformat(),
            "updated_at": new_character.updated_at.isoformat(),
            "metadata": new_character.metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating character: {str(e)}"
        )


@router.get("/")
async def get_characters(
    current_user: TokenData = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get all characters accessible to the current user"""
    try:
        user_id = int(current_user.get("sub"))
        
        from sqlalchemy import select
        # Get characters owned by user and public characters
        result = await db.execute(
            select(Character)
            .where(
                (Character.owner_id == user_id) | 
                (Character.is_public == True)
            )
            .order_by(Character.created_at.desc())
        )
        characters = result.scalars().all()
        
        return {
            "characters": [
                {
                    "id": char.id,
                    "name": char.name,
                    "description": char.description,
                    "creator_id": char.creator_id,
                    "owner_id": char.owner_id,
                    "is_public": char.is_public,
                    "created_at": char.created_at.isoformat(),
                    "updated_at": char.updated_at.isoformat()
                }
                for char in characters
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting characters: {str(e)}"
        )


@router.get("/{character_id}")
async def get_character(
    character_id: int,
    current_user: TokenData = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific character by ID"""
    try:
        user_id = int(current_user.get("sub"))
        
        from sqlalchemy import select
        result = await db.execute(
            select(Character)
            .where(
                (Character.id == character_id) &
                ((Character.owner_id == user_id) | (Character.is_public == True))
            )
        )
        character = result.scalar_one_or_none()
        
        if not character:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Character not found or not accessible"
            )
        
        return {
            "id": character.id,
            "name": character.name,
            "description": character.description,
            "system_prompt": character.system_prompt,
            "creator_id": character.creator_id,
            "owner_id": character.owner_id,
            "is_public": character.is_public,
            "created_at": character.created_at.isoformat(),
            "updated_at": character.updated_at.isoformat(),
            "metadata": character.metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting character: {str(e)}"
        )


@router.put("/{character_id}")
async def update_character(
    character_id: int,
    character_data: Dict[str, Any],
    current_user: TokenData = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Update a specific character (must be owner)"""
    try:
        user_id = int(current_user.get("sub"))
        
        from sqlalchemy import select
        result = await db.execute(
            select(Character)
            .where(Character.id == character_id)
            .where(Character.owner_id == user_id)
        )
        character = result.scalar_one_or_none()
        
        if not character:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Character not found or you don't have permission to edit it"
            )
        
        # Update allowed fields
        if "name" in character_data:
            character.name = character_data["name"]
        if "description" in character_data:
            character.description = character_data["description"]
        if "system_prompt" in character_data:
            character.system_prompt = character_data["system_prompt"]
        if "is_public" in character_data:
            character.is_public = character_data["is_public"]
        if "metadata" in character_data:
            character.metadata = json.dumps(character_data["metadata"])
        
        await db.commit()
        await db.refresh(character)
        
        return {
            "id": character.id,
            "name": character.name,
            "description": character.description,
            "system_prompt": character.system_prompt,
            "creator_id": character.creator_id,
            "owner_id": character.owner_id,
            "is_public": character.is_public,
            "created_at": character.created_at.isoformat(),
            "updated_at": character.updated_at.isoformat(),
            "metadata": character.metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating character: {str(e)}"
        )


@router.delete("/{character_id}")
async def delete_character(
    character_id: int,
    current_user: TokenData = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Delete a specific character (must be owner)"""
    try:
        user_id = int(current_user.get("sub"))
        
        from sqlalchemy import select
        result = await db.execute(
            select(Character)
            .where(Character.id == character_id)
            .where(Character.owner_id == user_id)
        )
        character = result.scalar_one_or_none()
        
        if not character:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Character not found or you don't have permission to delete it"
            )
        
        await db.delete(character)
        await db.commit()
        
        return {
            "message": "Character deleted successfully",
            "character_id": character_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting character: {str(e)}"
        )


@router.get("/public")
async def get_public_characters(
    current_user: TokenData = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get all public characters"""
    try:
        from sqlalchemy import select
        result = await db.execute(
            select(Character)
            .where(Character.is_public == True)
            .order_by(Character.created_at.desc())
        )
        characters = result.scalars().all()
        
        return {
            "characters": [
                {
                    "id": char.id,
                    "name": char.name,
                    "description": char.description,
                    "creator_id": char.creator_id,
                    "created_at": char.created_at.isoformat(),
                    "updated_at": char.updated_at.isoformat()
                }
                for char in characters
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting public characters: {str(e)}"
        )


@router.get("/my")
async def get_my_characters(
    current_user: TokenData = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get characters owned by the current user"""
    try:
        user_id = int(current_user.get("sub"))
        
        from sqlalchemy import select
        result = await db.execute(
            select(Character)
            .where(Character.owner_id == user_id)
            .order_by(Character.created_at.desc())
        )
        characters = result.scalars().all()
        
        return {
            "characters": [
                {
                    "id": char.id,
                    "name": char.name,
                    "description": char.description,
                    "is_public": char.is_public,
                    "created_at": char.created_at.isoformat(),
                    "updated_at": char.updated_at.isoformat()
                }
                for char in characters
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting user's characters: {str(e)}"
        )
import logging
import asyncio
import random
from typing import Optional, Dict, Any, Tuple
from telethon import TelegramClient
from telethon.errors import (
    UsernameNotOccupiedError, UsernameOccupiedError, UsernameInvalidError,
    ChatAdminRequiredError, ChannelPrivateError, SessionPasswordNeededError,
    FloodWaitError, AuthKeyUnregisteredError
)
from telethon.tl.functions.channels import GetFullChannelRequest, UpdateUsernameRequest
from telethon.tl.functions.messages import GetFullChatRequest
from telethon.tl.types import Channel, Chat, User

logger = logging.getLogger(__name__)

_client: Optional[TelegramClient] = None
_session_data: Dict[str, Any] = {}

class TelethonManagerError(Exception):
    """Base exception for Telethon manager errors"""
    pass

class ChannelResolutionError(TelethonManagerError):
    """Raised when channel cannot be resolved"""
    pass

class PermissionError(TelethonManagerError):
    """Raised when insufficient permissions"""
    pass

class UsernameChangeError(TelethonManagerError):
    """Raised when username change fails"""
    pass

def get_status() -> str:
    """Get Telethon client status"""
    if _client and _client.is_connected():
        return "ready"
    return "not_configured"

async def init_client(api_id: str, api_hash: str, phone: str, password: str = None) -> bool:
    """Initialize Telethon client with proper error handling"""
    global _client, _session_data
    
    try:
        _client = TelegramClient(f"sessions/guardian_{phone}", api_id, api_hash)
        await _client.start(phone=phone, password=password)
        
        if not _client.is_connected():
            logger.error("telethon_connection_failed")
            return False
            
        me = await _client.get_me()
        _session_data = {
            "user_id": me.id,
            "phone": phone,
            "connected": True
        }
        
        logger.info("telethon_initialized_successfully", extra={
            "user_id": me.id,
            "phone": phone
        })
        return True
        
    except SessionPasswordNeededError:
        logger.error("telethon_2fa_required")
        raise TelethonManagerError("Two-factor authentication required")
    except AuthKeyUnregisteredError:
        logger.error("telethon_auth_failed")
        raise TelethonManagerError("Authentication failed")
    except Exception as e:
        logger.error("telethon_init_error", extra={"error": str(e)})
        raise TelethonManagerError(f"Initialization failed: {str(e)}")

async def resolve_channel_entity(channel_input: str) -> Tuple[int, Channel]:
    """
    Resolve channel from username/link to entity and ID
    Returns: (channel_id, channel_entity)
    """
    if not _client or not _client.is_connected():
        raise TelethonManagerError("Telethon client not connected")
    
    try:
        # Clean input
        if channel_input.startswith('https://t.me/'):
            channel_input = channel_input.split('/')[-1]
        if channel_input.startswith('@'):
            channel_input = channel_input[1:]
        
        # Resolve entity
        entity = await _client.get_entity(channel_input)
        
        if not isinstance(entity, Channel):
            raise ChannelResolutionError(f"Entity is not a channel: {type(entity)}")
        
        channel_id = entity.id
        logger.info("channel_resolved", extra={
            "input": channel_input,
            "channel_id": channel_id,
            "username": getattr(entity, 'username', None)
        })
        
        return channel_id, entity
        
    except ValueError as e:
        logger.error("channel_resolution_failed", extra={
            "input": channel_input,
            "error": str(e)
        })
        raise ChannelResolutionError(f"Cannot resolve channel: {channel_input}")
    except Exception as e:
        logger.error("channel_resolution_error", extra={
            "input": channel_input,
            "error": str(e)
        })
        raise ChannelResolutionError(f"Resolution error: {str(e)}")

async def check_channel_permissions(channel_id: int) -> Dict[str, bool]:
    """
    Check if current user has admin permissions on channel
    Returns: Dict with permission status
    """
    if not _client or not _client.is_connected():
        raise TelethonManagerError("Telethon client not connected")
    
    try:
        # Get full channel info
        full_channel = await _client(GetFullChannelRequest(channel_id))
        participant = full_channel.full_chat.participants.participants[0] if full_channel.full_chat.participants else None
        
        if not participant:
            return {
                "is_admin": False,
                "can_change_info": False,
                "can_view_participants": False,
                "reason": "not_participant"
            }
        
        # Check admin permissions
        is_admin = hasattr(participant, 'admin_rights') and participant.admin_rights
        can_change_info = is_admin and participant.admin_rights.change_info if is_admin else False
        can_view_participants = is_admin and participant.admin_rights.view_participants if is_admin else False
        
        permissions = {
            "is_admin": is_admin,
            "can_change_info": can_change_info,
            "can_view_participants": can_view_participants,
            "reason": "success" if is_admin else "not_admin"
        }
        
        logger.info("permissions_checked", extra={
            "channel_id": channel_id,
            **permissions
        })
        
        return permissions
        
    except Exception as e:
        logger.error("permission_check_failed", extra={
            "channel_id": channel_id,
            "error": str(e)
        })
        return {
            "is_admin": False,
            "can_change_info": False,
            "can_view_participants": False,
            "reason": f"check_error: {str(e)}"
        }

async def verify_username_change(channel_id: int, target_username: str) -> bool:
    """
    Verify that username was actually changed by reading from Telegram
    Returns: True if verification successful, False otherwise
    """
    if not _client or not _client.is_connected():
        return False
    
    try:
        # Wait a bit for changes to propagate
        await asyncio.sleep(2)
        
        # Get current channel info
        entity = await _client.get_entity(channel_id)
        current_username = getattr(entity, 'username', None)
        
        # Compare with target
        verification_ok = current_username == target_username
        
        logger.info("username_verification", extra={
            "channel_id": channel_id,
            "target_username": target_username,
            "current_username": current_username,
            "verification_ok": verification_ok
        })
        
        return verification_ok
        
    except Exception as e:
        logger.error("username_verification_failed", extra={
            "channel_id": channel_id,
            "target_username": target_username,
            "error": str(e)
        })
        return False

async def change_channel_link(channel_id: int, new_username: str, trace_id: str = None) -> Dict[str, Any]:
    """
    Change channel username with proper error handling and verification
    Returns: Dict with operation result
    """
    if not _client or not _client.is_connected():
        raise TelethonManagerError("Telethon client not connected")
    
    trace_id = trace_id or f"rot_{random.randint(1000, 9999)}"
    
    try:
        # Step 1: Check permissions
        permissions = await check_channel_permissions(channel_id)
        if not permissions["is_admin"]:
            raise PermissionError(f"Not admin on channel {channel_id}")
        if not permissions["can_change_info"]:
            raise PermissionError(f"Cannot change info on channel {channel_id}")
        
        # Step 2: Attempt username change
        logger.info("username_change_attempt", extra={
            "channel_id": channel_id,
            "new_username": new_username,
            "trace_id": trace_id
        })
        
        await _client(UpdateUsernameRequest(channel_id, new_username))
        
        # Step 3: Verify the change
        verification_ok = await verify_username_change(channel_id, new_username)
        
        if verification_ok:
            logger.info("username_change_success", extra={
                "channel_id": channel_id,
                "new_username": new_username,
                "trace_id": trace_id
            })
            return {
                "success": True,
                "channel_id": channel_id,
                "new_username": new_username,
                "trace_id": trace_id,
                "verified": True
            }
        else:
            logger.error("username_change_verification_failed", extra={
                "channel_id": channel_id,
                "new_username": new_username,
                "trace_id": trace_id
            })
            return {
                "success": False,
                "channel_id": channel_id,
                "new_username": new_username,
                "trace_id": trace_id,
                "verified": False,
                "reason": "verification_failed"
            }
            
    except UsernameOccupiedError:
        logger.warning("username_occupied", extra={
            "channel_id": channel_id,
            "new_username": new_username,
            "trace_id": trace_id
        })
        raise UsernameChangeError(f"Username {new_username} is occupied")
        
    except UsernameInvalidError:
        logger.warning("username_invalid", extra={
            "channel_id": channel_id,
            "new_username": new_username,
            "trace_id": trace_id
        })
        raise UsernameChangeError(f"Username {new_username} is invalid")
        
    except ChatAdminRequiredError:
        logger.error("admin_required", extra={
            "channel_id": channel_id,
            "new_username": new_username,
            "trace_id": trace_id
        })
        raise PermissionError(f"Admin rights required for channel {channel_id}")
        
    except FloodWaitError as e:
        logger.error("flood_wait", extra={
            "channel_id": channel_id,
            "new_username": new_username,
            "trace_id": trace_id,
            "wait_time": e.seconds
        })
        raise TelethonManagerError(f"Rate limited, wait {e.seconds} seconds")
        
    except Exception as e:
        logger.error("username_change_error", extra={
            "channel_id": channel_id,
            "new_username": new_username,
            "trace_id": trace_id,
            "error": str(e)
        })
        raise UsernameChangeError(f"Change failed: {str(e)}")

async def get_channel_current_state(channel_id: int) -> Dict[str, Any]:
    """
    Get current channel state from Telegram
    Returns: Dict with current channel information
    """
    if not _client or not _client.is_connected():
        return {"error": "client_not_connected"}
    
    try:
        entity = await _client.get_entity(channel_id)
        full_channel = await _client(GetFullChannelRequest(channel_id))
        
        return {
            "channel_id": channel_id,
            "username": getattr(entity, 'username', None),
            "title": getattr(entity, 'title', None),
            "participants_count": getattr(full_channel.full_chat, 'participants_count', 0),
            "description": getattr(full_channel.full_chat, 'about', None)
        }
        
    except Exception as e:
        logger.error("get_channel_state_failed", extra={
            "channel_id": channel_id,
            "error": str(e)
        })
        return {"error": str(e)}

async def disconnect():
    """Disconnect Telethon client"""
    global _client
    if _client:
        await _client.disconnect()
        _client = None
        logger.info("telethon_disconnected")

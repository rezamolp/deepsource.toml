import logging
import random
import asyncio
from typing import Optional, Dict, Any, List
from services import telethon_manager
from services.telethon_manager import (
    TelethonManagerError, ChannelResolutionError, 
    PermissionError, UsernameChangeError
)

logger = logging.getLogger(__name__)

# Global state for rotation tracking
_rotation_stats = {
    "success_count": 0,
    "fail_count": 0,
    "last_suffix": 0,
    "last_rotation_time": None
}

class LinkRotationError(Exception):
    """Base exception for link rotation errors"""
    pass

async def resolve_channel_from_input(channel_input: str) -> Dict[str, Any]:
    """
    Resolve channel from various input formats and check permissions
    Returns: Dict with channel info and permissions
    """
    try:
        # Resolve channel entity
        channel_id, channel_entity = await telethon_manager.resolve_channel_entity(channel_input)
        
        # Check permissions
        permissions = await telethon_manager.check_channel_permissions(channel_id)
        
        # Get current state
        current_state = await telethon_manager.get_channel_current_state(channel_id)
        
        result = {
            "channel_id": channel_id,
            "channel_entity": channel_entity,
            "permissions": permissions,
            "current_state": current_state,
            "resolved": True
        }
        
        logger.info("channel_resolution_complete", extra={
            "channel_id": channel_id,
            "input": channel_input,
            "is_admin": permissions.get("is_admin", False),
            "can_change_info": permissions.get("can_change_info", False)
        })
        
        return result
        
    except ChannelResolutionError as e:
        logger.error("channel_resolution_failed", extra={
            "input": channel_input,
            "error": str(e)
        })
        raise LinkRotationError(f"Channel resolution failed: {str(e)}")
    except Exception as e:
        logger.error("channel_resolution_error", extra={
            "input": channel_input,
            "error": str(e)
        })
        raise LinkRotationError(f"Resolution error: {str(e)}")

async def change_public_link(channel_input: str, base_username: str, trace_id: str = None) -> Dict[str, Any]:
    """
    Change channel public link with comprehensive error handling and verification
    Returns: Dict with operation result
    """
    trace_id = trace_id or f"rot_{random.randint(1000, 9999)}"
    
    try:
        # Step 1: Resolve channel and check permissions
        channel_info = await resolve_channel_from_input(channel_input)
        channel_id = channel_info["channel_id"]
        permissions = channel_info["permissions"]
        
        # Step 2: Validate permissions
        if not permissions["is_admin"]:
            raise LinkRotationError("Not admin on channel")
        if not permissions["can_change_info"]:
            raise LinkRotationError("Cannot change channel info - insufficient permissions")
        
        # Step 3: Try username rotation with fallback
        result = await _attempt_username_rotation(channel_id, base_username, trace_id)
        
        # Step 4: Update statistics
        if result["success"]:
            _rotation_stats["success_count"] += 1
            _rotation_stats["last_rotation_time"] = asyncio.get_event_loop().time()
        else:
            _rotation_stats["fail_count"] += 1
        
        logger.info("link_rotation_completed", extra={
            "channel_id": channel_id,
            "base_username": base_username,
            "trace_id": trace_id,
            "success": result["success"],
            "new_username": result.get("new_username"),
            "reason": result.get("reason")
        })
        
        return result
        
    except LinkRotationError:
        raise
    except Exception as e:
        logger.error("link_rotation_unexpected_error", extra={
            "channel_input": channel_input,
            "base_username": base_username,
            "trace_id": trace_id,
            "error": str(e)
        })
        raise LinkRotationError(f"Unexpected error: {str(e)}")

async def _attempt_username_rotation(channel_id: int, base_username: str, trace_id: str) -> Dict[str, Any]:
    """
    Attempt username rotation with multiple suffixes
    Returns: Dict with rotation result
    """
    max_attempts = 100
    start_suffix = _rotation_stats["last_suffix"] + 1
    
    for attempt in range(max_attempts):
        suffix = (start_suffix + attempt) % 100
        if suffix == 0:
            suffix = 100
        
        new_username = f"{base_username}{suffix}"
        
        try:
            logger.info("username_rotation_attempt", extra={
                "channel_id": channel_id,
                "new_username": new_username,
                "attempt": attempt + 1,
                "trace_id": trace_id
            })
            
            # Attempt username change
            result = await telethon_manager.change_channel_link(channel_id, new_username, trace_id)
            
            if result["success"] and result["verified"]:
                # Success - update last suffix
                _rotation_stats["last_suffix"] = suffix
                
                return {
                    "success": True,
                    "new_username": new_username,
                    "channel_id": channel_id,
                    "trace_id": trace_id,
                    "attempts": attempt + 1,
                    "verified": True
                }
            else:
                # Change failed or verification failed
                logger.warning("username_rotation_verification_failed", extra={
                    "channel_id": channel_id,
                    "new_username": new_username,
                    "trace_id": trace_id,
                    "reason": result.get("reason", "unknown")
                })
                continue
                
        except UsernameChangeError as e:
            # Username occupied or invalid - try next
            logger.debug("username_rotation_attempt_failed", extra={
                "channel_id": channel_id,
                "new_username": new_username,
                "trace_id": trace_id,
                "error": str(e)
            })
            continue
            
        except PermissionError as e:
            # Permission error - stop trying
            logger.error("username_rotation_permission_error", extra={
                "channel_id": channel_id,
                "new_username": new_username,
                "trace_id": trace_id,
                "error": str(e)
            })
            return {
                "success": False,
                "channel_id": channel_id,
                "trace_id": trace_id,
                "reason": f"permission_error: {str(e)}",
                "attempts": attempt + 1
            }
            
        except TelethonManagerError as e:
            # Other telethon errors - stop trying
            logger.error("username_rotation_telethon_error", extra={
                "channel_id": channel_id,
                "new_username": new_username,
                "trace_id": trace_id,
                "error": str(e)
            })
            return {
                "success": False,
                "channel_id": channel_id,
                "trace_id": trace_id,
                "reason": f"telethon_error: {str(e)}",
                "attempts": attempt + 1
            }
            
        except Exception as e:
            # Unexpected error - stop trying
            logger.error("username_rotation_unexpected_error", extra={
                "channel_id": channel_id,
                "new_username": new_username,
                "trace_id": trace_id,
                "error": str(e)
            })
            return {
                "success": False,
                "channel_id": channel_id,
                "trace_id": trace_id,
                "reason": f"unexpected_error: {str(e)}",
                "attempts": attempt + 1
            }
    
    # All attempts failed
    logger.error("username_rotation_exhausted", extra={
        "channel_id": channel_id,
        "base_username": base_username,
        "trace_id": trace_id,
        "attempts": max_attempts
    })
    
    return {
        "success": False,
        "channel_id": channel_id,
        "trace_id": trace_id,
        "reason": "all_usernames_occupied_or_invalid",
        "attempts": max_attempts
    }

async def get_rotation_status(channel_input: str = None) -> Dict[str, Any]:
    """
    Get comprehensive rotation status including real channel state
    Returns: Dict with status information
    """
    status = {
        "telethon_status": telethon_manager.get_status(),
        "rotation_stats": _rotation_stats.copy(),
        "timestamp": asyncio.get_event_loop().time()
    }
    
    # If channel input provided, get real channel state
    if channel_input:
        try:
            channel_info = await resolve_channel_from_input(channel_input)
            status["channel_info"] = {
                "channel_id": channel_info["channel_id"],
                "current_state": channel_info["current_state"],
                "permissions": channel_info["permissions"]
            }
        except Exception as e:
            status["channel_info"] = {
                "error": str(e),
                "input": channel_input
            }
    
    return status

def get_rotation_statistics() -> Dict[str, Any]:
    """Get rotation statistics"""
    return _rotation_stats.copy()

async def reset_rotation_statistics():
    """Reset rotation statistics"""
    global _rotation_stats
    _rotation_stats = {
        "success_count": 0,
        "fail_count": 0,
        "last_suffix": 0,
        "last_rotation_time": None
    }
    logger.info("rotation_statistics_reset")

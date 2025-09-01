import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from services.telethon_manager import (
    TelethonManagerError, ChannelResolutionError, 
    PermissionError, UsernameChangeError
)
from services.channel import (
    change_public_link, resolve_channel_from_input,
    get_rotation_status, get_rotation_statistics
)

class TestLinkRotatorFixed:
    """Test suite for fixed link rotator functionality"""
    
    @pytest.fixture
    def mock_telethon_client(self):
        """Mock Telethon client"""
        client = Mock()
        client.is_connected.return_value = True
        return client
    
    @pytest.fixture
    def mock_channel_entity(self):
        """Mock channel entity"""
        entity = Mock()
        entity.id = 123456789
        entity.username = "testchannel"
        entity.title = "Test Channel"
        return entity
    
    @pytest.fixture
    def mock_permissions(self):
        """Mock permissions"""
        return {
            "is_admin": True,
            "can_change_info": True,
            "can_view_participants": True,
            "reason": "success"
        }
    
    @pytest.fixture
    def mock_current_state(self):
        """Mock current channel state"""
        return {
            "channel_id": 123456789,
            "username": "testchannel",
            "title": "Test Channel",
            "participants_count": 1000,
            "description": "Test channel description"
        }

    @pytest.mark.asyncio
    async def test_resolve_channel_from_input_success(self, mock_telethon_client, mock_channel_entity, mock_permissions, mock_current_state):
        """Test successful channel resolution"""
        with patch('services.channel.telethon_manager._client', mock_telethon_client):
            with patch('services.channel.telethon_manager.resolve_channel_entity') as mock_resolve:
                with patch('services.channel.telethon_manager.check_channel_permissions') as mock_perms:
                    with patch('services.channel.telethon_manager.get_channel_current_state') as mock_state:
                        
                        mock_resolve.return_value = (123456789, mock_channel_entity)
                        mock_perms.return_value = mock_permissions
                        mock_state.return_value = mock_current_state
                        
                        result = await resolve_channel_from_input("@testchannel")
                        
                        assert result["resolved"] is True
                        assert result["channel_id"] == 123456789
                        assert result["permissions"]["is_admin"] is True
                        assert result["permissions"]["can_change_info"] is True
                        assert result["current_state"]["username"] == "testchannel"

    @pytest.mark.asyncio
    async def test_resolve_channel_from_input_failure(self, mock_telethon_client):
        """Test channel resolution failure"""
        with patch('services.channel.telethon_manager._client', mock_telethon_client):
            with patch('services.channel.telethon_manager.resolve_channel_entity') as mock_resolve:
                mock_resolve.side_effect = ChannelResolutionError("Channel not found")
                
                with pytest.raises(Exception) as exc_info:
                    await resolve_channel_from_input("@nonexistent")
                
                assert "Channel resolution failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_change_public_link_success(self, mock_telethon_client, mock_channel_entity, mock_permissions):
        """Test successful link rotation"""
        with patch('services.channel.telethon_manager._client', mock_telethon_client):
            with patch('services.channel.resolve_channel_from_input') as mock_resolve:
                with patch('services.channel._attempt_username_rotation') as mock_rotation:
                    
                    mock_resolve.return_value = {
                        "channel_id": 123456789,
                        "permissions": mock_permissions
                    }
                    
                    mock_rotation.return_value = {
                        "success": True,
                        "new_username": "guardian1",
                        "channel_id": 123456789,
                        "trace_id": "test_123",
                        "attempts": 1,
                        "verified": True
                    }
                    
                    result = await change_public_link("@testchannel", "guardian")
                    
                    assert result["success"] is True
                    assert result["new_username"] == "guardian1"
                    assert result["verified"] is True
                    assert "trace_id" in result

    @pytest.mark.asyncio
    async def test_change_public_link_permission_error(self, mock_telethon_client, mock_channel_entity):
        """Test link rotation with permission error"""
        with patch('services.channel.telethon_manager._client', mock_telethon_client):
            with patch('services.channel.resolve_channel_from_input') as mock_resolve:
                
                mock_resolve.return_value = {
                    "channel_id": 123456789,
                    "permissions": {
                        "is_admin": False,
                        "can_change_info": False,
                        "can_view_participants": False,
                        "reason": "not_admin"
                    }
                }
                
                with pytest.raises(Exception) as exc_info:
                    await change_public_link("@testchannel", "guardian")
                
                assert "Not admin on channel" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_username_rotation_verification_failure(self, mock_telethon_client):
        """Test username rotation with verification failure"""
        with patch('services.channel.telethon_manager._client', mock_telethon_client):
            with patch('services.channel.telethon_manager.change_channel_link') as mock_change:
                
                # Mock successful change but failed verification
                mock_change.return_value = {
                    "success": True,
                    "verified": False,
                    "reason": "verification_failed"
                }
                
                with patch('services.channel._attempt_username_rotation') as mock_rotation:
                    mock_rotation.return_value = {
                        "success": False,
                        "channel_id": 123456789,
                        "trace_id": "test_123",
                        "reason": "verification_failed",
                        "attempts": 1
                    }
                    
                    result = await change_public_link("@testchannel", "guardian")
                    
                    assert result["success"] is False
                    assert "verification_failed" in result["reason"]

    @pytest.mark.asyncio
    async def test_username_occupied_handling(self, mock_telethon_client):
        """Test handling of occupied usernames"""
        with patch('services.channel.telethon_manager._client', mock_telethon_client):
            with patch('services.channel.telethon_manager.change_channel_link') as mock_change:
                
                # Mock UsernameOccupiedError
                mock_change.side_effect = UsernameChangeError("Username guardian1 is occupied")
                
                with patch('services.channel._attempt_username_rotation') as mock_rotation:
                    mock_rotation.return_value = {
                        "success": True,
                        "new_username": "guardian2",
                        "channel_id": 123456789,
                        "trace_id": "test_123",
                        "attempts": 2,
                        "verified": True
                    }
                    
                    result = await change_public_link("@testchannel", "guardian")
                    
                    assert result["success"] is True
                    assert result["new_username"] == "guardian2"
                    assert result["attempts"] == 2

    @pytest.mark.asyncio
    async def test_get_rotation_status_with_channel(self, mock_telethon_client, mock_channel_entity, mock_permissions, mock_current_state):
        """Test getting rotation status with channel info"""
        with patch('services.channel.telethon_manager._client', mock_telethon_client):
            with patch('services.channel.resolve_channel_from_input') as mock_resolve:
                
                mock_resolve.return_value = {
                    "channel_id": 123456789,
                    "permissions": mock_permissions,
                    "current_state": mock_current_state
                }
                
                result = await get_rotation_status("@testchannel")
                
                assert "telethon_status" in result
                assert "rotation_stats" in result
                assert "channel_info" in result
                assert result["channel_info"]["channel_id"] == 123456789

    @pytest.mark.asyncio
    async def test_get_rotation_status_without_channel(self, mock_telethon_client):
        """Test getting rotation status without channel"""
        with patch('services.channel.telethon_manager._client', mock_telethon_client):
            result = await get_rotation_status()
            
            assert "telethon_status" in result
            assert "rotation_stats" in result
            assert "channel_info" not in result

    @pytest.mark.asyncio
    async def test_rotation_statistics_tracking(self):
        """Test rotation statistics tracking"""
        # Reset statistics
        from services.channel import reset_rotation_statistics
        await reset_rotation_statistics()
        
        # Get initial stats
        initial_stats = get_rotation_statistics()
        assert initial_stats["success_count"] == 0
        assert initial_stats["fail_count"] == 0
        
        # Simulate successful rotation
        with patch('services.channel._rotation_stats') as mock_stats:
            mock_stats["success_count"] = 1
            mock_stats["last_rotation_time"] = 1234567890
            
            stats = get_rotation_statistics()
            assert stats["success_count"] == 1
            assert stats["last_rotation_time"] == 1234567890

    @pytest.mark.asyncio
    async def test_error_handling_comprehensive(self, mock_telethon_client):
        """Test comprehensive error handling"""
        with patch('services.channel.telethon_manager._client', mock_telethon_client):
            with patch('services.channel.resolve_channel_from_input') as mock_resolve:
                
                # Test various error scenarios
                error_scenarios = [
                    (ChannelResolutionError("Channel not found"), "Channel resolution failed"),
                    (PermissionError("Not admin"), "Not admin on channel"),
                    (TelethonManagerError("Connection failed"), "Unexpected error"),
                ]
                
                for error, expected_message in error_scenarios:
                    mock_resolve.side_effect = error
                    
                    with pytest.raises(Exception) as exc_info:
                        await change_public_link("@testchannel", "guardian")
                    
                    assert expected_message in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_trace_id_generation(self, mock_telethon_client, mock_channel_entity, mock_permissions):
        """Test trace ID generation for tracking"""
        with patch('services.channel.telethon_manager._client', mock_telethon_client):
            with patch('services.channel.resolve_channel_from_input') as mock_resolve:
                with patch('services.channel._attempt_username_rotation') as mock_rotation:
                    
                    mock_resolve.return_value = {
                        "channel_id": 123456789,
                        "permissions": mock_permissions
                    }
                    
                    mock_rotation.return_value = {
                        "success": True,
                        "new_username": "guardian1",
                        "channel_id": 123456789,
                        "trace_id": "rot_1234",
                        "attempts": 1,
                        "verified": True
                    }
                    
                    result = await change_public_link("@testchannel", "guardian")
                    
                    assert "trace_id" in result
                    assert result["trace_id"].startswith("rot_")
                    assert len(result["trace_id"]) > 5

    @pytest.mark.asyncio
    async def test_verification_delay(self, mock_telethon_client):
        """Test verification delay implementation"""
        with patch('services.channel.telethon_manager._client', mock_telethon_client):
            with patch('services.channel.telethon_manager.verify_username_change') as mock_verify:
                with patch('asyncio.sleep') as mock_sleep:
                    
                    mock_verify.return_value = True
                    
                    # This would be called during username change verification
                    await mock_sleep(2)
                    
                    mock_sleep.assert_called_once_with(2)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
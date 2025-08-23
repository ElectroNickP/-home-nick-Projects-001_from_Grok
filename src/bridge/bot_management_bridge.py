"""
Bot Management Bridge for integrating old and new bot management systems.

This module provides a bridge between the existing bot_manager and the new
hexagonal architecture's bot management system.
"""

import logging
import threading
import asyncio
from typing import Dict, Any, Optional, Tuple

from core.usecases.bot_management import BotManagementUseCase
from core.domain.bot import BotConfig

# Import existing bot manager
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import bot_manager as legacy_bot_manager
import config_manager as legacy_config

logger = logging.getLogger(__name__)


class BotManagementBridge:
    """
    Bridge between legacy bot_manager and new bot management system.
    
    This class provides seamless integration between the old threading-based
    bot management and the new use-case-driven bot management system.
    """
    
    def __init__(self, bot_management_use_case: BotManagementUseCase):
        """Initialize the bot management bridge."""
        self.use_case = bot_management_use_case
        self._operation_lock = threading.Lock()
        self._use_new_system = True
        self._fallback_enabled = True
        
        logger.info("BotManagementBridge initialized")
    
    def start_bot(self, bot_id: int) -> Tuple[bool, str]:
        """
        Start a bot using the unified system.
        
        Tries the new system first, falls back to legacy if needed.
        
        Args:
            bot_id: ID of the bot to start
            
        Returns:
            Tuple of (success, message)
        """
        with self._operation_lock:
            logger.info(f"Starting bot {bot_id} using unified system")
            
            if self._use_new_system:
                try:
                    # Try new system first
                    result = self.use_case.start_bot(bot_id)
                    
                    if result.get("success", False):
                        logger.info(f"Bot {bot_id} started successfully using new system")
                        
                        # Sync status to legacy system
                        self._sync_bot_status_to_legacy(bot_id, "running")
                        
                        return True, result.get("message", "Bot started successfully")
                    else:
                        logger.warning(f"New system failed to start bot {bot_id}: {result.get('message')}")
                        
                        if self._fallback_enabled:
                            return self._fallback_start_bot(bot_id)
                        else:
                            return False, result.get("message", "Failed to start bot")
                            
                except Exception as e:
                    logger.error(f"Exception in new system when starting bot {bot_id}: {e}")
                    
                    if self._fallback_enabled:
                        return self._fallback_start_bot(bot_id)
                    else:
                        return False, f"Failed to start bot: {str(e)}"
            else:
                # Use legacy system only
                return self._fallback_start_bot(bot_id)
    
    def stop_bot(self, bot_id: int) -> Tuple[bool, str]:
        """
        Stop a bot using the unified system.
        
        Args:
            bot_id: ID of the bot to stop
            
        Returns:
            Tuple of (success, message)
        """
        with self._operation_lock:
            logger.info(f"Stopping bot {bot_id} using unified system")
            
            if self._use_new_system:
                try:
                    # Try new system first
                    result = self.use_case.stop_bot(bot_id)
                    
                    if result.get("success", False):
                        logger.info(f"Bot {bot_id} stopped successfully using new system")
                        
                        # Sync status to legacy system
                        self._sync_bot_status_to_legacy(bot_id, "stopped")
                        
                        return True, result.get("message", "Bot stopped successfully")
                    else:
                        logger.warning(f"New system failed to stop bot {bot_id}: {result.get('message')}")
                        
                        if self._fallback_enabled:
                            return self._fallback_stop_bot(bot_id)
                        else:
                            return False, result.get("message", "Failed to stop bot")
                            
                except Exception as e:
                    logger.error(f"Exception in new system when stopping bot {bot_id}: {e}")
                    
                    if self._fallback_enabled:
                        return self._fallback_stop_bot(bot_id)
                    else:
                        return False, f"Failed to stop bot: {str(e)}"
            else:
                # Use legacy system only
                return self._fallback_stop_bot(bot_id)
    
    def restart_bot(self, bot_id: int) -> Tuple[bool, str]:
        """
        Restart a bot using the unified system.
        
        Args:
            bot_id: ID of the bot to restart
            
        Returns:
            Tuple of (success, message)
        """
        logger.info(f"Restarting bot {bot_id}")
        
        # Stop the bot first
        stop_success, stop_message = self.stop_bot(bot_id)
        
        if not stop_success:
            return False, f"Failed to stop bot for restart: {stop_message}"
        
        # Start the bot again
        start_success, start_message = self.start_bot(bot_id)
        
        if not start_success:
            return False, f"Failed to start bot after stop: {start_message}"
        
        return True, "Bot restarted successfully"
    
    def get_bot_status(self, bot_id: int) -> Dict[str, Any]:
        """
        Get bot status from unified system.
        
        Args:
            bot_id: ID of the bot
            
        Returns:
            Dict containing bot status information
        """
        try:
            # Try new system first
            if self._use_new_system:
                result = self.use_case.get_bot(bot_id)
                
                if result.get("success", False):
                    bot = result.get("bot", {})
                    return {
                        "success": True,
                        "status": bot.get("status", "unknown"),
                        "name": bot.get("name", ""),
                        "id": bot_id,
                        "source": "new_system"
                    }
            
            # Fallback to legacy system
            return self._get_legacy_bot_status(bot_id)
            
        except Exception as e:
            logger.error(f"Failed to get bot status for {bot_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "unknown"
            }
    
    def list_bots(self) -> Dict[str, Any]:
        """
        List all bots from unified system.
        
        Returns:
            Dict containing list of bots
        """
        try:
            # Try new system first
            if self._use_new_system:
                result = self.use_case.list_bots()
                
                if result.get("success", False):
                    return {
                        "success": True,
                        "bots": result.get("bots", []),
                        "total": result.get("total", 0),
                        "source": "new_system"
                    }
            
            # Fallback to legacy system
            return self._list_legacy_bots()
            
        except Exception as e:
            logger.error(f"Failed to list bots: {e}")
            return {
                "success": False,
                "error": str(e),
                "bots": []
            }
    
    def _fallback_start_bot(self, bot_id: int) -> Tuple[bool, str]:
        """Fallback to legacy bot start method."""
        logger.info(f"Using legacy system to start bot {bot_id}")
        
        try:
            success, message = legacy_bot_manager.start_bot_thread(bot_id)
            
            if success:
                logger.info(f"Bot {bot_id} started successfully using legacy system")
            else:
                logger.error(f"Legacy system failed to start bot {bot_id}: {message}")
            
            return success, message
            
        except Exception as e:
            logger.error(f"Exception in legacy system when starting bot {bot_id}: {e}")
            return False, f"Legacy system failed: {str(e)}"
    
    def _fallback_stop_bot(self, bot_id: int) -> Tuple[bool, str]:
        """Fallback to legacy bot stop method."""
        logger.info(f"Using legacy system to stop bot {bot_id}")
        
        try:
            success, message = legacy_bot_manager.stop_bot_thread(bot_id)
            
            if success:
                logger.info(f"Bot {bot_id} stopped successfully using legacy system")
            else:
                logger.error(f"Legacy system failed to stop bot {bot_id}: {message}")
            
            return success, message
            
        except Exception as e:
            logger.error(f"Exception in legacy system when stopping bot {bot_id}: {e}")
            return False, f"Legacy system failed: {str(e)}"
    
    def _get_legacy_bot_status(self, bot_id: int) -> Dict[str, Any]:
        """Get bot status from legacy system."""
        try:
            with legacy_config.BOT_CONFIGS_LOCK:
                if bot_id not in legacy_config.BOT_CONFIGS:
                    return {
                        "success": False,
                        "error": "Bot not found",
                        "status": "not_found"
                    }
                
                bot_data = legacy_config.BOT_CONFIGS[bot_id]
                return {
                    "success": True,
                    "status": bot_data.get("status", "unknown"),
                    "name": bot_data.get("config", {}).get("bot_name", ""),
                    "id": bot_id,
                    "source": "legacy_system"
                }
                
        except Exception as e:
            logger.error(f"Failed to get legacy bot status for {bot_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "error"
            }
    
    def _list_legacy_bots(self) -> Dict[str, Any]:
        """List bots from legacy system."""
        try:
            with legacy_config.BOT_CONFIGS_LOCK:
                bots = []
                for bot_id, bot_data in legacy_config.BOT_CONFIGS.items():
                    config = bot_data.get("config", {})
                    bots.append({
                        "id": bot_id,
                        "name": config.get("bot_name", f"Bot {bot_id}"),
                        "status": bot_data.get("status", "unknown"),
                        "token": config.get("telegram_token", "")[:10] + "..." if config.get("telegram_token") else ""
                    })
                
                return {
                    "success": True,
                    "bots": bots,
                    "total": len(bots),
                    "source": "legacy_system"
                }
                
        except Exception as e:
            logger.error(f"Failed to list legacy bots: {e}")
            return {
                "success": False,
                "error": str(e),
                "bots": []
            }
    
    def _sync_bot_status_to_legacy(self, bot_id: int, status: str):
        """Sync bot status to legacy system."""
        try:
            with legacy_config.BOT_CONFIGS_LOCK:
                if bot_id in legacy_config.BOT_CONFIGS:
                    legacy_config.BOT_CONFIGS[bot_id]["status"] = status
                    logger.debug(f"Synced bot {bot_id} status to legacy system: {status}")
                
        except Exception as e:
            logger.warning(f"Failed to sync bot {bot_id} status to legacy system: {e}")
    
    def enable_new_system(self):
        """Enable the new bot management system."""
        self._use_new_system = True
        logger.info("New bot management system enabled")
    
    def disable_new_system(self):
        """Disable the new bot management system (use legacy only)."""
        self._use_new_system = False
        logger.info("New bot management system disabled, using legacy only")
    
    def enable_fallback(self):
        """Enable fallback to legacy system on failures."""
        self._fallback_enabled = True
        logger.info("Fallback to legacy system enabled")
    
    def disable_fallback(self):
        """Disable fallback to legacy system."""
        self._fallback_enabled = False
        logger.info("Fallback to legacy system disabled")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of both management systems."""
        try:
            # Check new system status
            new_system_status = "operational"
            try:
                test_result = self.use_case.list_bots()
                if not test_result.get("success", False):
                    new_system_status = "degraded"
            except Exception:
                new_system_status = "failed"
            
            # Check legacy system status
            legacy_system_status = "operational"
            try:
                with legacy_config.BOT_CONFIGS_LOCK:
                    len(legacy_config.BOT_CONFIGS)
            except Exception:
                legacy_system_status = "failed"
            
            return {
                "new_system": {
                    "status": new_system_status,
                    "enabled": self._use_new_system
                },
                "legacy_system": {
                    "status": legacy_system_status,
                    "fallback_enabled": self._fallback_enabled
                },
                "unified_system": {
                    "operational": (new_system_status == "operational" or 
                                  (legacy_system_status == "operational" and self._fallback_enabled))
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {
                "error": str(e),
                "unified_system": {"operational": False}
            }
    
    def stop_all_bots(self, timeout: int = 30) -> Dict[str, Any]:
        """
        Stop all bots using the unified system.
        
        Args:
            timeout: Maximum time to wait for all bots to stop
            
        Returns:
            Dict containing operation results
        """
        logger.info(f"Stopping all bots with timeout {timeout}s")
        
        result = {
            "success": True,
            "stopped_bots": 0,
            "failed_bots": 0,
            "errors": []
        }
        
        try:
            # Get list of all bots
            bots_result = self.list_bots()
            
            if not bots_result.get("success", False):
                return {
                    "success": False,
                    "error": "Failed to get bot list",
                    "stopped_bots": 0,
                    "failed_bots": 0
                }
            
            bots = bots_result.get("bots", [])
            
            # Stop each bot
            for bot in bots:
                bot_id = bot.get("id")
                if bot.get("status") == "running":
                    try:
                        success, message = self.stop_bot(bot_id)
                        
                        if success:
                            result["stopped_bots"] += 1
                        else:
                            result["failed_bots"] += 1
                            result["errors"].append(f"Bot {bot_id}: {message}")
                            
                    except Exception as e:
                        result["failed_bots"] += 1
                        result["errors"].append(f"Bot {bot_id}: {str(e)}")
            
            if result["failed_bots"] > 0:
                result["success"] = False
            
            logger.info(
                f"Stopped {result['stopped_bots']} bots, "
                f"{result['failed_bots']} failures"
            )
            
        except Exception as e:
            logger.error(f"Failed to stop all bots: {e}")
            result = {
                "success": False,
                "error": str(e),
                "stopped_bots": 0,
                "failed_bots": 0
            }
        
        return result







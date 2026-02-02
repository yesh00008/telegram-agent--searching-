"""
Notification Handler Module
Sends job alerts via Telegram Bot using python-telegram-bot
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

import requests
from telegram import Bot
from telegram.error import TelegramError

from config import (
    BOT_TOKEN,
    ALERT_CHAT_ID,
    MAX_ALERTS_PER_HOUR,
    ALERT_DELAY_SECONDS,
    ENABLE_RATE_LIMITING
)
from utils import RateLimiter, format_timestamp

logger = logging.getLogger(__name__)


class NotificationHandler:
    """Handles sending job alerts via Telegram bot"""
    
    def __init__(self):
        """Initialize notification handler with bot credentials"""
        self.bot_token = BOT_TOKEN
        self.chat_id = ALERT_CHAT_ID
        self.bot = None
        self.rate_limiter = RateLimiter(max_per_hour=MAX_ALERTS_PER_HOUR)
        self.alert_count = 0
        
        logger.info("NotificationHandler initialized")
    
    async def initialize(self):
        """Initialize the Telegram bot"""
        try:
            self.bot = Bot(token=self.bot_token)
            
            # Test bot connection
            bot_info = await self.bot.get_me()
            logger.info(f"Notification bot connected: @{bot_info.username}")
            
            # Send startup notification
            await self._send_startup_message()
            
        except Exception as e:
            logger.error(f"Failed to initialize notification bot: {e}")
            raise
    
    async def _send_startup_message(self):
        """Send a startup notification to confirm bot is working"""
        startup_msg = (
            "🤖 <b>Job Monitor Bot Started</b>\n\n"
            f"✅ Monitoring active\n"
            f"📅 Started at: {format_timestamp(datetime.now())}\n\n"
            "I'll notify you when relevant job posts are detected!"
        )
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=startup_msg,
                parse_mode='HTML'
            )
            logger.info("Startup notification sent")
        except Exception as e:
            logger.warning(f"Failed to send startup message: {e}")
    
    async def send_alert(self, alert_data: Dict[str, Any]):
        """
        Send a formatted job alert
        
        Args:
            alert_data: Dictionary containing:
                - category: Job category
                - description: Short job description
                - links: List of job links
                - source: Source group/channel name
                - timestamp: Message timestamp
        """
        # Check rate limiting
        if ENABLE_RATE_LIMITING and not self.rate_limiter.can_send():
            logger.warning("Rate limit exceeded, alert dropped")
            return
        
        try:
            # Format the alert message
            message = self._format_alert_message(alert_data)
            
            # Send via Telegram bot
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=False
            )
            
            self.alert_count += 1
            logger.info(f"Alert #{self.alert_count} sent successfully")
            
            # Apply delay to avoid rate limits
            if ALERT_DELAY_SECONDS > 0:
                await asyncio.sleep(ALERT_DELAY_SECONDS)
            
        except TelegramError as e:
            logger.error(f"Telegram error sending alert: {e}")
        except Exception as e:
            logger.error(f"Error sending alert: {e}", exc_info=True)
    
    def _format_alert_message(self, data: Dict[str, Any]) -> str:
        """
        Format job alert as HTML message
        
        Args:
            data: Alert data dictionary
            
        Returns:
            Formatted HTML message string
        """
        category = data.get('category', 'Unknown')
        description = data.get('description', 'No description')
        links = data.get('links', [])
        source = data.get('source', 'Unknown Source')
        timestamp = data.get('timestamp', datetime.now())
        
        # Category emoji mapping
        category_emoji = {
            'AI/ML': '🤖',
            'Cyber Security': '🔒',
            'Full Stack': '💻',
            'Backend': '⚙️',
            'Frontend': '🎨',
            'Data': '📊'
        }
        
        emoji = category_emoji.get(category, '💼')
        
        # Build message
        message = f"{emoji} <b>{category} Job Opening</b>\n\n"
        message += f"📝 <b>Description:</b>\n{description}\n\n"
        
        # Add links
        if links:
            message += "🔗 <b>Application Links:</b>\n"
            for i, link in enumerate(links, 1):
                message += f"{i}. {link}\n"
            message += "\n"
        else:
            message += "ℹ️ No external links found (check source for details)\n\n"
        
        # Add metadata
        message += f"📢 <b>Source:</b> {source}\n"
        message += f"🕐 <b>Posted:</b> {format_timestamp(timestamp)}\n"
        
        return message
    
    async def send_error_notification(self, error_message: str):
        """Send error notification to admin"""
        try:
            msg = f"⚠️ <b>Bot Error</b>\n\n<code>{error_message}</code>"
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=msg,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
    
    async def send_shutdown_message(self):
        """Send shutdown notification"""
        try:
            msg = (
                "🔴 <b>Job Monitor Bot Stopped</b>\n\n"
                f"⏰ Stopped at: {format_timestamp(datetime.now())}\n"
                f"📊 Total alerts sent: {self.alert_count}"
            )
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=msg,
                parse_mode='HTML'
            )
            logger.info("Shutdown notification sent")
        except Exception as e:
            logger.warning(f"Failed to send shutdown message: {e}")


class FallbackNotifier:
    """
    Fallback notification system using direct Bot API
    Used if python-telegram-bot fails
    """
    
    def __init__(self):
        self.bot_token = BOT_TOKEN
        self.chat_id = ALERT_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.alert_count = 0
        
        logger.info("FallbackNotifier initialized")
    
    async def initialize(self):
        """Test bot connection"""
        try:
            response = requests.get(f"{self.base_url}/getMe", timeout=10)
            if response.status_code == 200:
                bot_info = response.json()['result']
                logger.info(f"Fallback bot connected: @{bot_info['username']}")
            else:
                logger.error("Failed to connect fallback bot")
        except Exception as e:
            logger.error(f"Fallback bot initialization error: {e}")
    
    def send_message_sync(self, text: str):
        """Send message using direct API call (synchronous)"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                self.alert_count += 1
                logger.info(f"Fallback alert #{self.alert_count} sent")
                return True
            else:
                logger.error(f"Fallback send failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Fallback send error: {e}")
            return False

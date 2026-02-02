"""
Userbot Message Listener using Telethon
Monitors Telegram groups/channels for new messages
"""

import logging
from typing import Set, Optional
from datetime import datetime

from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat

from config import (
    API_ID,
    API_HASH,
    PHONE_NUMBER,
    SESSION_NAME,
    MONITORED_GROUPS,
    AUTO_RECONNECT,
    RECONNECT_DELAY_SECONDS,
    PROCESS_ONLY_NEW_MESSAGES
)
from filters import JobDetector, LinkExtractor
from utils import DedupManager, format_timestamp

logger = logging.getLogger(__name__)


class TelegramMonitor:
    """Monitors Telegram groups/channels using Telethon userbot"""
    
    def __init__(self, notifier):
        """
        Initialize Telegram monitor
        
        Args:
            notifier: NotificationHandler instance to send alerts
        """
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        self.notifier = notifier
        self.dedup_manager = DedupManager()
        self.monitored_entity_ids: Set[int] = set()
        self.is_running = False
        self.start_time = None
        
        logger.info("TelegramMonitor initialized")
    
    async def start(self):
        """Start the userbot and register event handlers"""
        logger.info("Starting Telegram userbot...")
        
        # Connect and authenticate
        await self.client.start(phone=PHONE_NUMBER)
        
        # Get current user info
        me = await self.client.get_me()
        logger.info(f"Logged in as: {me.first_name} (@{me.username})")
        
        # Store start time for filtering new messages
        self.start_time = datetime.now()
        
        # Get monitored entities
        await self._setup_monitored_entities()
        
        # Register new message handler
        self.client.add_event_handler(
            self._on_new_message,
            events.NewMessage(chats=list(self.monitored_entity_ids) if self.monitored_entity_ids else None)
        )
        
        self.is_running = True
        logger.info("Telegram monitor started successfully")
        logger.info(f"Monitoring {len(self.monitored_entity_ids)} entities")
        
        # Keep the client running
        await self.client.run_until_disconnected()
    
    async def _setup_monitored_entities(self):
        """Setup list of groups/channels to monitor"""
        if MONITORED_GROUPS:
            # Monitor specific groups/channels
            logger.info(f"Setting up {len(MONITORED_GROUPS)} specific monitored groups...")
            
            for group_identifier in MONITORED_GROUPS:
                try:
                    entity = await self.client.get_entity(group_identifier)
                    self.monitored_entity_ids.add(entity.id)
                    logger.info(f"Added to monitor: {getattr(entity, 'title', getattr(entity, 'username', 'Unknown'))}")
                except Exception as e:
                    logger.error(f"Failed to add {group_identifier}: {e}")
        else:
            # Monitor all groups/channels where userbot is a member
            logger.info("Setting up monitoring for all joined groups/channels...")
            
            async for dialog in self.client.iter_dialogs():
                # Only monitor channels and groups (not private chats)
                if isinstance(dialog.entity, (Channel, Chat)):
                    self.monitored_entity_ids.add(dialog.entity.id)
                    logger.debug(f"Added to monitor: {dialog.title}")
            
            logger.info(f"Monitoring all {len(self.monitored_entity_ids)} groups/channels")
    
    async def _on_new_message(self, event):
        """
        Event handler for new messages
        Filters, processes, and sends alerts for job posts
        """
        try:
            message = event.message
            
            # Skip messages from before bot started (if configured)
            if PROCESS_ONLY_NEW_MESSAGES and self.start_time:
                if message.date.replace(tzinfo=None) < self.start_time:
                    return
            
            # Get source info
            chat = await event.get_chat()
            source_name = getattr(chat, 'title', getattr(chat, 'username', 'Unknown'))
            
            logger.debug(f"Processing message from {source_name}")
            
            # Check if message is a job post
            is_job, category = JobDetector.is_job_post(message)
            
            if not is_job:
                return
            
            # Check for duplicates
            if self.dedup_manager.is_duplicate(message.text):
                logger.info(f"Duplicate job post ignored from {source_name}")
                return
            
            logger.info(f"New job detected: {category} from {source_name}")
            
            # Extract job details
            description = JobDetector.extract_description(message.text)
            links = LinkExtractor.extract_links(message.text)
            
            # Check for duplicate links
            unique_links = self.dedup_manager.filter_duplicate_links(links)
            
            if not unique_links and links:
                logger.info("All links were duplicates, skipping alert")
                return
            
            # Create alert data
            alert_data = {
                'category': category,
                'description': description,
                'links': unique_links,
                'source': source_name,
                'timestamp': message.date
            }
            
            # Send notification
            await self.notifier.send_alert(alert_data)
            
            logger.info(f"Alert sent for {category} job from {source_name}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
    
    async def stop(self):
        """Stop the userbot gracefully"""
        logger.info("Stopping Telegram monitor...")
        self.is_running = False
        await self.client.disconnect()
        logger.info("Telegram monitor stopped")

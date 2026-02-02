"""
Utility Functions and Helper Classes
Includes deduplication, rate limiting, and formatting utilities
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Set, List, Optional
from collections import deque

from config import (
    DEDUP_WINDOW_SECONDS,
    MAX_CACHE_SIZE,
    ENABLE_DEDUPLICATION
)

logger = logging.getLogger(__name__)


class DedupManager:
    """
    Manages message and link deduplication
    Uses hash-based caching with time-based expiration
    """
    
    def __init__(self):
        """Initialize deduplication manager"""
        self.message_hashes: deque = deque(maxlen=MAX_CACHE_SIZE)
        self.message_timestamps: deque = deque(maxlen=MAX_CACHE_SIZE)
        self.link_hashes: Set[str] = set()
        self.link_timestamps: dict = {}
        
        logger.info("DedupManager initialized")
    
    def _hash_text(self, text: str) -> str:
        """Generate hash from text content"""
        # Normalize text before hashing
        normalized = text.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def is_duplicate(self, text: str) -> bool:
        """
        Check if message is a duplicate
        
        Args:
            text: Message text to check
            
        Returns:
            True if duplicate, False otherwise
        """
        if not ENABLE_DEDUPLICATION:
            return False
        
        text_hash = self._hash_text(text)
        current_time = datetime.now()
        
        # Clean old entries
        self._cleanup_old_messages(current_time)
        
        # Check if hash exists in recent messages
        if text_hash in self.message_hashes:
            logger.debug(f"Duplicate message detected: {text_hash[:8]}...")
            return True
        
        # Add new hash
        self.message_hashes.append(text_hash)
        self.message_timestamps.append(current_time)
        
        return False
    
    def _cleanup_old_messages(self, current_time: datetime):
        """Remove messages older than dedup window"""
        cutoff_time = current_time - timedelta(seconds=DEDUP_WINDOW_SECONDS)
        
        # Remove old entries from the front of the deque
        while self.message_timestamps and self.message_timestamps[0] < cutoff_time:
            self.message_timestamps.popleft()
            self.message_hashes.popleft()
    
    def is_duplicate_link(self, link: str) -> bool:
        """
        Check if link has been seen before
        
        Args:
            link: URL to check
            
        Returns:
            True if duplicate, False otherwise
        """
        if not ENABLE_DEDUPLICATION:
            return False
        
        link_hash = self._hash_text(link)
        current_time = datetime.now()
        
        # Clean old link hashes
        self._cleanup_old_links(current_time)
        
        if link_hash in self.link_hashes:
            logger.debug(f"Duplicate link detected: {link[:50]}...")
            return True
        
        # Add new link
        self.link_hashes.add(link_hash)
        self.link_timestamps[link_hash] = current_time
        
        return False
    
    def filter_duplicate_links(self, links: List[str]) -> List[str]:
        """
        Filter out duplicate links from a list
        
        Args:
            links: List of URLs
            
        Returns:
            List of unique URLs
        """
        unique_links = []
        
        for link in links:
            if not self.is_duplicate_link(link):
                unique_links.append(link)
        
        return unique_links
    
    def _cleanup_old_links(self, current_time: datetime):
        """Remove links older than dedup window"""
        cutoff_time = current_time - timedelta(seconds=DEDUP_WINDOW_SECONDS)
        
        # Find and remove expired links
        expired_hashes = [
            h for h, t in self.link_timestamps.items()
            if t < cutoff_time
        ]
        
        for h in expired_hashes:
            self.link_hashes.discard(h)
            self.link_timestamps.pop(h, None)
    
    def get_stats(self) -> dict:
        """Get deduplication statistics"""
        return {
            'cached_messages': len(self.message_hashes),
            'cached_links': len(self.link_hashes),
            'max_cache_size': MAX_CACHE_SIZE,
            'dedup_window_seconds': DEDUP_WINDOW_SECONDS
        }


class RateLimiter:
    """
    Rate limiter to prevent exceeding Telegram rate limits
    Tracks messages sent per hour
    """
    
    def __init__(self, max_per_hour: int):
        """
        Initialize rate limiter
        
        Args:
            max_per_hour: Maximum allowed messages per hour
        """
        self.max_per_hour = max_per_hour
        self.send_timestamps: deque = deque()
        
        logger.info(f"RateLimiter initialized: {max_per_hour} msgs/hour")
    
    def can_send(self) -> bool:
        """
        Check if we can send a message without exceeding rate limit
        
        Returns:
            True if allowed, False if rate limit exceeded
        """
        current_time = datetime.now()
        one_hour_ago = current_time - timedelta(hours=1)
        
        # Remove timestamps older than 1 hour
        while self.send_timestamps and self.send_timestamps[0] < one_hour_ago:
            self.send_timestamps.popleft()
        
        # Check if under limit
        if len(self.send_timestamps) < self.max_per_hour:
            self.send_timestamps.append(current_time)
            return True
        
        logger.warning(f"Rate limit exceeded: {len(self.send_timestamps)}/{self.max_per_hour}")
        return False
    
    def get_stats(self) -> dict:
        """Get rate limiter statistics"""
        current_time = datetime.now()
        one_hour_ago = current_time - timedelta(hours=1)
        
        # Count messages in last hour
        recent_count = sum(1 for ts in self.send_timestamps if ts > one_hour_ago)
        
        return {
            'sent_last_hour': recent_count,
            'max_per_hour': self.max_per_hour,
            'remaining': max(0, self.max_per_hour - recent_count)
        }


def format_timestamp(dt: datetime) -> str:
    """
    Format datetime as readable string
    
    Args:
        dt: Datetime object
        
    Returns:
        Formatted string like "2026-02-02 14:30:45"
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def setup_logging(log_level: str = 'INFO', log_file: Optional[str] = None):
    """
    Configure logging for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
    """
    from config import LOG_FORMAT
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),  # Console output
        ]
    )
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logging.getLogger().addHandler(file_handler)
    
    # Reduce noise from external libraries
    logging.getLogger('telethon').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    logger.info(f"Logging configured: level={log_level}")


def validate_config():
    """
    Validate configuration values
    Raises ValueError if critical config is missing
    """
    from config import API_ID, API_HASH, BOT_TOKEN, ALERT_CHAT_ID
    
    errors = []
    
    # Check API credentials
    if API_ID == 12345678 or not isinstance(API_ID, int):
        errors.append("API_ID not configured properly")
    
    if API_HASH == 'your_api_hash_here' or not API_HASH:
        errors.append("API_HASH not configured")
    
    if BOT_TOKEN == 'your_bot_token_here' or not BOT_TOKEN:
        errors.append("BOT_TOKEN not configured")
    
    if ALERT_CHAT_ID == 123456789 or not isinstance(ALERT_CHAT_ID, int):
        errors.append("ALERT_CHAT_ID not configured")
    
    if errors:
        error_msg = "Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("Configuration validated successfully")


def get_system_stats(dedup_manager: DedupManager, rate_limiter: RateLimiter) -> dict:
    """
    Get comprehensive system statistics
    
    Args:
        dedup_manager: DedupManager instance
        rate_limiter: RateLimiter instance
        
    Returns:
        Dictionary of system stats
    """
    return {
        'deduplication': dedup_manager.get_stats(),
        'rate_limiting': rate_limiter.get_stats(),
        'timestamp': format_timestamp(datetime.now())
    }

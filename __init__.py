"""
Package Initialization
Telegram Job Monitoring Bot
"""

__version__ = "1.0.0"
__author__ = "Production Ready System"
__description__ = "Telegram userbot for monitoring job posts in tech domains"

# Make key classes available at package level
from .monitor import TelegramMonitor
from .notifier import NotificationHandler
from .filters import JobDetector, MessageFilter, LinkExtractor
from .utils import DedupManager, RateLimiter

__all__ = [
    'TelegramMonitor',
    'NotificationHandler',
    'JobDetector',
    'MessageFilter',
    'LinkExtractor',
    'DedupManager',
    'RateLimiter'
]

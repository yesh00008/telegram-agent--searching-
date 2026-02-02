"""
Main Entry Point for Telegram Job Monitoring Bot
Production-ready system with auto-reconnect and error handling
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime

from monitor import TelegramMonitor
from notifier import NotificationHandler
from utils import setup_logging, validate_config, format_timestamp
from config import LOG_LEVEL, AUTO_RECONNECT, RECONNECT_DELAY_SECONDS, MAX_RECONNECT_ATTEMPTS

logger = logging.getLogger(__name__)


class JobMonitorBot:
    """Main application orchestrator"""
    
    def __init__(self):
        """Initialize the job monitor bot"""
        self.notifier = None
        self.monitor = None
        self.is_running = False
        self.reconnect_attempts = 0
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("JobMonitorBot initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals (Ctrl+C, etc.)"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.is_running = False
        
        # Schedule shutdown coroutine
        if asyncio.get_event_loop().is_running():
            asyncio.create_task(self.shutdown())
    
    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing components...")
        
        # Validate configuration first
        validate_config()
        
        # Initialize notification handler
        self.notifier = NotificationHandler()
        await self.notifier.initialize()
        
        # Initialize monitor with notifier
        self.monitor = TelegramMonitor(self.notifier)
        
        logger.info("All components initialized successfully")
    
    async def start(self):
        """Start the bot with auto-reconnect capability"""
        self.is_running = True
        
        logger.info("=" * 60)
        logger.info("TELEGRAM JOB MONITORING BOT")
        logger.info("=" * 60)
        logger.info(f"Started at: {format_timestamp(datetime.now())}")
        logger.info("=" * 60)
        
        while self.is_running:
            try:
                # Initialize components
                await self.initialize()
                
                # Reset reconnect counter on successful connection
                self.reconnect_attempts = 0
                
                # Start monitoring (this blocks until disconnected)
                logger.info("Starting message monitoring...")
                await self.monitor.start()
                
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                break
                
            except Exception as e:
                logger.error(f"Fatal error in main loop: {e}", exc_info=True)
                
                # Send error notification if notifier is available
                if self.notifier:
                    try:
                        await self.notifier.send_error_notification(str(e))
                    except:
                        pass
                
                # Handle reconnection
                if AUTO_RECONNECT and self.is_running:
                    self.reconnect_attempts += 1
                    
                    if self.reconnect_attempts <= MAX_RECONNECT_ATTEMPTS:
                        logger.info(
                            f"Reconnection attempt {self.reconnect_attempts}/{MAX_RECONNECT_ATTEMPTS} "
                            f"in {RECONNECT_DELAY_SECONDS} seconds..."
                        )
                        await asyncio.sleep(RECONNECT_DELAY_SECONDS)
                    else:
                        logger.error("Maximum reconnection attempts reached, stopping bot")
                        break
                else:
                    break
        
        # Graceful shutdown
        await self.shutdown()
    
    async def shutdown(self):
        """Shutdown all components gracefully"""
        logger.info("Shutting down bot...")
        
        try:
            # Stop monitor
            if self.monitor:
                await self.monitor.stop()
            
            # Send shutdown notification
            if self.notifier:
                await self.notifier.send_shutdown_message()
            
            logger.info("=" * 60)
            logger.info("Bot shutdown complete")
            logger.info(f"Stopped at: {format_timestamp(datetime.now())}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        finally:
            self.is_running = False


async def main():
    """Main entry point"""
    # Setup logging
    setup_logging(log_level=LOG_LEVEL)
    
    # Print startup banner
    print("\n" + "=" * 60)
    print("  TELEGRAM JOB MONITORING BOT - Production Ready")
    print("=" * 60)
    print(f"  Version: 1.0.0")
    print(f"  Started: {format_timestamp(datetime.now())}")
    print("=" * 60 + "\n")
    
    # Create and start bot
    bot = JobMonitorBot()
    
    try:
        await bot.start()
    except Exception as e:
        logger.critical(f"Critical error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    """Run the bot"""
    try:
        # Run the async main function
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nBot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        sys.exit(1)

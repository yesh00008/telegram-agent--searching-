"""
Interactive Telegram Job Monitor with Button Controls
Control monitoring through Telegram buttons
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telethon import TelegramClient, events
from telethon.tl.types import Channel

from config import API_ID, API_HASH, PHONE_NUMBER, SESSION_NAME, BOT_TOKEN
from filters import JobDetector, LinkExtractor, MessageFilter
from utils import setup_logging, DedupManager

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Jobs database file
JOBS_DB_FILE = Path(__file__).parent / "jobs_database.json"

# Channels to monitor
CHANNELS = [
    'getjobss',
    'jobs_and_internships_updates',
    'work4freshers',
    'gocareers',
    'AJ_tech_career',
    'PLACEMENTLELO'
]


class JobMonitorBot:
    """Interactive bot with button controls"""
    
    def __init__(self):
        self.monitoring = False
        self.telethon_client = None
        self.bot_app = None
        self.jobs_db: List[Dict] = []
        self.dedup_manager = DedupManager()
        self.admin_chat_id = None
        
        # Load existing jobs
        self.load_jobs_db()
    
    def load_jobs_db(self):
        """Load jobs from database file"""
        if JOBS_DB_FILE.exists():
            try:
                with open(JOBS_DB_FILE, 'r', encoding='utf-8') as f:
                    self.jobs_db = json.load(f)
                logger.info(f"Loaded {len(self.jobs_db)} jobs from database")
            except Exception as e:
                logger.error(f"Error loading jobs database: {e}")
                self.jobs_db = []
        else:
            self.jobs_db = []
    
    def save_jobs_db(self):
        """Save jobs to database file"""
        try:
            with open(JOBS_DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.jobs_db, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.jobs_db)} jobs to database")
        except Exception as e:
            logger.error(f"Error saving jobs database: {e}")
    
    def add_job(self, job_data: Dict):
        """Add job to database"""
        # Add timestamp if not present
        if 'saved_at' not in job_data:
            job_data['saved_at'] = datetime.now().isoformat()
        
        self.jobs_db.append(job_data)
        self.save_jobs_db()
    
    def get_main_keyboard(self) -> InlineKeyboardMarkup:
        """Create main menu keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("📋 Jobs List", callback_data='jobs_list'),
                InlineKeyboardButton("📊 Statistics", callback_data='stats')
            ],
            [
                InlineKeyboardButton(
                    "🟢 Start Monitor" if not self.monitoring else "🔴 Stop Monitor",
                    callback_data='toggle_monitor'
                )
            ],
            [
                InlineKeyboardButton("🔍 Scan Last 3 Days", callback_data='scan_history'),
                InlineKeyboardButton("🗑️ Clear Jobs", callback_data='clear_jobs')
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        self.admin_chat_id = update.effective_chat.id
        
        welcome_text = (
            "🤖 *Telegram Job Monitor Bot*\n\n"
            "🎓 *Filter:* 2026 Passouts & Freshers Only\n"
            f"📺 *Monitoring {len(CHANNELS)} channels*\n\n"
            "Use the buttons below to control the bot:"
        )
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=self.get_main_keyboard(),
            parse_mode='Markdown'
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button clicks"""
        query = update.callback_query
        await query.answer()
        
        action = query.data
        
        if action == 'toggle_monitor':
            await self.toggle_monitoring(query)
        
        elif action == 'jobs_list':
            await self.show_jobs_list(query)
        
        elif action == 'stats':
            await self.show_statistics(query)
        
        elif action == 'scan_history':
            await self.scan_history(query)
        
        elif action == 'clear_jobs':
            await self.clear_jobs(query)
        
        elif action == 'back_to_menu':
            await query.edit_message_text(
                "🤖 *Main Menu*\n\nChoose an option:",
                reply_markup=self.get_main_keyboard(),
                parse_mode='Markdown'
            )
    
    async def toggle_monitoring(self, query):
        """Start or stop monitoring"""
        if not self.monitoring:
            # Start monitoring
            await query.edit_message_text("🟢 *Starting Monitor...*", parse_mode='Markdown')
            
            try:
                # Start Telethon client
                if not self.telethon_client:
                    self.telethon_client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
                    await self.telethon_client.start(phone=PHONE_NUMBER)
                    
                    # Register event handler
                    @self.telethon_client.on(events.NewMessage(chats=CHANNELS))
                    async def message_handler(event):
                        await self.process_message(event.message, event)
                
                if not self.telethon_client.is_connected():
                    await self.telethon_client.connect()
                
                self.monitoring = True
                
                await query.edit_message_text(
                    f"✅ *Monitor Started!*\n\n"
                    f"📺 Monitoring {len(CHANNELS)} channels\n"
                    f"🎓 Filtering: 2026 passouts & freshers only\n"
                    f"📊 Jobs collected: {len(self.jobs_db)}\n\n"
                    f"You'll receive alerts here for new jobs!",
                    reply_markup=self.get_main_keyboard(),
                    parse_mode='Markdown'
                )
                
            except Exception as e:
                logger.error(f"Error starting monitor: {e}")
                await query.edit_message_text(
                    f"❌ *Error starting monitor:*\n{str(e)}\n\n"
                    f"Make sure you've updated phone number in .env",
                    reply_markup=self.get_main_keyboard(),
                    parse_mode='Markdown'
                )
                self.monitoring = False
        
        else:
            # Stop monitoring
            self.monitoring = False
            
            if self.telethon_client and self.telethon_client.is_connected():
                await self.telethon_client.disconnect()
            
            await query.edit_message_text(
                "🔴 *Monitor Stopped*\n\n"
                f"📊 Total jobs collected: {len(self.jobs_db)}",
                reply_markup=self.get_main_keyboard(),
                parse_mode='Markdown'
            )
    
    async def process_message(self, message, event):
        """Process incoming message from monitored channels"""
        try:
            # Check if it's a job post
            is_job, category = JobDetector.is_job_post(message)
            if not is_job:
                return
            
            # Check for duplicates
            if self.dedup_manager.is_duplicate(message.text):
                logger.info("Duplicate job ignored")
                return
            
            # Get channel info
            chat = await event.get_chat()
            source = getattr(chat, 'title', getattr(chat, 'username', 'Unknown'))
            
            # Extract details
            description = JobDetector.extract_description(message.text)
            links = LinkExtractor.extract_links(message.text)
            
            # Create job data
            job_data = {
                'category': category,
                'description': description,
                'full_text': message.text[:500],
                'links': links,
                'source': source,
                'date': message.date.strftime('%Y-%m-%d %H:%M'),
                'message_link': f"https://t.me/{chat.username}/{message.id}" if chat.username else None
            }
            
            # Save to database
            self.add_job(job_data)
            
            # Send alert to admin
            if self.admin_chat_id:
                alert_text = self.format_job_alert(job_data)
                await self.bot_app.bot.send_message(
                    chat_id=self.admin_chat_id,
                    text=alert_text,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
            
            logger.info(f"New job saved: {category} from {source}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def format_job_alert(self, job: Dict) -> str:
        """Format job as alert message"""
        emoji_map = {
            'AI/ML': '🤖',
            'Cyber Security': '🔒',
            'Full Stack': '💻',
            'Backend': '⚙️',
            'Frontend': '🎨',
            'Data': '📊'
        }
        
        emoji = emoji_map.get(job['category'], '💼')
        
        text = f"{emoji} <b>{job['category']} Job Alert!</b>\n\n"
        text += f"📝 {job['description']}\n\n"
        text += f"📺 Source: {job['source']}\n"
        text += f"📅 Posted: {job['date']}\n"
        
        if job.get('links'):
            text += f"\n🔗 <b>Apply Links:</b>\n"
            for link in job['links'][:3]:
                text += f"   • {link}\n"
        
        if job.get('message_link'):
            text += f"\n📱 <a href=\"{job['message_link']}\">View Original Message</a>"
        
        return text
    
    async def show_jobs_list(self, query):
        """Show list of collected jobs"""
        if not self.jobs_db:
            await query.edit_message_text(
                "📋 *Jobs List*\n\n❌ No jobs collected yet!\n\n"
                "Start monitoring or scan history to find jobs.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Back", callback_data='back_to_menu')
                ]]),
                parse_mode='Markdown'
            )
            return
        
        # Get recent jobs (last 20)
        recent_jobs = self.jobs_db[-20:]
        
        text = f"📋 *Jobs List* ({len(self.jobs_db)} total)\n\n"
        text += "*Last 20 Jobs:*\n\n"
        
        for idx, job in enumerate(reversed(recent_jobs), 1):
            text += f"{idx}. [{job['category']}] - {job['date']}\n"
            text += f"   {job['description'][:80]}...\n"
            if job.get('message_link'):
                text += f"   [View]({job['message_link']})\n"
            text += "\n"
        
        keyboard = [
            [InlineKeyboardButton("📊 By Category", callback_data='stats')],
            [InlineKeyboardButton("◀️ Back", callback_data='back_to_menu')]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    
    async def show_statistics(self, query):
        """Show statistics"""
        if not self.jobs_db:
            await query.edit_message_text(
                "📊 *Statistics*\n\n❌ No data yet!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Back", callback_data='back_to_menu')
                ]]),
                parse_mode='Markdown'
            )
            return
        
        # Count by category
        by_category = {}
        by_source = {}
        
        for job in self.jobs_db:
            cat = job['category']
            src = job['source']
            by_category[cat] = by_category.get(cat, 0) + 1
            by_source[src] = by_source.get(src, 0) + 1
        
        text = f"📊 *Statistics*\n\n"
        text += f"📋 Total Jobs: {len(self.jobs_db)}\n\n"
        
        text += "*By Category:*\n"
        for cat, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
            text += f"   • {cat}: {count}\n"
        
        text += f"\n*By Source:*\n"
        for src, count in sorted(by_source.items(), key=lambda x: x[1], reverse=True):
            text += f"   • {src}: {count}\n"
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Back", callback_data='back_to_menu')
            ]]),
            parse_mode='Markdown'
        )
    
    async def scan_history(self, query):
        """Scan last 3 days of messages"""
        await query.edit_message_text(
            "🔍 *Scanning History...*\n\nThis may take a few minutes...",
            parse_mode='Markdown'
        )
        
        try:
            # Connect Telethon if not connected
            if not self.telethon_client:
                self.telethon_client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
                await self.telethon_client.start(phone=PHONE_NUMBER)
            
            if not self.telethon_client.is_connected():
                await self.telethon_client.connect()
            
            # Scan each channel
            date_limit = datetime.now() - timedelta(days=3)
            total_found = 0
            
            for channel in CHANNELS:
                try:
                    entity = await self.telethon_client.get_entity(channel)
                    count = 0
                    
                    async for message in self.telethon_client.iter_messages(entity, limit=500):
                        if message.date.replace(tzinfo=None) < date_limit:
                            break
                        
                        if not MessageFilter.is_valid_message(message):
                            continue
                        
                        is_job, category = JobDetector.is_job_post(message)
                        if not is_job:
                            continue
                        
                        if self.dedup_manager.is_duplicate(message.text):
                            continue
                        
                        # Save job
                        description = JobDetector.extract_description(message.text)
                        links = LinkExtractor.extract_links(message.text)
                        
                        job_data = {
                            'category': category,
                            'description': description,
                            'full_text': message.text[:500],
                            'links': links,
                            'source': getattr(entity, 'title', channel),
                            'date': message.date.strftime('%Y-%m-%d %H:%M'),
                            'message_link': f"https://t.me/{channel}/{message.id}"
                        }
                        
                        self.add_job(job_data)
                        count += 1
                    
                    total_found += count
                    logger.info(f"Scanned {channel}: {count} jobs found")
                    
                except Exception as e:
                    logger.error(f"Error scanning {channel}: {e}")
            
            await query.edit_message_text(
                f"✅ *Scan Complete!*\n\n"
                f"📋 Found {total_found} new jobs\n"
                f"💾 Total in database: {len(self.jobs_db)}",
                reply_markup=self.get_main_keyboard(),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in scan_history: {e}")
            await query.edit_message_text(
                f"❌ *Scan failed:*\n{str(e)}",
                reply_markup=self.get_main_keyboard(),
                parse_mode='Markdown'
            )
    
    async def clear_jobs(self, query):
        """Clear jobs database"""
        self.jobs_db = []
        self.save_jobs_db()
        
        await query.edit_message_text(
            "🗑️ *Jobs database cleared!*",
            reply_markup=self.get_main_keyboard(),
            parse_mode='Markdown'
        )
    
    async def run(self):
        """Run the bot"""
        # Create bot application
        self.bot_app = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        self.bot_app.add_handler(CommandHandler("start", self.start_command))
        self.bot_app.add_handler(CallbackQueryHandler(self.button_callback))
        
        logger.info("Interactive bot starting...")
        print("\n" + "="*60)
        print("🤖 INTERACTIVE JOB MONITOR BOT")
        print("="*60)
        print("✅ Bot is running!")
        print("📱 Open Telegram and send /start to your bot")
        print("🔘 Use buttons to control monitoring")
        print("="*60 + "\n")
        
        # Initialize and run bot
        async with self.bot_app:
            await self.bot_app.initialize()
            await self.bot_app.start()
            await self.bot_app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
            
            # Keep running
            try:
                await asyncio.Event().wait()
            except (KeyboardInterrupt, SystemExit):
                logger.info("Shutting down...")
            finally:
                await self.bot_app.updater.stop()
                await self.bot_app.stop()
                await self.bot_app.shutdown()


async def main():
    """Main entry point"""
    bot = JobMonitorBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ Bot stopped!")

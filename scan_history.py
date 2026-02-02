"""
Historical Message Scanner - Scan last 3 days for 2026 passout/fresher jobs
"""

import asyncio
import logging
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.tl.types import Channel

from config import API_ID, API_HASH, PHONE_NUMBER, SESSION_NAME
from filters import JobDetector, LinkExtractor, MessageFilter
from utils import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Channels to scan
CHANNELS = [
    'getjobss',
    'jobs_and_internships_updates',
    'work4freshers',
    'gocareers',
    'AJ_tech_career',
    'PLACEMENTLELO'
]

# Filter for 2026 passouts and freshers only
PASSOUT_YEAR = 2026
DAYS_TO_SCAN = 3


def is_fresher_job(text: str) -> bool:
    """Check if job is EXPLICITLY for 2026 passouts or freshers - STRICT FILTER"""
    text_lower = text.lower()
    import re
    
    # First, reject if experience > 0 is required
    experience_patterns = [
        r'(\d+)\+?\s*(year|yr|yrs|years)\s*(of)?\s*experience',
        r'experience\s*:\s*(\d+)',
        r'exp\s*:\s*(\d+)',
        r'(\d+)-(\d+)\s*(year|yr|yrs|years)',
        r'minimum\s*(\d+)\s*(year|yr|yrs|years)'
    ]
    
    for pattern in experience_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            for match in matches:
                if isinstance(match, tuple):
                    exp_value = match[0] if match[0].isdigit() else '0'
                else:
                    exp_value = match if match.isdigit() else '0'
                
                if int(exp_value) > 0:
                    logger.debug(f"Rejected: Requires {exp_value}+ years experience")
                    return False
    
    # Check for EXPLICIT 2026 passout mentions
    passout_2026_patterns = [
        '2026 passout', '2026 pass out', '2026 graduate', '2026 batch',
        'passout 2026', 'batch 2026', 'graduating 2026', '2026 passing',
        'batch of 2026', '2026 graduation', 'class of 2026'
    ]
    
    for pattern in passout_2026_patterns:
        if pattern in text_lower:
            logger.info(f"✓ Found 2026 passout: {pattern}")
            return True
    
    # Check for EXPLICIT fresher/0 experience keywords
    fresher_keywords = [
        'fresher', 'freshers', '0 experience', 'zero experience',
        'no experience', 'no experience required', 'no prior experience',
        'entry level', 'entry-level', 'trainee', 'fresher job',
        'graduate trainee', 'campus hire', 'campus hiring',
        'fresh graduate', 'recent graduate'
    ]
    
    for keyword in fresher_keywords:
        if keyword in text_lower:
            logger.info(f"✓ Found fresher keyword: {keyword}")
            return True
    
    # STRICT: If no 2026 or fresher mention, REJECT
    logger.debug("Rejected: No explicit 2026 or fresher mention")
    return False


async def scan_channel_history(client: TelegramClient, channel_username: str):
    """Scan last 3 days of messages from a channel"""
    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"Scanning: {channel_username}")
        logger.info(f"{'='*60}")
        
        # Get channel entity
        entity = await client.get_entity(channel_username)
        
        # Calculate date limit (3 days ago)
        date_limit = datetime.now() - timedelta(days=DAYS_TO_SCAN)
        
        found_jobs = []
        message_count = 0
        
        # Iterate through messages
        async for message in client.iter_messages(entity, limit=500):
            message_count += 1
            
            # Stop if message is older than 3 days
            if message.date.replace(tzinfo=None) < date_limit:
                break
            
            # Check if valid message
            if not MessageFilter.is_valid_message(message):
                continue
            
            # Check if it's a job post
            is_job, category = JobDetector.is_job_post(message)
            if not is_job:
                continue
            
            # Check if it's for freshers/2026 passouts
            if not is_fresher_job(message.text):
                continue
            
            # Extract details
            description = JobDetector.extract_description(message.text)
            links = LinkExtractor.extract_links(message.text)
            
            job_data = {
                'category': category,
                'description': description,
                'links': links,
                'date': message.date.strftime('%Y-%m-%d %H:%M'),
                'message_link': f"https://t.me/{channel_username}/{message.id}"
            }
            
            found_jobs.append(job_data)
        
        logger.info(f"Scanned {message_count} messages, found {len(found_jobs)} matching jobs")
        
        # Print results
        if found_jobs:
            print(f"\n\n{'='*80}")
            print(f"📋 FOUND {len(found_jobs)} JOBS FOR 2026 PASSOUTS/FRESHERS in {channel_username}")
            print(f"{'='*80}\n")
            
            for idx, job in enumerate(found_jobs, 1):
                print(f"\n{idx}. [{job['category']}] - {job['date']}")
                print(f"   {job['description'][:150]}...")
                if job['links']:
                    print(f"   🔗 Links: {', '.join(job['links'][:3])}")
                print(f"   📱 Message: {job['message_link']}")
                print("-" * 80)
        else:
            print(f"\n❌ No matching jobs found in {channel_username}")
        
        return found_jobs
        
    except Exception as e:
        logger.error(f"Error scanning {channel_username}: {e}")
        return []


async def main():
    """Main scanner function"""
    print("\n" + "="*80)
    print("🔍 TELEGRAM JOB SCANNER - 2026 PASSOUTS & FRESHERS ONLY")
    print("="*80)
    print(f"📅 Scanning last {DAYS_TO_SCAN} days")
    print(f"🎓 Filtering: 2026 passouts, freshers, 0 experience only")
    print(f"📺 Channels: {', '.join(CHANNELS)}")
    print("="*80 + "\n")
    
    # Create client
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        # Connect
        await client.start(phone=PHONE_NUMBER)
        
        # Get user info
        me = await client.get_me()
        logger.info(f"Logged in as: {me.first_name} (@{me.username})")
        
        # Scan all channels
        all_jobs = []
        for channel in CHANNELS:
            jobs = await scan_channel_history(client, channel)
            all_jobs.extend(jobs)
            await asyncio.sleep(2)  # Rate limiting
        
        # Final summary
        print("\n\n" + "="*80)
        print(f"✅ SCAN COMPLETE")
        print("="*80)
        print(f"Total jobs found: {len(all_jobs)}")
        print(f"Channels scanned: {len(CHANNELS)}")
        print(f"Time period: Last {DAYS_TO_SCAN} days")
        print("="*80 + "\n")
        
        # Group by category
        by_category = {}
        for job in all_jobs:
            cat = job['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(job)
        
        if by_category:
            print("\n📊 JOBS BY CATEGORY:")
            for category, jobs in sorted(by_category.items(), key=lambda x: len(x[1]), reverse=True):
                print(f"   {category}: {len(jobs)} jobs")
        
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
    finally:
        await client.disconnect()
        logger.info("Scanner stopped")


if __name__ == '__main__':
    asyncio.run(main())

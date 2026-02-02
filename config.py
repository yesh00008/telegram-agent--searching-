"""
Configuration Management for Telegram Job Monitoring Bot
All sensitive credentials and settings stored here
"""

import os
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ==================== TELEGRAM CREDENTIALS ====================
# Userbot credentials (get from https://my.telegram.org)
API_ID = int(os.getenv('TELEGRAM_API_ID', '12345678'))  # Replace with your API ID
API_HASH = os.getenv('TELEGRAM_API_HASH', 'your_api_hash_here')  # Replace with your API hash
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE', '+1234567890')  # Your phone number with country code

# Bot credentials (create via @BotFather)
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your_bot_token_here')  # Replace with your bot token
ALERT_CHAT_ID = int(os.getenv('ALERT_CHAT_ID', '123456789'))  # Chat ID to receive alerts (can be user ID or group chat ID)

# Session file for Telethon
SESSION_NAME = 'job_monitor_session'

# ==================== MONITORING SETTINGS ====================
# Groups and channels to monitor (leave empty to monitor all joined groups/channels)
# Format: ['@channelname', 'Group Name', -1001234567890]
MONITORED_GROUPS: List[str] = [
    'getjobss',
    'jobs_and_internships_updates',
    'work4freshers',
    'gocareers',
    'AJ_tech_career',
    'PLACEMENTLELO'
]

# ==================== JOB CATEGORIES & KEYWORDS ====================
# Define job categories with their specific keywords
JOB_CATEGORIES: Dict[str, List[str]] = {
    'AI/ML': [
        'machine learning', 'ml engineer', 'ai engineer', 'data scientist',
        'deep learning', 'nlp', 'computer vision', 'artificial intelligence',
        'pytorch', 'tensorflow', 'keras', 'mlops', 'neural network',
        'llm', 'generative ai', 'chatgpt', 'transformers'
    ],
    'Cyber Security': [
        'security engineer', 'cybersecurity', 'penetration test', 'pen tester',
        'security analyst', 'infosec', 'information security', 'soc analyst',
        'threat intelligence', 'vulnerability', 'ethical hacker', 'cissp',
        'security operations', 'incident response', 'malware analyst'
    ],
    'Full Stack': [
        'full stack', 'fullstack', 'mern', 'mean stack', 'full-stack developer',
        'react node', 'angular node', 'vue node', 'django react', 'flask react'
    ],
    'Backend': [
        'backend', 'back-end', 'node.js', 'django', 'flask', 'fastapi',
        'spring boot', 'golang', 'java backend', 'python backend',
        'api development', 'microservices', 'rest api', 'graphql',
        'express.js', 'nest.js', '.net core', 'ruby on rails'
    ],
    'Frontend': [
        'frontend', 'front-end', 'react', 'angular', 'vue.js', 'svelte',
        'javascript developer', 'typescript', 'next.js', 'nuxt.js',
        'ui developer', 'web developer', 'html css', 'tailwind', 'bootstrap'
    ],
    'Data': [
        'data analyst', 'data engineer', 'data scientist', 'business analyst',
        'analytics engineer', 'bi developer', 'tableau', 'power bi',
        'sql developer', 'etl developer', 'spark', 'hadoop', 'databricks',
        'snowflake', 'redshift', 'bigquery', 'data warehouse'
    ]
}

# Hiring intent keywords - must be present for a message to be considered a job post
HIRING_INTENT_KEYWORDS: List[str] = [
    'hiring', 'hiring for', 'looking for', 'wanted', 'opening', 'openings',
    'vacancy', 'vacancies', 'position', 'job opportunity', 'career',
    'we are hiring', 'join our team', 'apply now', 'apply here',
    'recruitment', 'recruiter', 'opportunity', 'join us', 'we need',
    'required immediately', 'immediate joining', 'urgent requirement',
    'walk-in', 'walkin', 'interview', 'fresher', 'experience required',
    'job opening', 'job role', 'seeking', 'candidate', 'applicant',
    'position available', 'job alert', 'job posting', 'now hiring'
]

# ==================== FILTERING & BLOCKLIST ====================
# Messages containing these terms will be ignored
BLOCKLIST_KEYWORDS: List[str] = [
    # Crypto/Trading spam
    'crypto', 'bitcoin', 'btc', 'eth', 'cryptocurrency', 'trading signals',
    'forex', 'binary option', 'investment plan', 'roi', 'pump',
    
    # Referral/MLM spam
    'referral', 'refer and earn', 'earn money', 'work from home',
    'part time income', 'side hustle', 'make money online', 'mlm',
    
    # Course advertisements
    'free course', 'paid course', 'enroll now', 'certification course',
    'online training', 'discount code', 'limited seats', 'batch starting',
    
    # Internship scams
    'unpaid intern', 'no stipend', 'certificate only', 'letter of recommendation',
    
    # Other spam
    'click here', 'dm me', 'telegram premium', 'followers', 'subscribers'
]

# Minimum message length (characters) to be considered
MIN_MESSAGE_LENGTH = 30

# Maximum message length for short description (characters)
MAX_DESCRIPTION_LENGTH = 200

# ==================== RATE LIMITING ====================
# Maximum alerts per hour to avoid spam
MAX_ALERTS_PER_HOUR = 30

# Delay between sending alerts (seconds)
ALERT_DELAY_SECONDS = 2

# ==================== DEDUPLICATION ====================
# Time window for duplicate detection (seconds)
# Messages with same content within this window will be ignored
DEDUP_WINDOW_SECONDS = 3600  # 1 hour

# Maximum cache size for deduplication
MAX_CACHE_SIZE = 10000

# ==================== LOGGING ====================
# Log level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL = 'INFO'

# Log format
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# ==================== LINK EXTRACTION ====================
# Valid job link domains (only extract links from these domains)
VALID_JOB_DOMAINS: List[str] = [
    'linkedin.com', 'indeed.com', 'glassdoor.com', 'naukri.com',
    'monster.com', 'dice.com', 'stackoverflow.com/jobs',
    'angel.co', 'wellfound.com', 'ycombinator.com/jobs',
    'greenhouse.io', 'lever.co', 'workday.com', 'recruitee.com',
    'jobvite.com', 'smartrecruiters.com', 'bamboohr.com',
    'instahyre.com', 'cutshort.io', 'hirect.in', 'apna.co'
]

# Blocked link patterns (Telegram invite links, etc.)
BLOCKED_LINK_PATTERNS: List[str] = [
    't.me/', 'telegram.me/', 'telegram.dog/',
    'wa.me/', 'whatsapp.com/', 'bit.ly/', 'tinyurl.com/'
]

# ==================== RECONNECTION SETTINGS ====================
# Auto-reconnect settings for Telethon
AUTO_RECONNECT = True
RECONNECT_DELAY_SECONDS = 5
MAX_RECONNECT_ATTEMPTS = 10

# ==================== FEATURE FLAGS ====================
# Enable/disable features
ENABLE_LINK_EXTRACTION = True
ENABLE_DEDUPLICATION = True
ENABLE_RATE_LIMITING = True
PROCESS_ONLY_NEW_MESSAGES = True  # If False, will process historical messages

# Future NLP/AI features (placeholders for extensibility)
ENABLE_AI_SCORING = False  # Set to True when implementing AI-based relevance scoring
AI_CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence score for AI classification

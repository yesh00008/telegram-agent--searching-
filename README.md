# Telegram Job Monitoring Bot

A production-ready Telegram bot that monitors public groups and channels for job postings in AI/ML, Cyber Security, Full Stack, Backend, Frontend, and Data roles.

## Features

✅ **Real-time Monitoring** - Monitors Telegram groups/channels using userbot (Telethon)  
✅ **Smart Job Detection** - Keyword-based filtering with hiring intent analysis  
✅ **Category Classification** - Automatically categorizes jobs into 6 domains  
✅ **Spam Filtering** - Blocks crypto, referrals, courses, and scam posts  
✅ **Link Extraction** - Extracts valid job links while ignoring Telegram invites  
✅ **Deduplication** - Hash-based caching to avoid duplicate alerts  
✅ **Rate Limiting** - Prevents Telegram API rate limit violations  
✅ **Auto-Reconnect** - Handles network disconnects gracefully  
✅ **Modular Architecture** - Clean separation of concerns, ready for AI/NLP extensions  
✅ **Production Ready** - Error handling, logging, configuration management  

## Architecture

```
telegram_job_bot/
├── main.py          # Entry point and orchestrator
├── config.py        # Configuration and settings
├── monitor.py       # Telethon userbot message listener
├── filters.py       # Job detection and filtering logic
├── notifier.py      # Telegram bot notification handler
├── utils.py         # Utilities (deduplication, rate limiting)
├── requirements.txt # Python dependencies
├── .env.example     # Environment variables template
└── README.md        # This file
```

## Prerequisites

1. **Python 3.8+** installed
2. **Telegram API Credentials** from https://my.telegram.org
   - API ID
   - API Hash
   - Phone number
3. **Telegram Bot Token** from @BotFather
4. **Alert Chat ID** (your user ID from @userinfobot)

## Installation

### 1. Clone or navigate to the project

```bash
cd telegram_job_bot
```

### 2. Create virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure credentials

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+1234567890
TELEGRAM_BOT_TOKEN=your_bot_token
ALERT_CHAT_ID=your_chat_id
```

**OR** edit `config.py` directly (lines 13-18).

### 5. Customize monitoring (optional)

Edit `config.py` to:
- Add specific groups to monitor (`MONITORED_GROUPS`)
- Adjust job categories and keywords (`JOB_CATEGORIES`)
- Modify blocklist terms (`BLOCKLIST_KEYWORDS`)
- Change rate limits and deduplication settings

## Usage

### Start the bot

```bash
python main.py
```

On first run, Telethon will ask for:
1. Your phone number (if not in config)
2. Verification code sent to Telegram
3. Two-factor password (if enabled)

The bot will then:
1. Connect to Telegram as your userbot
2. Start monitoring all joined groups/channels
3. Send job alerts to your configured chat

### Stop the bot

Press `Ctrl+C` for graceful shutdown.

## Configuration Reference

### Key Settings in `config.py`

| Setting | Description | Default |
|---------|-------------|---------|
| `MONITORED_GROUPS` | Specific groups to monitor (empty = all) | `[]` |
| `MIN_MESSAGE_LENGTH` | Minimum characters for valid job post | `50` |
| `MAX_ALERTS_PER_HOUR` | Rate limit for alerts | `30` |
| `DEDUP_WINDOW_SECONDS` | Duplicate detection window | `3600` (1 hour) |
| `AUTO_RECONNECT` | Auto-reconnect on disconnect | `True` |
| `PROCESS_ONLY_NEW_MESSAGES` | Ignore historical messages | `True` |

### Job Categories

- **AI/ML** - Machine Learning, Deep Learning, NLP, Computer Vision
- **Cyber Security** - Security Engineer, Pentester, SOC Analyst
- **Full Stack** - MERN, MEAN, Django+React
- **Backend** - Node.js, Django, Spring Boot, FastAPI
- **Frontend** - React, Angular, Vue.js, Next.js
- **Data** - Data Analyst, Data Engineer, Data Scientist, BI Developer

### Spam Filtering

The bot automatically filters:
- Crypto/trading spam
- Referral/MLM schemes
- Course advertisements
- Unpaid internship scams
- Forwarded messages
- Media-only posts
- Very short messages

## Alert Format

When a job is detected, you'll receive:

```
🤖 AI/ML Job Opening

📝 Description:
We are hiring ML Engineers for our AI team...

🔗 Application Links:
1. https://company.com/jobs/ml-engineer

📢 Source: Tech Jobs India
🕐 Posted: 2026-02-02 14:30:45
```

## Troubleshooting

### "Configuration errors" on startup

Make sure you've set:
- `TELEGRAM_API_ID` (numeric ID)
- `TELEGRAM_API_HASH` (string hash)
- `TELEGRAM_BOT_TOKEN` (bot token from BotFather)
- `ALERT_CHAT_ID` (your user ID or group chat ID)

### "Rate limit exceeded"

Increase `ALERT_DELAY_SECONDS` or decrease `MAX_ALERTS_PER_HOUR` in `config.py`.

### Bot not detecting jobs

1. Check that groups are public or userbot has joined
2. Review keywords in `JOB_CATEGORIES` and `HIRING_INTENT_KEYWORDS`
3. Enable DEBUG logging: set `LOG_LEVEL = 'DEBUG'` in `config.py`

### Connection errors

The bot auto-reconnects by default. Check:
- Internet connection
- Telegram API status
- `AUTO_RECONNECT` and `MAX_RECONNECT_ATTEMPTS` settings

## Extending with AI/NLP

The architecture is designed for easy AI integration:

1. **Set flag**: `ENABLE_AI_SCORING = True` in `config.py`
2. **Add model**: Create `ai_classifier.py` with scoring logic
3. **Integrate**: Call from `filters.py` → `JobDetector.is_job_post()`
4. **Dependencies**: Uncomment transformers/torch in `requirements.txt`

Example integration point in `filters.py`:

```python
# In JobDetector.is_job_post() method
if config.ENABLE_AI_SCORING:
    score = ai_classifier.score_relevance(text)
    if score < config.AI_CONFIDENCE_THRESHOLD:
        return False, None
```

## Production Deployment

### Running as a service (Linux)

Create `/etc/systemd/system/telegram-job-bot.service`:

```ini
[Unit]
Description=Telegram Job Monitoring Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/telegram_job_bot
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl enable telegram-job-bot
sudo systemctl start telegram-job-bot
sudo systemctl status telegram-job-bot
```

### Running with screen/tmux (Linux)

```bash
screen -S telegram_bot
python main.py
# Detach: Ctrl+A then D
# Reattach: screen -r telegram_bot
```

### Running on Windows

Use Windows Task Scheduler or run in background:

```powershell
Start-Process python -ArgumentList "main.py" -WindowStyle Hidden
```

## Security Best Practices

1. **Never commit `.env` or credentials** to version control
2. **Use environment variables** for production deployments
3. **Restrict file permissions** on config files (chmod 600)
4. **Monitor rate limits** to avoid account bans
5. **Keep dependencies updated** regularly
6. **Review logs** for suspicious activity

## Logs

Console logs show:
- Job detections with categories
- Alerts sent
- Rate limiting events
- Errors and warnings
- Reconnection attempts

Set `LOG_LEVEL = 'DEBUG'` for detailed debugging.

## Contributing

To extend the bot:

1. **Add job categories**: Edit `JOB_CATEGORIES` in `config.py`
2. **Custom filters**: Modify `filters.py` → `MessageFilter` class
3. **Alert format**: Edit `notifier.py` → `_format_alert_message()`
4. **Link validation**: Update `VALID_JOB_DOMAINS` in `config.py`

## License

This is a production-ready template. Modify as needed for your use case.

## Support

For issues:
1. Enable DEBUG logging
2. Check configuration values
3. Review Telegram API documentation
4. Check rate limits and quotas

---

**Built with:**
- [Telethon](https://docs.telethon.dev/) - Telegram userbot library
- [python-telegram-bot](https://python-telegram-bot.org/) - Bot API wrapper
- Python asyncio for concurrent operations

**Ready for deployment. Happy job hunting! 🚀**

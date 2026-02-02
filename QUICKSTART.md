# Quick Start Guide - Telegram Job Monitoring Bot

## 🚀 Get Started in 5 Minutes

### Step 1: Get Telegram Credentials

#### A. API Credentials (Userbot)
1. Go to https://my.telegram.org
2. Log in with your phone number
3. Click "API Development Tools"
4. Create a new application
5. Note down:
   - **API ID** (numeric, e.g., 12345678)
   - **API Hash** (string, e.g., abc123def456...)

#### B. Bot Token
1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Follow prompts to create your bot
4. Copy the **Bot Token** (format: `123456789:ABCdef...`)

#### C. Your Chat ID
1. Search for [@userinfobot](https://t.me/userinfobot) in Telegram
2. Send `/start`
3. Copy your **User ID** (numeric, e.g., 987654321)

### Step 2: Install

```bash
# Navigate to project folder
cd telegram_job_bot

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure

Create a `.env` file:

```env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_PHONE=+1234567890
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHI...
ALERT_CHAT_ID=987654321
```

**Replace with your actual values!**

### Step 4: Run

```bash
python main.py
```

On first run:
1. Enter verification code sent to your Telegram
2. Enter 2FA password (if enabled)
3. Bot will start monitoring!

### Step 5: Join Groups

The bot monitors all groups/channels where your account is a member:

1. Join Telegram job groups (e.g., "Tech Jobs India", "Remote Jobs")
2. Bot automatically detects job posts
3. Alerts sent to your configured chat

## ⚙️ Basic Customization

Edit `config.py` to customize:

### Monitor Specific Groups Only

```python
MONITORED_GROUPS = [
    '@techjobsindia',
    'Remote Jobs Channel',
    -1001234567890  # Chat ID
]
```

### Adjust Rate Limiting

```python
MAX_ALERTS_PER_HOUR = 50  # Default: 30
ALERT_DELAY_SECONDS = 1   # Default: 2
```

### Add Custom Keywords

```python
HIRING_INTENT_KEYWORDS = [
    'hiring', 'opening', 'vacancy',
    'your custom term here'
]
```

## 📊 What You'll See

### Console Output
```
============================================================
TELEGRAM JOB MONITORING BOT - Production Ready
============================================================
2026-02-02 14:30:45 - INFO - Logged in as: John Doe
2026-02-02 14:31:02 - INFO - Job detected: AI/ML from Tech Jobs
2026-02-02 14:31:03 - INFO - Alert #1 sent successfully
```

### Telegram Alerts
```
🤖 AI/ML Job Opening

📝 Description:
Hiring Machine Learning Engineers for our AI team...

🔗 Application Links:
https://company.com/careers/ml-engineer

📢 Source: Tech Jobs India
🕐 Posted: 2026-02-02 14:30:45
```

## 🛑 Stopping the Bot

Press `Ctrl+C` - the bot will shut down gracefully.

## ❓ Common Issues

### "Configuration errors"
→ Check your `.env` file has all 5 values filled in

### "No jobs detected"
→ Wait for new messages (historical messages are ignored by default)

### "Rate limit exceeded"
→ Reduce `MAX_ALERTS_PER_HOUR` in `config.py`

### Session authentication issues
→ Delete `*.session` files and restart

## 📚 Next Steps

- Read [README.md](README.md) for detailed documentation
- Review `config.py` for all available settings
- Check logs for debugging (`LOG_LEVEL = 'DEBUG'`)
- Deploy to server for 24/7 operation

## 🎯 Tips

1. **Start small**: Monitor 2-3 active job groups first
2. **Test alerts**: Join a test group and post a message with keywords
3. **Adjust keywords**: Fine-tune `JOB_CATEGORIES` based on results
4. **Monitor logs**: Watch console output to understand filtering
5. **Rate limits**: Start conservative to avoid Telegram bans

---

**Ready to find your next opportunity! 🎉**

Need help? Check the full [README.md](README.md) or review the source code comments.

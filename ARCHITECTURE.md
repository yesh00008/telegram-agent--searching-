# Project Architecture Documentation
# Telegram Job Monitoring Bot - Technical Overview

## 📋 System Overview

The Telegram Job Monitoring Bot is a production-ready, event-driven system that continuously monitors Telegram groups and channels for job postings in technical domains (AI/ML, Cyber Security, Full Stack, Backend, Frontend, Data roles).

### Key Characteristics
- **Architecture**: Event-driven microservices pattern
- **Language**: Python 3.8+
- **Concurrency**: asyncio-based async/await
- **Deployment**: Standalone script, Docker, or cloud services
- **State Management**: Session-based authentication, in-memory caching
- **Scalability**: Modular design ready for horizontal scaling

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         TELEGRAM                             │
│              (Groups, Channels, Bot API)                     │
└───────────────────┬─────────────────────┬───────────────────┘
                    │                     │
                    ▼                     ▼
        ┌──────────────────┐   ┌──────────────────┐
        │  Telethon Client │   │  Bot API Client  │
        │    (Userbot)     │   │  (Notifications) │
        └────────┬─────────┘   └────────┬─────────┘
                 │                      │
                 ▼                      │
    ┌────────────────────────┐         │
    │   Message Listener     │         │
    │   (monitor.py)         │         │
    └──────────┬─────────────┘         │
               │                       │
               ▼                       │
    ┌────────────────────────┐         │
    │  Message Filter        │         │
    │  (filters.py)          │         │
    │  ├─ Validation         │         │
    │  ├─ Blocklist Check    │         │
    │  ├─ Job Detection      │         │
    │  ├─ Category Detection │         │
    │  └─ Link Extraction    │         │
    └──────────┬─────────────┘         │
               │                       │
               ▼                       │
    ┌────────────────────────┐         │
    │  Deduplication         │         │
    │  (utils.py)            │         │
    │  ├─ Message Hash       │         │
    │  └─ Link Hash          │         │
    └──────────┬─────────────┘         │
               │                       │
               ▼                       │
    ┌────────────────────────┐         │
    │  Alert Formatter       │         │
    │  (notifier.py)         │         │
    │  ├─ Format Message     │         │
    │  └─ Rate Limit Check   │         │
    └──────────┬─────────────┘         │
               │                       │
               └───────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Send Notification   │
              │  (Telegram Bot)      │
              └──────────────────────┘
                         │
                         ▼
                ┌────────────────┐
                │   User Chat    │
                └────────────────┘
```

---

## 📁 Project Structure

```
telegram_job_bot/
│
├── main.py                 # Application entry point & orchestrator
│   ├── JobMonitorBot class
│   ├── Signal handlers (graceful shutdown)
│   ├── Auto-reconnect logic
│   └── Error recovery
│
├── config.py              # Configuration management (single source of truth)
│   ├── API credentials
│   ├── Job categories & keywords
│   ├── Blocklist terms
│   ├── Rate limiting settings
│   ├── Deduplication settings
│   └── Feature flags
│
├── monitor.py             # Telethon userbot implementation
│   ├── TelegramMonitor class
│   ├── Event handlers (NewMessage)
│   ├── Entity management (groups/channels)
│   └── Message routing to filters
│
├── filters.py             # Message filtering & job detection
│   ├── MessageFilter (validation, preprocessing)
│   ├── JobDetector (category classification)
│   └── LinkExtractor (URL extraction & validation)
│
├── notifier.py            # Notification sending via Bot API
│   ├── NotificationHandler (main bot)
│   ├── FallbackNotifier (direct API)
│   ├── Alert formatting (HTML templates)
│   └── Rate limiting integration
│
├── utils.py               # Utilities & helpers
│   ├── DedupManager (hash-based caching)
│   ├── RateLimiter (token bucket algorithm)
│   ├── Logging setup
│   ├── Config validation
│   └── Timestamp formatting
│
├── ai_classifier.py       # AI/NLP extension placeholder
│   ├── AIJobClassifier
│   ├── SentimentAnalyzer
│   └── Integration examples
│
├── tests.py               # Comprehensive test suite
│   ├── Unit tests
│   ├── Integration tests
│   └── Mock data
│
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
├── __init__.py            # Package initialization
│
├── README.md              # Full documentation
├── QUICKSTART.md          # 5-minute setup guide
├── DEPLOYMENT.md          # Production deployment guide
│
├── Dockerfile             # Container image definition
└── docker-compose.yml     # Docker orchestration
```

---

## 🔄 Data Flow

### 1. Message Reception
```
Telegram Group → Telethon Client → NewMessage Event → monitor.py
```

### 2. Filtering Pipeline
```python
Message
  → is_valid_message()        # Length, forward check, media check
  → contains_blocklist_terms() # Crypto, spam, course ads
  → has_hiring_intent()        # "hiring", "vacancy", etc.
  → detect_job_category()      # Match against JOB_CATEGORIES
  → is_duplicate()             # Hash-based deduplication
```

### 3. Link Extraction
```python
Message Text
  → regex URL extraction
  → filter blocked domains (t.me, wa.me)
  → validate against VALID_JOB_DOMAINS
  → deduplicate links
  → return unique URLs
```

### 4. Alert Generation
```python
Job Data
  → format_alert_message()     # HTML formatting with emoji
  → check rate limit
  → send_message() via Bot API
  → log success/failure
```

---

## 🎯 Core Algorithms

### Job Detection Algorithm
```python
def is_job_post(message):
    # Step 1: Basic validation
    if not is_valid(message):
        return False, None
    
    # Step 2: Blocklist check (negative filter)
    if contains_spam_keywords(message):
        return False, None
    
    # Step 3: Hiring intent (required signal)
    if not has_hiring_keywords(message):
        return False, None
    
    # Step 4: Category classification
    category = classify_by_keywords(message)
    
    if category:
        return True, category
    else:
        return False, None
```

### Deduplication Algorithm
```python
def is_duplicate(text, timestamp):
    # Hash-based with time window
    text_hash = md5(normalize(text))
    
    # Clean old entries outside time window
    cleanup_old_hashes(current_time - WINDOW)
    
    # Check if hash exists
    if text_hash in cache:
        return True  # Duplicate
    
    # Add to cache
    cache.add(text_hash, timestamp)
    return False
```

### Rate Limiting Algorithm
```python
def can_send():
    # Token bucket / sliding window
    current_time = now()
    one_hour_ago = current_time - 1_hour
    
    # Remove old timestamps
    remove_timestamps_before(one_hour_ago)
    
    # Check count
    if count(timestamps) < MAX_PER_HOUR:
        timestamps.append(current_time)
        return True
    
    return False  # Rate limited
```

---

## 🔌 Integration Points

### External Systems
1. **Telegram MTProto API** (via Telethon)
   - Authentication
   - Message streaming
   - Entity resolution

2. **Telegram Bot API** (via python-telegram-bot)
   - Send messages
   - HTML formatting
   - Error handling

### Future Extensions
1. **Database Integration**
   ```python
   # In monitor.py after job detection:
   await db.save_job_post(category, description, links, source)
   ```

2. **AI/NLP Integration**
   ```python
   # In filters.py:
   if config.ENABLE_AI_SCORING:
       score = ai_classifier.score_relevance(text)
       if score < threshold:
           return False, None
   ```

3. **Web Dashboard**
   ```python
   # Expose metrics endpoint:
   from flask import Flask, jsonify
   
   @app.route('/metrics')
   def metrics():
       return jsonify({
           'jobs_detected': counter.total,
           'alerts_sent': notifier.alert_count,
           'cache_size': dedup.get_stats()
       })
   ```

4. **Message Queue**
   ```python
   # For high-volume processing:
   import redis
   
   async def on_job_detected(job_data):
       await redis_queue.enqueue('job_processing', job_data)
   ```

---

## ⚙️ Configuration Strategy

### Hierarchy
1. **Environment Variables** (.env) - Highest priority
2. **config.py defaults** - Fallback values
3. **Hard-coded constants** - Last resort

### Hot-Reloadable Settings
Currently requires restart. To add hot-reload:
```python
import watchdog

def reload_config_on_change():
    watcher = FileSystemWatcher('config.py')
    watcher.on_modified(lambda: importlib.reload(config))
```

---

## 🔐 Security Considerations

### Credential Management
- ✅ Never commit `.env` or `.session` files
- ✅ Use environment variables in production
- ✅ Restrict file permissions (chmod 600)
- ✅ Separate bot token from API credentials

### Rate Limiting
- ✅ Telegram API: 30 messages/second (handled by Telethon)
- ✅ Bot API: 30 messages/second to same chat
- ✅ Custom: `MAX_ALERTS_PER_HOUR` configurable

### Error Handling
- ✅ Graceful degradation on network errors
- ✅ Auto-reconnect with exponential backoff
- ✅ Error notifications to admin
- ✅ Comprehensive logging

---

## 📊 Performance Characteristics

### Resource Usage (Typical)
- **Memory**: 50-150 MB (depends on cache size)
- **CPU**: <5% on idle, <15% when processing
- **Network**: ~100-500 KB/minute (depends on group activity)

### Scalability Limits
- **Messages/second**: ~100 (Telethon limit)
- **Groups monitored**: Unlimited (all joined groups)
- **Cache size**: Configurable (default 10,000 entries)
- **Concurrent operations**: Async I/O (thousands)

### Optimization Opportunities
1. **Database for deduplication** (Redis/PostgreSQL)
2. **Batch notifications** (combine multiple jobs)
3. **Parallel processing** (multiple worker coroutines)
4. **Lazy loading** (load configs on-demand)

---

## 🧪 Testing Strategy

### Test Coverage
```
tests.py
├── Unit Tests
│   ├── MessageFilter (5 tests)
│   ├── JobDetector (7 tests)
│   ├── LinkExtractor (4 tests)
│   ├── DedupManager (4 tests)
│   └── RateLimiter (3 tests)
│
└── Integration Tests
    └── Complete workflow (1 test)

Total: 24+ test cases
```

### Running Tests
```bash
# Install pytest
pip install pytest pytest-asyncio

# Run all tests
pytest tests.py -v

# Run with coverage
pytest tests.py --cov=. --cov-report=html

# Run specific test
pytest tests.py::TestJobDetector::test_detect_ai_ml_job -v
```

---

## 🚀 Deployment Patterns

### Pattern 1: Single Instance
```
Server → Python Process → Bot Instance
```
- **Use case**: Personal use, <10 groups
- **Pros**: Simple, low resource
- **Cons**: Single point of failure

### Pattern 2: Container
```
Server → Docker → Bot Container
```
- **Use case**: Professional deployment
- **Pros**: Isolated, reproducible
- **Cons**: Slight overhead

### Pattern 3: Multi-Instance
```
Load Balancer → [Bot1, Bot2, Bot3]
                     ↓
                Shared Redis Cache
```
- **Use case**: High-volume monitoring
- **Pros**: Scalable, fault-tolerant
- **Cons**: Complex setup

---

## 📈 Monitoring & Observability

### Logs
```python
# Structured logging example
logger.info("Job detected", extra={
    'category': category,
    'source': source_name,
    'has_links': len(links) > 0
})
```

### Metrics to Track
- Jobs detected (by category)
- Alerts sent
- Messages processed
- Duplicates filtered
- Rate limit hits
- Errors encountered
- Reconnection events

### Health Checks
```python
# Add to main.py
async def health_check():
    return {
        'status': 'healthy' if is_running else 'down',
        'uptime': time.time() - start_time,
        'last_message': last_message_time,
        'alerts_sent': notifier.alert_count
    }
```

---

## 🛠️ Maintenance Guide

### Regular Tasks
- **Daily**: Check logs for errors
- **Weekly**: Review detected jobs, adjust keywords
- **Monthly**: Update dependencies, rotate logs
- **Quarterly**: Review and optimize filters

### Backup Strategy
```bash
# What to backup:
- *.session (authentication)
- .env (credentials)
- config.py (customizations)
- logs/ (historical data)

# Automated backup:
0 2 * * * /opt/backup_telegram_bot.sh
```

---

## 🎓 Best Practices

### Code Quality
- ✅ Type hints on all functions
- ✅ Docstrings on all modules/classes
- ✅ Single Responsibility Principle
- ✅ DRY (Don't Repeat Yourself)
- ✅ Error handling on all async operations

### Operational
- ✅ Start with DEBUG logging initially
- ✅ Monitor first 24 hours closely
- ✅ Adjust keywords based on false positives
- ✅ Set conservative rate limits initially
- ✅ Test in small group before scaling

### Development
- ✅ Use virtual environment
- ✅ Pin dependency versions
- ✅ Test before deploying
- ✅ Use version control (Git)
- ✅ Document configuration changes

---

## 🔮 Future Enhancements

### Planned Features
1. **AI-Based Classification**
   - Fine-tuned BERT model
   - Confidence scoring
   - Skill extraction

2. **Web Dashboard**
   - Real-time job listings
   - Analytics and insights
   - Manual moderation

3. **Database Backend**
   - PostgreSQL for job storage
   - Redis for caching
   - Full-text search

4. **Advanced Filtering**
   - Salary range extraction
   - Location filtering
   - Experience level detection

5. **Multi-User Support**
   - User registration
   - Custom keyword preferences
   - Multiple notification channels

---

## 📚 References

### Libraries Used
- **Telethon**: https://docs.telethon.dev/
- **python-telegram-bot**: https://python-telegram-bot.org/
- **asyncio**: https://docs.python.org/3/library/asyncio.html

### Telegram APIs
- **MTProto API**: https://core.telegram.org/api
- **Bot API**: https://core.telegram.org/bots/api

### Related Documentation
- [README.md](README.md) - User documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick setup
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production guide

---

**Architecture Version**: 1.0.0  
**Last Updated**: 2026-02-02  
**Status**: Production Ready ✅

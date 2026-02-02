# Deployment Guide - Production Setup

## 🚀 Deployment Options

### Option 1: Direct Python Deployment

#### Linux/Ubuntu Server

1. **Install Python 3.8+**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

2. **Clone/Upload code**
```bash
cd /opt
# Upload your code here
cd telegram_job_bot
```

3. **Setup virtual environment**
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. **Configure credentials**
```bash
cp .env.example .env
nano .env  # Edit with your credentials
```

5. **Run initial authentication**
```bash
python main.py
# Enter verification code when prompted
# Ctrl+C to stop after authentication
```

6. **Create systemd service**
```bash
sudo nano /etc/systemd/system/telegram-job-bot.service
```

Paste:
```ini
[Unit]
Description=Telegram Job Monitoring Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/opt/telegram_job_bot
Environment="PATH=/opt/telegram_job_bot/venv/bin"
ExecStart=/opt/telegram_job_bot/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/telegram-job-bot.log
StandardError=append:/var/log/telegram-job-bot-error.log

[Install]
WantedBy=multi-user.target
```

7. **Start service**
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-job-bot
sudo systemctl start telegram-job-bot
sudo systemctl status telegram-job-bot
```

8. **View logs**
```bash
sudo journalctl -u telegram-job-bot -f
# OR
tail -f /var/log/telegram-job-bot.log
```

---

### Option 2: Docker Deployment

#### Prerequisites
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose
```

#### Build and Run

1. **Configure environment**
```bash
cp .env.example .env
nano .env  # Add your credentials
```

2. **Build image**
```bash
docker-compose build
```

3. **First run (for authentication)**
```bash
docker-compose run --rm telegram-job-bot
# Enter verification code
# Ctrl+C after authentication
```

4. **Start service**
```bash
docker-compose up -d
```

5. **View logs**
```bash
docker-compose logs -f
```

6. **Stop service**
```bash
docker-compose down
```

#### Docker Commands Reference
```bash
# Restart bot
docker-compose restart

# Update and restart
docker-compose pull
docker-compose up -d

# View resource usage
docker stats telegram_job_monitor

# Shell access
docker-compose exec telegram-job-bot bash
```

---

### Option 3: Cloud Deployment

#### AWS EC2

1. **Launch EC2 instance**
   - Ubuntu 22.04 LTS
   - t2.micro (free tier eligible)
   - Open port 22 (SSH) only

2. **SSH into instance**
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

3. **Follow Linux deployment steps above**

4. **Setup security**
```bash
# Update firewall
sudo ufw allow 22/tcp
sudo ufw enable

# Keep system updated
sudo apt update && sudo apt upgrade -y
```

#### Google Cloud Run (Serverless)

```bash
# Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/telegram-job-bot

# Deploy
gcloud run deploy telegram-job-bot \
  --image gcr.io/PROJECT_ID/telegram-job-bot \
  --platform managed \
  --region us-central1 \
  --set-env-vars TELEGRAM_API_ID=xxx,TELEGRAM_API_HASH=xxx,...
```

#### Azure Container Instances

```bash
# Login
az login

# Create resource group
az group create --name telegram-bot-rg --location eastus

# Deploy container
az container create \
  --resource-group telegram-bot-rg \
  --name telegram-job-bot \
  --image your-registry/telegram-job-bot \
  --environment-variables \
    TELEGRAM_API_ID=xxx \
    TELEGRAM_API_HASH=xxx \
    TELEGRAM_BOT_TOKEN=xxx \
    ALERT_CHAT_ID=xxx
```

#### DigitalOcean Droplet

1. Create Ubuntu 22.04 droplet ($6/month)
2. Follow Linux deployment steps
3. Enable monitoring and backups

---

### Option 4: VPS Deployment

#### Popular VPS Providers
- **DigitalOcean**: $6/month
- **Linode**: $5/month
- **Vultr**: $6/month
- **Hetzner**: €4/month

#### Quick Setup
```bash
# SSH into VPS
ssh root@your-vps-ip

# Update system
apt update && apt upgrade -y

# Install requirements
apt install python3.11 python3.11-venv git

# Clone repository
git clone <your-repo-url> /opt/telegram_job_bot
cd /opt/telegram_job_bot

# Follow steps from Linux deployment
```

---

## 🔒 Security Best Practices

### 1. Environment Variables
```bash
# Never commit .env or session files
echo ".env" >> .gitignore
echo "*.session*" >> .gitignore

# Restrict file permissions
chmod 600 .env
chmod 600 *.session
```

### 2. Firewall Configuration
```bash
# UFW (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw enable
```

### 3. SSH Hardening
```bash
# Disable password auth (use SSH keys only)
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
sudo systemctl restart sshd
```

### 4. Regular Updates
```bash
# Setup automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 5. Monitoring
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Monitor bot
htop  # Check CPU/RAM
sudo journalctl -u telegram-job-bot -f  # Logs
```

---

## 📊 Monitoring & Maintenance

### Log Management

#### Rotate logs
```bash
sudo nano /etc/logrotate.d/telegram-job-bot
```

```
/var/log/telegram-job-bot*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 your_user your_user
    sharedscripts
    postrotate
        systemctl reload telegram-job-bot > /dev/null 2>&1 || true
    endscript
}
```

### Health Checks

Create monitoring script:
```bash
#!/bin/bash
# check_bot.sh

if ! systemctl is-active --quiet telegram-job-bot; then
    echo "Bot is down! Restarting..."
    systemctl restart telegram-job-bot
    # Send alert (optional)
fi
```

Add to crontab:
```bash
crontab -e
# Add: */5 * * * * /path/to/check_bot.sh
```

### Backup

```bash
#!/bin/bash
# backup_bot.sh

BACKUP_DIR="/backup/telegram_bot"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup session and config
tar -czf $BACKUP_DIR/bot_backup_$DATE.tar.gz \
    /opt/telegram_job_bot/*.session* \
    /opt/telegram_job_bot/.env \
    /opt/telegram_job_bot/config.py

# Keep only last 7 backups
find $BACKUP_DIR -name "bot_backup_*.tar.gz" -mtime +7 -delete
```

---

## 🔧 Troubleshooting

### Bot stops unexpectedly
```bash
# Check logs
sudo journalctl -u telegram-job-bot -n 100

# Check system resources
free -h
df -h

# Restart service
sudo systemctl restart telegram-job-bot
```

### Session authentication issues
```bash
# Delete session and re-authenticate
rm *.session*
python main.py  # Re-enter verification code
```

### High memory usage
```bash
# Edit config.py
# Reduce: MAX_CACHE_SIZE = 1000
# Reduce: DEDUP_WINDOW_SECONDS = 1800
```

### Rate limit errors
```bash
# Edit config.py
# Increase: ALERT_DELAY_SECONDS = 3
# Decrease: MAX_ALERTS_PER_HOUR = 20
```

---

## 📈 Scaling

### Multiple Bots
Run separate instances for different job categories:

```bash
# Create separate directories
/opt/telegram_bot_ai_ml/
/opt/telegram_bot_security/
/opt/telegram_bot_data/

# Configure each with filtered categories
# Run as separate systemd services
```

### Load Balancing
For high-volume monitoring:
- Use multiple Telegram accounts
- Distribute groups across instances
- Use Redis for shared deduplication

---

## ✅ Post-Deployment Checklist

- [ ] Bot starts automatically on server reboot
- [ ] Logs are being written and rotated
- [ ] Receiving job alerts in Telegram
- [ ] Monitoring/health checks configured
- [ ] Backups scheduled
- [ ] Firewall configured
- [ ] SSH hardened
- [ ] Resource usage acceptable (<50% RAM/CPU)
- [ ] Error notifications working
- [ ] Session files backed up

---

**Need help?** Check main [README.md](README.md) or review logs with `LOG_LEVEL='DEBUG'`

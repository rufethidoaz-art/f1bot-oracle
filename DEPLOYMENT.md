# Deployment Guide

This guide covers deploying the F1 Telegram Bot to a Linux server using systemd.

## Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Python 3.10 or higher
- sudo access
- Telegram Bot Token

## Step-by-Step Deployment

### 1. Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install Python 3.10+

```bash
# Check current version
python3 --version

# If needed, install Python 3.10+
sudo apt install python3.10 python3.10-venv python3-pip -y
```

### 3. Clone Repository

```bash
cd /home/opc  # or your preferred directory
git clone <your-repo-url> f1bot2026update
cd f1bot2026update
```

### 4. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium
```

### 6. Configure Environment

```bash
cp .env.example .env
nano .env
```

Add your bot token:
```
TELEGRAM_BOT_TOKEN=your_actual_token_here
```

### 7. Test the Bot

```bash
python3 main.py
```

Press Ctrl+C to stop after confirming it works.

### 8. Set Up systemd Service

```bash
# Update the service file paths if needed
sudo nano setup/f1bot.service

# Copy to systemd
sudo cp setup/f1bot.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### 9. Enable and Start Service

```bash
sudo systemctl enable f1bot
sudo systemctl start f1bot
```

### 10. Verify Service

```bash
sudo systemctl status f1bot
sudo journalctl -u f1bot -f
```

## Updating the Bot

```bash
cd /home/opc/f1bot2026update
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart f1bot
```

## Troubleshooting

### Check Logs

```bash
sudo journalctl -u f1bot -n 100 --no-pager
```

### Restart Service

```bash
sudo systemctl restart f1bot
```

### Check Service Status

```bash
sudo systemctl status f1bot
```

### Manual Test

```bash
cd /home/opc/f1bot2026update
source venv/bin/activate
python3 main.py
```

## Python Version Upgrade

If you need to upgrade Python:

```bash
# Install new Python version
sudo apt install python3.11 python3.11-venv -y

# Recreate virtual environment
cd /home/opc/f1bot2026update
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Restart service
sudo systemctl restart f1bot
```

## Security Notes

- Never commit `.env` file to git
- Keep your bot token secure
- Regularly update dependencies
- Monitor logs for errors

## Performance Optimization

- The bot uses caching to minimize API calls
- Live timing updates every 3 seconds (configurable in code)
- Message regeneration every 10 minutes to avoid Telegram limits

## Support

For issues or questions, check the logs first:
```bash
sudo journalctl -u f1bot -f
```

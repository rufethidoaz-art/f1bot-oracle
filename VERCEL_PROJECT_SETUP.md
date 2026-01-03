# F1 Telegram Bot - Vercel Project Setup Guide

This guide provides the exact configuration needed when setting up your F1 Telegram Bot project on Vercel.

## 🎯 Vercel Project Configuration

When you import your GitHub repository to Vercel, use these exact settings:

### Project Settings

| Setting | Value |
|---------|-------|
| **Framework Preset** | `Other` |
| **Build Command** | `bash vercel-build.sh` |
| **Output Directory** | `api` |
| **Install Command** | `pip install -r requirements.txt` |
| **Development Command** | (leave empty) |

### Environment Variables

Add these in **Project Settings → Environment Variables**:

| Variable | Value | Notes |
|----------|-------|-------|
| `TELEGRAM_BOT_TOKEN` | `your_bot_token_from_botfather` | Get from @BotFather |
| `WEBHOOK_URL` | `https://your-project.vercel.app/webhook` | Set after deployment |

**Important**: Enter the actual values directly. Do NOT use `@variable_name` syntax.

## 📋 Step-by-Step Deployment

### Step 1: Import Repository
1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click **"Add New"** → **"Project"**
3. Select your GitHub repository (`rufethidoaz-art/f1bot2026update`)
4. Click **"Import"**

### Step 2: Configure Project
Configure the project with these exact settings:

```
Project Name: f1-telegram-bot (or your preferred name)

Framework Preset: Other
Build Command: bash vercel-build.sh
Output Directory: api
Install Command: pip install -r requirements.txt
```

### Step 3: Set Environment Variables
Add these variables:

```
TELEGRAM_BOT_TOKEN = 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
WEBHOOK_URL = https://your-project.vercel.app/webhook
```

**Note**: The `WEBHOOK_URL` will be available after deployment. You can:
1. Deploy first without it
2. Get your project URL
3. Add the webhook URL
4. Redeploy

### Step 4: Deploy
Click **"Deploy"** and wait for the build to complete.

## 🔍 Build Process Details

### What Happens During Build

Your `vercel-build.sh` script runs:

```bash
#!/bin/bash
echo "Building F1 Telegram Bot for Vercel..."

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium --with-deps

# Create necessary directories
mkdir -p /tmp/playwright

echo "Build completed successfully!"
```

### Build Output
You should see:
```
✓ Completed under 2 minutes
✓ Build logs show Playwright installation
✓ All Python packages installed
```

## 🎯 After Deployment

### 1. Get Your URLs
Once deployed, Vercel provides:
- **Main URL**: `https://your-project.vercel.app`
- **Webhook URL**: `https://your-project.vercel.app/webhook`

### 2. Set Webhook
Visit your webhook setup endpoint:
```
https://your-project.vercel.app/set-webhook
```

Or use Telegram API:
```bash
curl -F "url=https://your-project.vercel.app/webhook" \
     https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook
```

### 3. Test Your Bot
Send these commands in Telegram:
- `/start` - Should show welcome message
- `/health` - Check: `https://your-project.vercel.app/health`
- `/debug` - Check: `https://your-project.vercel.app/debug`

## 📊 Monitoring & Logs

### Vercel Dashboard
- **Functions**: View serverless function invocations
- **Logs**: Real-time logs for debugging
- **Metrics**: Performance and usage statistics

### Health Check Endpoints
```
https://your-project.vercel.app/health
https://your-project.vercel.app/debug
https://your-project.vercel.app/webhook-info
```

## 🔧 Troubleshooting

### Build Fails
**Check**:
- Build command: `bash vercel-build.sh`
- Output directory: `api`
- Install command: `pip install -r requirements.txt`

### Bot Not Responding
**Check**:
1. Environment variables are set correctly
2. Webhook is configured: `https://your-project.vercel.app/set-webhook`
3. Bot token is valid

### Playwright Issues
**Solution**: Ensure build script runs:
```
playwright install chromium --with-deps
```

### Memory Issues
**Solution**: 
- Upgrade to Vercel Pro (1GB memory)
- Or optimize: Use OpenF1 API instead of scraping

## 🚀 Quick Reference

### Project Structure
```
f1-telegram-bot/
├── api/                    # Vercel output directory
│   ├── webhook.py         # Main handler
│   ├── health.py          # Health check
│   ├── index.py           # Info endpoint
│   ├── debug.py           # Debug info
│   ├── webhook_info.py    # Webhook status
│   └── set_webhook.py     # Webhook setup
├── f1_bot_live.py         # Bot handlers
├── f1_playwright_scraper_fixed.py  # Scraper
├── requirements.txt       # Python deps
├── vercel.json            # Vercel config
├── vercel-build.sh        # Build script
└── package.json           # Build config
```

### Key Files Explained

**`vercel.json`** - Routes and configuration:
```json
{
  "version": 2,
  "builds": [{"src": "api/*.py", "use": "@vercel/python"}],
  "routes": [
    {"src": "/webhook", "dest": "api/webhook.py"},
    {"src": "/health", "dest": "api/health.py"}
  ],
  "env": {
    "TELEGRAM_BOT_TOKEN": "${TELEGRAM_BOT_TOKEN}",
    "WEBHOOK_URL": "${WEBHOOK_URL}"
  }
}
```

**`vercel-build.sh`** - Build script:
```bash
pip install -r requirements.txt
playwright install chromium --with-deps
```

**`requirements.txt`** - Python dependencies:
```
python-telegram-bot==20.7
requests==2.32.3
playwright==1.40.0
beautifulsoup4==4.12.2
lxml==4.9.3
python-dateutil==2.8.2
httpx==0.25.2
structlog==23.2.0
```

## 🎯 Success Checklist

- [ ] Project imported to Vercel
- [ ] Framework: Other
- [ ] Build Command: `bash vercel-build.sh`
- [ ] Output Directory: `api`
- [ ] Install Command: `pip install -r requirements.txt`
- [ ] Environment variables set
- [ ] Deployment successful
- [ ] Webhook configured
- [ ] Bot responds to `/start`

## 📞 Need Help?

1. Check `/debug` endpoint for detailed error information
2. Review Vercel logs in dashboard
3. Verify environment variables are set correctly
4. Ensure Telegram bot token is valid

---

**Your bot is ready for Vercel deployment!** 🚀
# Vercel Deployment Configuration Guide

## 🚀 Complete Vercel Setup Instructions

### Project Configuration

**Root Directory:** `/` (project root)

**Framework Preset:** `None` (Custom)

**Environment Presets:** `Python`

### Build Settings

**Install Command:** `pip install -r requirements.txt`

**Build Command:** `Leave empty` (No build step needed for Python serverless functions)

**Output Directory:** `Leave empty` (Vercel auto-detects Python functions)

### Environment Variables

Required environment variables to set in Vercel dashboard:

| Variable Name | Value | Description |
|---------------|-------|-------------|
| `TELEGRAM_BOT_TOKEN` | Your bot token | Telegram bot token from @BotFather |

### Function Configuration

**Function Runtime:** Python 3.11 (auto-detected)

**Max Duration:** 30 seconds (configured in vercel.json)

**Memory:** 1024 MB (default)

### File Structure for Vercel

```
F1-bot-vercel/
├── app.py              # Main Flask application (Vercel entry point)
├── f1_bot.py           # Bot logic and handlers
├── requirements.txt    # Python dependencies
├── vercel.json         # Vercel configuration
├── streams.txt         # Stream configuration
├── README.md          # Documentation
└── .gitignore         # Git ignore rules
```

### Vercel.json Configuration

```json
{
  "version": 2,
  "name": "f1-bot-vercel",
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/",
      "dest": "app.py"
    },
    {
      "src": "/health",
      "dest": "app.py"
    },
    {
      "src": "/webhook",
      "dest": "app.py"
    }
  ],
  "functions": {
    "app.py": {
      "maxDuration": 30
    }
  }
}
```

### Deployment Steps

1. **Import Repository**
   - Go to Vercel Dashboard
   - Click "New Project"
   - Import from GitHub
   - Select this repository

2. **Configure Project**
   - Framework Preset: `None`
   - Root Directory: `/` (default)
   - Install Command: `pip install -r requirements.txt`
   - Build Command: `Leave empty`
   - Output Directory: `Leave empty`

3. **Set Environment Variables**
   - Go to Project Settings → Environment Variables
   - Add: `TELEGRAM_BOT_TOKEN` with your bot token

4. **Deploy**
   - Click "Deploy"
   - Wait for deployment (2-3 minutes)

5. **Configure Webhook**
   - After deployment, get your Vercel URL
   - Set webhook: `https://api.telegram.org/bot{TOKEN}/setWebhook?url={VERCEL_URL}/webhook`

### Vercel Dashboard Settings

**Project Settings:**
- **General** → Project Name: `f1-bot-vercel`
- **Functions** → Runtime: `Python 3.11`
- **Functions** → Max Duration: `30s`
- **Environment Variables** → Add `TELEGRAM_BOT_TOKEN`

**Build & Development Settings:**
- **Install Command:** `pip install -r requirements.txt`
- **Build Command:** *(empty)*
- **Output Directory:** *(empty)*
- **Root Directory:** `/`

### Monitoring & Logs

**View Logs:**
- Vercel Dashboard → Project → Logs
- Real-time function execution logs
- Error tracking and debugging

**Performance Monitoring:**
- Function execution time
- Memory usage
- Request/response logs

### Troubleshooting

**Common Issues:**

1. **Build Failures:**
   - Check requirements.txt syntax
   - Ensure all dependencies are compatible with Python 3.11
   - Verify no syntax errors in Python files

2. **Function Timeouts:**
   - Increase maxDuration in vercel.json if needed
   - Optimize API calls and data processing

3. **Environment Variables:**
   - Ensure TELEGRAM_BOT_TOKEN is set correctly
   - Check for typos in variable names

4. **Webhook Issues:**
   - Verify Vercel URL is correct
   - Check that deployment is successful
   - Ensure HTTPS is enabled

5. **Build Warnings:**
   - If you see: "Due to `builds` existing in your configuration file, the Build and Development Settings defined in your Project Settings will not apply"
   - This is expected behavior - the vercel.json configuration takes precedence
   - The warning can be safely ignored as our configuration is optimized for the F1 bot
   - To eliminate the warning, ensure your vercel.json has proper function configuration (already configured)

### Cost Optimization

**Free Tier Usage:**
- 100GB bandwidth per month
- 125,000 invocations per month
- 10s function timeout (increased to 30s in config)

**Optimization Tips:**
- Keep dependencies minimal
- Use efficient API calls
- Cache responses when possible
- Monitor usage in Vercel dashboard

### Security Considerations

**Environment Variables:**
- Never commit bot tokens to repository
- Use Vercel's secure environment variable storage
- Rotate tokens regularly

**Function Security:**
- Validate all incoming webhook requests
- Use HTTPS for all communications
- Implement rate limiting if needed

### Scaling

**Automatic Scaling:**
- Vercel automatically scales based on traffic
- No manual configuration needed
- Pay-per-use pricing model

**Performance Optimization:**
- Cold start optimization with minimal dependencies
- Efficient API calls to external services
- Proper error handling and retries
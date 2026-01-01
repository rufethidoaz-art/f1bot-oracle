# F1 Bot - Leapcell Deployment Validation Checklist

## Pre-Deployment Validation

### 1. Environment Configuration
- [ ] **TELEGRAM_BOT_TOKEN** configured in environment variables
- [ ] **PORT** set to 8080 (matches leapcell.yaml)
- [ ] Bot token format is valid (contains bot_id:token)

### 2. Code Validation
- [ ] All imports work correctly
- [ ] Flask app starts without errors
- [ ] Health check endpoint responds at `/health`
- [ ] Webhook endpoint configured at `/webhook`

### 3. Dependencies
- [ ] `python-telegram-bot==20.7` installed
- [ ] `flask==3.0.3` installed  
- [ ] `gunicorn==21.2.0` installed
- [ ] `requests==2.32.3` installed
- [ ] `python-dotenv==1.0.1` installed

### 4. Leapcell Configuration
- [ ] `leapcell.yaml` configured correctly
- [ ] Build command: `pip install -r requirements.txt`
- [ ] Start command: `gunicorn -w 1 -b :8080 app:app`
- [ ] Port: 8080

## Live Timing Feature Testing

### 1. API Connectivity
- [ ] OpenF1 API accessible: `https://api.openf1.org/v1/sessions`
- [ ] Jolpica F1 API accessible: `https://api.jolpi.ca/ergast/f1/2024/driverStandings.json`
- [ ] Weather API accessible: `https://api.open-meteo.com/v1/forecast`

### 2. F1 Session Detection
- [ ] Session detection works during F1 weekends
- [ ] Correctly identifies active sessions
- [ ] Handles no active session gracefully

### 3. Live Timing Functions
- [ ] `check_live_timing_available()` returns correct boolean
- [ ] `get_live_session_info()` returns session data
- [ ] `get_live_positions()` fetches driver positions
- [ ] `format_live_timing_message()` formats messages correctly

### 4. Caching System
- [ ] Cache reduces API calls
- [ ] Cache expiration works correctly
- [ ] Different cache keys function independently

## Error Handling & Edge Cases

### 1. Invalid Data Handling
- [ ] Handles missing session data gracefully
- [ ] Handles invalid session keys
- [ ] Handles network timeouts

### 2. Message Formatting
- [ ] Empty data handled gracefully
- [ ] Unicode characters supported
- [ ] Long messages truncated properly

## Deployment Testing Commands

### Run Full Test Suite
```bash
python test_leapcell_deployment.py
```

### Test Flask App Locally
```bash
python app.py
```

### Test Health Endpoint
```bash
curl http://localhost:8080/health
```

### Test Webhook Endpoint
```bash
curl -X POST http://localhost:8080/webhook
```

### Test Bot Commands
Send these commands to your bot:
- `/start` - Should show welcome message
- `/menu` - Should show main menu
- `/standings` - Should show current standings
- `/constructors` - Should show constructor standings
- `/lastrace` - Should show last session results
- `/nextrace` - Should show next race info
- `/live` - Should show live timing (if session active)

## Common Issues & Solutions

### Bot Not Responding
1. Check TELEGRAM_BOT_TOKEN is set correctly
2. Verify webhook URL is configured in BotFather
3. Check health endpoint responds
4. Review logs for initialization errors

### Live Timing Not Working
1. Verify OpenF1 API is accessible
2. Check network connectivity from Leapcell
3. Ensure caching doesn't prevent fresh data
4. Test with actual F1 session data

### Deployment Fails
1. Check all dependencies in requirements.txt
2. Verify port configuration in leapcell.yaml
3. Ensure environment variables are set
4. Review build logs for compilation errors

## Post-Deployment Steps

### 1. Configure Telegram Webhook
1. Get your Leapcell app URL
2. Set webhook using BotFather: `https://api.telegram.org/bot<TOKEN>/setWebhook?url=<APP_URL>/webhook`
3. Verify webhook is set: `https://api.telegram.org/bot<TOKEN>/getWebhookInfo`

### 2. Functional Testing
1. Send `/start` command to bot
2. Test all menu options
3. Verify live timing during F1 session
4. Check error handling

### 3. Monitoring
1. Set up log monitoring in Leapcell
2. Monitor health check endpoint
3. Watch for any runtime errors
4. Test during actual F1 events

## Performance Validation

### Response Times
- API calls should complete within 15 seconds
- Country flag lookups should be instant
- Cache hits should be under 100ms

### Resource Usage
- Memory usage should be stable
- CPU usage should be low when idle
- Network requests should be minimal

## Leapcell-Specific Considerations

### Cold Start Optimization
- Bot initializes on startup for faster responses
- Caching reduces API calls during high traffic
- Efficient error handling prevents unnecessary processing

### Environment Variables
- All sensitive data stored in environment variables
- No hardcoded tokens or secrets
- Fallback environment loading from .env file

### Logging
- Optimized for serverless logging limits
- WARNING level to reduce log storage
- Essential information logged for debugging

## Testing During F1 Sessions

### Live Session Testing
1. Check session detection 2 hours before session
2. Verify live positions update every 15-30 seconds
3. Test message formatting with real data
4. Ensure no errors during session updates

### Session End Testing
1. Verify graceful handling when session ends
2. Check caching expiration after session
3. Ensure proper cleanup of session data

## Final Validation

### Pre-Launch Checklist
- [ ] All tests pass (python test_leapcell_deployment.py)
- [ ] Bot responds to basic commands
- [ ] Health endpoint accessible
- [ ] Environment variables configured
- [ ] Webhook properly set
- [ ] Logs show no critical errors

### Success Criteria
- Bot responds to all commands
- Live timing works during F1 sessions
- No critical errors in logs
- Health check passes consistently
- Performance meets expectations

---

**Deployment Status**: Ready for Leapcell deployment after completing all checklist items.
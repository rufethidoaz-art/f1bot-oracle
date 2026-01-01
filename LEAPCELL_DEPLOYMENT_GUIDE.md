# F1 Bot - Leapcell Deployment Guide

## Quick Fix Summary

The 500 INTERNAL SERVER ERROR you're experiencing is likely due to:

1. **Bot initialization timing issues** - Fixed in the updated webhook handler
2. **Missing environment variables** - Ensure your bot token is properly set
3. **Deployment configuration** - Updated leapcell.yaml for better compatibility

## Updated leapcell.yaml

Replace your current `leapcell.yaml` with this optimized version:

```yaml
# F1 Bot Leapcell Configuration - Optimized
runtime: python
build_command: pip install -r requirements.txt
start_command: gunicorn -w 1 -b :8080 app:app
port: 8080

# Environment variables (set these in Leapcell dashboard)
env:
  TELEGRAM_BOT_TOKEN: your_bot_token_here
  PORT: 8080

# Health check configuration
health_check:
  path: /health
  interval: 30
  timeout: 10
  retries: 3

# Resource configuration
resources:
  cpu: 0.5
  memory: 512
```

## Step-by-Step Deployment

### 1. Prepare Your Environment

1. **Get your bot token** from [@BotFather](https://t.me/BotFather) on Telegram
2. **Set up webhook** using this command:
   ```bash
   curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook" \
   -H "Content-Type: application/json" \
   -d '{"url": "https://your-app.leapcell.io/webhook"}'
   ```

### 2. Configure Leapcell

1. **Upload your project files** to Leapcell
2. **Set environment variables** in Leapcell dashboard:
   - `TELEGRAM_BOT_TOKEN`: Your bot token
   - `PORT`: 8080 (or your preferred port)

3. **Use the updated leapcell.yaml** above

### 3. Test Your Deployment

1. **Check health endpoint**: Visit `https://your-app.leapcell.io/health`
2. **Test webhook**: Send a test POST request to `/webhook`
3. **Test in Telegram**: Send `/start` to your bot

## Common Issues and Solutions

### Issue: 500 Error on Webhook

**Cause**: Bot not initialized or missing token
**Solution**: 
- Check that `TELEGRAM_BOT_TOKEN` is set correctly
- Verify bot initialization in logs
- Test with `/health` endpoint first

### Issue: Bot Not Responding

**Cause**: Webhook not set or incorrect URL
**Solution**:
- Verify webhook URL is correct
- Check that your app is accessible from internet
- Ensure HTTPS is used (required by Telegram)

### Issue: Slow Response Times

**Cause**: Cold starts or resource limits
**Solution**:
- Increase memory allocation in Leapcell
- Add health check pings to keep app warm
- Optimize bot initialization

## Testing Commands

### Test Webhook Locally
```bash
# Test with curl
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{"update_id":123456789,"message":{"message_id":1,"from":{"id":123456789,"is_bot":false,"first_name":"Test","username":"testuser"},"chat":{"id":123456789,"first_name":"Test","username":"testuser","type":"private"},"date":1234567890,"text":"/start"}}'
```

### Test in Telegram
1. Send `/start` to your bot
2. Send `/menu` to test button responses
3. Send `/standings` to test API calls

## Monitoring and Debugging

### Check Logs
- View logs in Leapcell dashboard
- Look for "Bot initialized successfully" message
- Check for any error messages during webhook processing

### Health Monitoring
- Use `/health` endpoint to check status
- Use `/logs` endpoint for debug information
- Monitor response times and error rates

## Performance Optimization

### For Better Performance:
1. **Enable caching** for API responses
2. **Use async/await** properly (already implemented)
3. **Monitor resource usage** in Leapcell dashboard
4. **Set up health checks** to keep app warm

### Resource Recommendations:
- **CPU**: 0.5-1 core
- **Memory**: 512MB-1GB
- **Storage**: 100MB (for logs and temporary files)

## Troubleshooting Checklist

- [ ] Bot token is set correctly in environment variables
- [ ] Webhook is configured with correct URL
- [ ] App is accessible from internet (test with curl)
- [ ] Health endpoint returns success
- [ ] No syntax errors in Python code
- [ ] All dependencies are in requirements.txt
- [ ] leapcell.yaml is properly configured
- [ ] Logs show successful bot initialization

## Support

If you continue to experience issues:

1. Check the logs in Leapcell dashboard
2. Test each component individually
3. Verify your bot token works with other tools
4. Ensure your webhook URL is accessible
5. Check that all required files are uploaded to Leapcell

## Next Steps

After successful deployment:
1. Set up monitoring for uptime
2. Configure alerts for errors
3. Optimize performance based on usage patterns
4. Consider adding caching for frequently accessed data
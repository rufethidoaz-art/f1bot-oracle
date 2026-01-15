#!/bin/bash

# Check if TELEGRAM_BOT_TOKEN is set
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "Error: TELEGRAM_BOT_TOKEN is not set."
    echo "Please export it: export TELEGRAM_BOT_TOKEN='your_token_here'"
    exit 1
fi

echo "Starting localhost.run tunnel..."

# Start SSH tunnel in background and capture output
# We use stdbuf to unbuffer output so we can grep it immediately
rm -f nohup.out
nohup ssh -o StrictHostKeyChecking=no -R 80:localhost:8443 nokey@localhost.run > nohup.out 2>&1 &
TUNNEL_PID=$!

echo "Tunnel process started with PID $TUNNEL_PID. Waiting for URL..."

# Loop to extract URL from log file
MAX_RETRIES=30
COUNT=0
WEBHOOK_URL=""

while [ $COUNT -lt $MAX_RETRIES ]; do
    if grep -q "tunneled with tls" nohup.out; then
        # Extract URL: it's usually the last word on the line containing "tunneled with tls"
        # Example line: "your-subdomain.localhost.run tunneled with tls change https://your-subdomain.localhost.run"
        WEBHOOK_URL=$(grep "tunneled with tls" nohup.out | head -n 1 | awk '{print $NF}')
        break
    fi
    sleep 1
    COUNT=$((COUNT+1))
    echo -n "."
done

echo ""

if [ -z "$WEBHOOK_URL" ]; then
    echo "Failed to get webhook URL from localhost.run. Check nohup.out:"
    cat nohup.out
    kill $TUNNEL_PID
    exit 1
fi

echo "Webhook URL obtained: $WEBHOOK_URL"

# Export for python script
export WEBHOOK_URL=$WEBHOOK_URL
export PORT=8443

# Run the bot
echo "Starting Python bot..."
python3 run_webhook.py

# Cleanup on exit
kill $TUNNEL_PID

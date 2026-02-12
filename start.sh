#!/bin/bash
set -e

echo "========================================"
echo "ILECO-1 Chatbot Starting..."
echo "========================================"

# Start Rasa Actions Server in background
echo "Starting Actions Server..."
rasa run actions --port 5055 > /tmp/actions.log 2>&1 &
ACTION_PID=$!

# Wait for actions server
sleep 8

# Start Rasa Server in background
echo "Starting Rasa Server (this takes 2-3 minutes)..."
rasa run \
    --enable-api \
    --cors "*" \
    --port 5000 \
    --debug > /tmp/rasa.log 2>&1 &
RASA_PID=$!

# Wait for Rasa to be ready
echo "Waiting for Rasa to become ready..."
for i in {1..180}; do
    if curl -s http://localhost:5000/ > /dev/null 2>&1; then
        echo "✓ Rasa server is ready!"
        break
    fi
    if [ $i -eq 180 ]; then
        echo "ERROR: Rasa failed to start after 3 minutes"
        cat /tmp/rasa.log
        exit 1
    fi
    sleep 1
    if [ $((i % 10)) -eq 0 ]; then
        echo "Still waiting... ($i seconds)"
    fi
done

# Keep the container running by tailing logs
echo "========================================"
echo "Server is UP and ready for requests!"
echo "Actions Server: http://0.0.0.0:5055"
echo "Rasa Server: http://0.0.0.0:5000"
echo "========================================"

tail -f /tmp/rasa.log /tmp/actions.log
#!/bin/bash
set -e

echo "========================================"
echo "MINIMAL TEST MODE - ILECO-1 Chatbot"
echo "========================================"
echo "Main App Port: 5000"
echo "Action Server Port: 5055"
echo "Working Directory: $(pwd)"
echo "========================================"

# Start Rasa Actions Server in the background
echo "Starting Rasa Actions Server on port 5055..."
rasa run actions --port 5055 &
ACTION_PID=$!

# Wait for actions server to be ready
echo "Waiting for actions server to initialize..."
sleep 10

# Check if actions server is running
if ! kill -0 $ACTION_PID 2>/dev/null; then
    echo "ERROR: Actions server failed to start"
    exit 1
fi

echo "✓ Actions server started successfully on port 5055 (PID: $ACTION_PID)"

# Start Rasa Server on port 5000
echo "Starting Rasa Server on port 5000..."
exec rasa run \
    --enable-api \
    --cors "*" \
    --port 5000 \
    --debug
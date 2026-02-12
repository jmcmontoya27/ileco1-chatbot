#!/bin/bash

echo "========================================"
echo "MINIMAL TEST MODE - ILECO-1 Chatbot"
echo "========================================"
echo "WARNING: Running in low-memory mode"
echo "This is for TESTING ONLY"
echo "========================================"

# Use environment variables or defaults
PORT=${PORT:-5000}
ACTION_SERVER_PORT=${ACTION_SERVER_PORT:-5055}

echo "Main App Port: $PORT"
echo "Action Server Port: $ACTION_SERVER_PORT"
echo "Working Directory: $(pwd)"

# List files for debugging
echo "Files in current directory:"
ls -lah

# Verify required files exist
if [ ! -f "config.yml" ]; then
    echo "ERROR: config.yml not found!"
    exit 1
fi

if [ ! -f "domain.yml" ]; then
    echo "ERROR: domain.yml not found!"
    exit 1
fi

if [ ! -f "endpoints.yml" ]; then
    echo "ERROR: endpoints.yml not found!"
    exit 1
fi

if [ ! -f "credentials.yml" ]; then
    echo "ERROR: credentials.yml not found!"
    exit 1
fi

# Start Actions Server in background
echo "Starting Rasa Actions Server on port $ACTION_SERVER_PORT..."
python -m rasa_sdk --actions actions --port $ACTION_SERVER_PORT &
ACTION_PID=$!

# Wait for actions server to initialize
echo "Waiting for actions server to initialize..."
sleep 10

# Verify actions server is running
if ps -p $ACTION_PID > /dev/null; then
    echo "✓ Actions server started successfully (PID: $ACTION_PID)"
else
    echo "✗ ERROR: Actions server failed to start!"
    exit 1
fi

# Start Rasa Server with minimal memory footprint
echo "Starting Rasa Server on port $PORT..."
exec rasa run \
    --port $PORT \
    --enable-api \
    --cors "*" \
    --endpoints endpoints.yml \
    --credentials credentials.yml \
    --log-level warning
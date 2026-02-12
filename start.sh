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
for f in config.yml domain.yml endpoints.yml credentials.yml; do
    if [ ! -f "$f" ]; then
        echo "ERROR: $f not found!"
        exit 1
    fi
done

# Start Actions Server in background
echo "Starting Rasa Actions Server on port $ACTION_SERVER_PORT..."
python -m rasa_sdk --actions actions --port $ACTION_SERVER_PORT &
ACTION_PID=$!

# Wait for actions server to become available on its port
echo "Waiting for actions server to initialize..."
MAX_WAIT=30
COUNT=0
until (echo > /dev/tcp/localhost/$ACTION_SERVER_PORT) 2>/dev/null; do
    # Also check if the background process died unexpectedly
    if ! kill -0 $ACTION_PID 2>/dev/null; then
        echo "✗ ERROR: Actions server process exited unexpectedly!"
        exit 1
    fi
    sleep 1
    COUNT=$((COUNT + 1))
    if [ $COUNT -ge $MAX_WAIT ]; then
        echo "✗ ERROR: Actions server failed to start within ${MAX_WAIT}s!"
        kill $ACTION_PID 2>/dev/null
        exit 1
    fi
done

echo "✓ Actions server started successfully on port $ACTION_SERVER_PORT (PID: $ACTION_PID)"

# Start Rasa Server with minimal memory footprint
echo "Starting Rasa Server on port $PORT..."
exec rasa run \
    --port $PORT \
    --enable-api \
    --cors "*" \
    --endpoints endpoints.yml \
    --credentials credentials.yml \
    --log-level warning
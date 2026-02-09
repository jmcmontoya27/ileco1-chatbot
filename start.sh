#!/bin/bash
set -e

echo "========================================"
echo "Starting ILECO-1 Chatbot on Railway"
echo "========================================"

# NO virtual environment activation needed in Docker!
# Railway runs in a containerized environment

# Set default port if not provided by Railway
export PORT=${PORT:-5000}
export ACTION_PORT=5055

echo "Main App Port: $PORT"
echo "Action Server Port: $ACTION_PORT"
echo "Working Directory: $(pwd)"

# List files for debugging
echo "Files in current directory:"
ls -la

# Check if actions directory exists
if [ -d "actions" ]; then
    echo "✓ Actions directory found"
    ls -la actions/
else
    echo "✗ Actions directory NOT found!"
fi

# Start Rasa Actions Server in background
echo "Starting Rasa Actions Server on port $ACTION_PORT..."
python -m rasa_sdk --actions actions --port $ACTION_PORT &

# Wait a moment for actions server to start
sleep 3

# Start main Rasa server on Railway's assigned PORT
echo "Starting Rasa Server on port $PORT..."
rasa run --port $PORT \
    --enable-api \
    --cors "*" \
    --debug \
    --endpoints endpoints.yml \
    --credentials credentials.yml
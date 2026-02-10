#!/bin/bash
set -e

echo "========================================"
echo "Starting ILECO-1 Chatbot on Railway"
echo "========================================"

export PORT=${PORT:-5000}
export ACTION_PORT=5055

echo "Main App Port: $PORT"
echo "Action Server Port: $ACTION_PORT"
echo "Working Directory: $(pwd)"

# List files for debugging
echo "Files in current directory:"
ls -la

# Substitute DATABASE_URL in endpoints.yml
echo "Substituting environment variables in endpoints.yml..."
envsubst < rasa/endpoints.yml > rasa/endpoints_processed.yml

# Start Rasa Actions Server in background
echo "Starting Rasa Actions Server on port $ACTION_PORT..."
python -m rasa_sdk --actions actions.actions --port $ACTION_PORT &

# Wait for actions server to start
echo "Waiting for actions server to initialize..."
sleep 5

# Start main Rasa server with processed endpoints
echo "Starting Rasa Server on port $PORT..."
rasa run --port $PORT \
    --enable-api \
    --cors "*" \
    --endpoints rasa/endpoints_processed.yml \
    --credentials rasa/credentials.yml
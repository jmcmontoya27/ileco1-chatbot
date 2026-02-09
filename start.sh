#!/bin/bash

# Activate virtual environment
source .venv/Scripts/activate

# Run Actions server in background
cd actions
rasa run actions --port 5055 --actions actions --debug &

# Run main Rasa server on Railway's port
cd ..
rasa run --port $PORT --endpoints endpoints.yml --credentials credentials.yml -m models --enable-api --cors "*" --debug

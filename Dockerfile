FROM python:3.10-slim

WORKDIR /app

# Install system dependencies including build tools for Rasa
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    git \
    gettext-base \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .

# CRITICAL FIX: Install PyYAML 6.0.1 (has prebuilt wheels for Python 3.10)
# Then downgrade to compatible version after Rasa installs
RUN pip install --no-cache-dir PyYAML==6.0.1

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Train model only if models directory is empty (fallback)
RUN if [ ! "$(ls -A models 2>/dev/null)" ]; then \
        echo "No model found, training new model..."; \
        rasa train --domain rasa/domain.yml \
                    --config rasa/config.yml \
                    --data rasa/data \
                    --out models; \
    else \
        echo "Using existing model from models/"; \
    fi

# Make start.sh executable
RUN chmod +x start.sh

# Expose both ports
EXPOSE 5000 5055

# Use start.sh as entrypoint
CMD ["./start.sh"]
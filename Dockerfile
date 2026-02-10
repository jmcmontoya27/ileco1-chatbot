FROM python:3.10-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    git \
    gettext-base \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip only
RUN pip install --upgrade pip

# Copy requirements
COPY requirements.txt .

# Let pip resolve all dependencies automatically
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Train model if needed
RUN if [ ! "$(ls -A models 2>/dev/null)" ]; then \
        echo "Training new model..."; \
        rasa train --domain rasa/domain.yml \
                    --config rasa/config.yml \
                    --data rasa/data \
                    --out models; \
    else \
        echo "Using existing model"; \
    fi

# Make start script executable
RUN chmod +x start.sh

EXPOSE 5000 5055

CMD ["./start.sh"]
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

# CRITICAL: Install EXACT versions that work together
# Do NOT use --upgrade on setuptools or it will install v82!
RUN pip install --upgrade pip && \
    pip install "setuptools==69.5.1" "wheel<1.0" "Cython<3.0"

# Copy requirements
COPY requirements.txt .

# Install dependencies with legacy resolver
RUN pip install --no-cache-dir --use-deprecated=legacy-resolver -r requirements.txt

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
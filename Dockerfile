# Use Python 3.9 for better compatibility with TensorFlow and Rasa
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV TF_CPP_MIN_LOG_LEVEL=2
ENV TF_ENABLE_ONEDNN_OPTS=0
ENV PYTHONUNBUFFERED=1
ENV SQLALCHEMY_WARN_20=0
ENV SQLALCHEMY_SILENCE_UBER_WARNING=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    gettext-base \
    libpq-dev \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies with optimized layers
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir tensorflow==2.11.0 && \
    pip install --no-cache-dir SQLAlchemy==1.4.49 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY config.yml domain.yml credentials.yml endpoints.yml /app/
COPY data /app/data
COPY models /app/models
COPY actions /app/actions

# Copy and set permissions for start script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose ports
EXPOSE 5000 5055

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Run the start script
CMD ["/app/start.sh"]
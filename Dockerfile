# Use Python 3.9 instead of 3.10 for better compatibility with TensorFlow and Rasa
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables for TensorFlow
ENV TF_CPP_MIN_LOG_LEVEL=2
ENV TF_ENABLE_ONEDNN_OPTS=0
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    gettext-base \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
# Using TensorFlow 2.11.0 for better stability with Rasa
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

# Run the start script
CMD ["/app/start.sh"]
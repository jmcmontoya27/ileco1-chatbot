FROM python:3.9-slim

WORKDIR /app

# Install system dependencies including build tools for Rasa
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Make start.sh executable
RUN chmod +x start.sh

# Expose both ports
EXPOSE 5000 5055

# Use start.sh as entrypoint
CMD ["./start.sh"]
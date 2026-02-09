FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire actions folder
COPY . .

# Expose port
EXPOSE 5055

# Start the actions server
CMD ["python", "-m", "rasa_sdk", "--actions", "actions", "--port", "5055"]
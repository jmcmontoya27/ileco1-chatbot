FROM rasa/rasa:3.6.20-full

# Set working directory
WORKDIR /app

# Copy Rasa configuration files
COPY domain.yml config.yml credentials.yml endpoints.yml ./
COPY data ./data

# Train model
RUN rasa train --domain domain.yml --data data --out models

# Expose port
EXPOSE 5005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:5005/ || exit 1

# Start Rasa server
CMD ["run", "--enable-api", "--cors", "*", "--port", "5005", "--credentials", "credentials.yml", "--endpoints", "endpoints.yml", "--debug"]
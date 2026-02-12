FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONOPTIMIZE=2 \
    TF_CPP_MIN_LOG_LEVEL=3 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    gettext-base \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

ARG CACHEBUST=1

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir tensorflow==2.12.0 && \
    pip install --no-cache-dir SQLAlchemy==1.4.49 && \
    pip install --no-cache-dir -r requirements.txt

RUN find /usr/local -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local -type f -name '*.pyc' -delete 2>/dev/null || true && \
    find /usr/local -type f -name '*.pyo' -delete 2>/dev/null || true

COPY config.yml domain.yml credentials.yml endpoints.yml /app/
COPY data /app/data
COPY models /app/models
COPY actions /app/actions
COPY start.sh /app/start.sh

RUN chmod +x /app/start.sh

EXPOSE 5000 5055

CMD ["./start.sh"]
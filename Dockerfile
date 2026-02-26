# Cloud Service Selection System - production image
FROM python:3.11-slim

# Prevent Python from writing pyc and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY frontend/ ./frontend/
COPY run.py .

# Create non-root user for running the app
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 5001

# Production: gunicorn, 2 workers, bind all interfaces
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5001", "run:app"]

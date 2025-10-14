# Dockerfile for Omni-Revenue-Agent API
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY api/requirements.txt /app/api/requirements.txt
COPY automations/requirements.txt /app/automations/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r api/requirements.txt
RUN pip install --no-cache-dir -r automations/requirements.txt

# Copy application code
COPY api/ /app/api/
COPY automations/ /app/automations/
COPY database/ /app/database/

# Generate Prisma client
WORKDIR /app/database
RUN prisma generate

# Back to app directory
WORKDIR /app

# Expose port
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=api/app.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:5000/health')"

# Run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "api.app:app"]


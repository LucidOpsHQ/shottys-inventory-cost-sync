# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY scrape_markov_inventory.py .
COPY upload_to_postgres.py .
COPY main.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the main script
CMD ["python", "main.py"]

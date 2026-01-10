# Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ .

# Create data directories
RUN mkdir -p /data/db /data/xml /data/deleted /logs

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /data /logs

# Switch to non-root user
USER appuser

# Run scheduler
CMD ["python", "-u", "scheduler.py"]

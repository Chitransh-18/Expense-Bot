FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Set environment variables
ENV PORT=5000
ENV FLASK_ENV=production

# Run database init and start gunicorn
CMD ["sh", "-c", "python database.py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4"]

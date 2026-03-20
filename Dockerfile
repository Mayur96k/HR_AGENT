FROM python:3.11-slim

# System deps for pdfplumber / python-docx
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpoppler-cpp-dev \
        poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Non-root user for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 5000

# Gunicorn for production (threaded to match Flask threaded=True)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", \
     "--timeout", "300", "--access-logfile", "-", "api_server:app"]

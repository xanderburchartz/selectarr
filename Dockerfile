FROM python:3.11-slim

# Create a non-root user for security
RUN useradd -m -u 1000 selectarr

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# The config directory is mounted as a volume at runtime
RUN mkdir -p /config && chown selectarr:selectarr /config

USER selectarr

EXPOSE 8889

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8889/status')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8889"]

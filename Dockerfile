FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=cloud

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ /app/app/

# User should run as non-root
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Run the app
CMD ["python", "-m", "app.main"]

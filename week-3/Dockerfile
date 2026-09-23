# Dockerfile for University Knowledge Assistant
# Uses a clean Python 3.12 slim base image
FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install dependencies
COPY week-3/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code, microservices, and knowledge base data
COPY week-3/app/ ./app/
COPY week-3/services/ ./services/
COPY week-3/data/ ./data/
COPY week-4/data/ ./week-4/data/

# Expose default application gateway port
EXPOSE 8000

# Default entrypoint runs the Application / Gateway service
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

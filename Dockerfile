# Multi-stage build for YouTube Sentiment Analysis App

# ===== Frontend Build Stage =====
FROM node:18 AS frontend-build

WORKDIR /app/frontend

# Copy frontend files
COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ===== Final Stage =====
FROM python:3.9-slim

WORKDIR /app

# Copy backend files
COPY backend/ /app/backend/

# Copy built frontend 
COPY --from=frontend-build /app/frontend/build /app/frontend/build

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    python3-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set up Python environment
WORKDIR /app/backend
RUN pip install --no-cache-dir scikit-learn pandas nltk joblib flask flask-cors gunicorn

# Install nginx for serving frontend
RUN apt-get update && \
    apt-get install -y --no-install-recommends nginx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configure nginx
COPY nginx.conf /etc/nginx/sites-available/default

# Create directory for scraper output
RUN mkdir -p /app/backend/scraper/output
RUN mkdir -p /app/backend/sentiment_analysis/models

# Copy startup script
COPY startup.sh /app/
RUN chmod +x /app/startup.sh

# Healthcheck to verify the service is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:5000/api/status || exit 1

EXPOSE 80

# Start both frontend and backend
CMD ["/app/startup.sh"]

# Weaver Service Dockerfile
# ML inference worker for virtual try-on processing

FROM python:3.11-slim AS base

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for OpenCV and ML libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY weaver_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the weaver service package
COPY common/ /app/common/
COPY weaver_service/ /app/weaver_service/

# Create directory for model downloads
RUN mkdir -p /app/models

# Set Python path to allow imports
ENV PYTHONPATH=/app

# Run the worker
CMD ["python", "-m", "weaver_service.main"]

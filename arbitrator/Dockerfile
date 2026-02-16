# Arbitrator Dockerfile
# Meta-scheduler: adjusts batch_size from queue depth

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install Python dependencies
COPY arbitrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy common and arbitrator packages
COPY common/ /app/common/
COPY arbitrator/ /app/arbitrator/

ENV PYTHONPATH=/app

CMD ["python", "-m", "arbitrator.main"]

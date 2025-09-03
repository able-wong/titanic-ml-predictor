# Multi-stage build for optimized production image
FROM python:3.11-slim AS builder

# Set build environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build dependencies for psutil and other compiled packages
RUN apt-get update && apt-get install -y gcc python3-dev && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy production requirements and install dependencies
COPY requirements-prod.txt .
RUN pip install --no-cache-dir --user -r requirements-prod.txt

# Production stage - minimal runtime image
FROM python:3.11-slim AS production

# Set production environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ML_SERVICE_ENVIRONMENT=production
ENV ML_SERVICE_HOST=0.0.0.0
ENV PORT=8080
ENV PATH=/home/app/.local/bin:$PATH

# JWT keys will be provided via environment variables:
# JWT_PRIVATE_KEY and JWT_PUBLIC_KEY
# These should be set during deployment, not in the Dockerfile

# Install tini for proper signal handling and update system packages
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y tini \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/app/.local

# Copy all necessary components to match project structure
COPY --chown=app:app models/ /models/
COPY --chown=app:app shared/ /shared/
COPY --chown=app:app 2-ml-service/ ./

# Switch to non-root user
USER app

# Set PATH to include user-local binaries and PYTHONPATH for proper imports
ENV PATH="/home/app/.local/bin:$PATH"
ENV PYTHONPATH="/app:/shared:/models"

# Expose ports for both Firebase Functions and direct Docker usage
EXPOSE 8080 8000

# Use tini as PID 1 for proper signal handling
ENTRYPOINT ["tini", "--"]

# Start FastAPI application directly
CMD ["python", "main.py"]
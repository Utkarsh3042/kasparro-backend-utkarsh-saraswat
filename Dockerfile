# Multi-stage build for optimized production image
# Crypto ETL Backend System v2.0.0
# Supports: SQLAlchemy ORM, PostgreSQL/SQLite, Rate Limiting, Circuit Breaker

# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/data /app/logs && \
    chown -R appuser:appuser /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Ensure data directory exists with correct permissions
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data

# Make PATH include user-installed packages
ENV PATH=/root/.local/bin:$PATH

# Environment variables (can be overridden)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATABASE_URL=sqlite:///./data/crypto_data.db \
    AUTO_INGEST_ON_STARTUP=true \
    AUTO_INGEST_SOURCES=csv,coingecko,coinpaprika \
    LOG_LEVEL=INFO \
    COINGECKO_API_URL=https://api.coingecko.com/api/v3 \
    COINPAPRIKA_API_URL=https://api.coinpaprika.com/v1

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command with optimized workers
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
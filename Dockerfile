# Multi-stage Dockerfile for CoralCollective
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1000 coral && \
    useradd --uid 1000 --gid coral --shell /bin/bash --create-home coral

# Development stage
FROM base as development

WORKDIR /app

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt setup.py ./
COPY coral_collective/__init__.py coral_collective/__init__.py

# Install dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -e .[all]

# Copy source code
COPY . .

# Install in development mode
RUN pip install -e .[all]

# Change ownership to coral user
RUN chown -R coral:coral /app /opt/venv
USER coral

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD python -c "import coral_collective; print('healthy')" || exit 1

CMD ["python", "-m", "coral_collective.cli.main", "--help"]

# Production stage
FROM base as production

WORKDIR /app

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install package
COPY requirements.txt setup.py ./
COPY coral_collective/ coral_collective/
COPY agents/ agents/
COPY config/ config/
COPY templates/ templates/
COPY mcp/configs/ mcp/configs/
# Memory module removed - using project state instead
COPY MANIFEST.in ./

# Install production dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install . && \
    pip install gunicorn[gevent]

# Remove build dependencies
RUN apt-get purge -y build-essential && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* /root/.cache

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/tmp && \
    chown -R coral:coral /app /opt/venv

USER coral

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD python -c "import coral_collective; print('healthy')" || exit 1

EXPOSE 8000

# Default command
CMD ["coral", "--help"]

# Memory-enabled stage for applications requiring vector storage
FROM production as memory

USER root

# Install ChromaDB system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

USER coral

# Install memory dependencies
RUN pip install --no-cache-dir \
    numpy>=1.24.0 \
    scipy>=1.10.0

# Create data directories
RUN mkdir -p /app/data /app/.coral

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD python -c "import coral_collective; print('CoralCollective is healthy')" || exit 1

CMD ["coral", "--help"]
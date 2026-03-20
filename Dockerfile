FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git && rm -rf /var/lib/apt/lists/*

# Copy Python project
COPY pyproject.toml .
COPY agents/ agents/
COPY mcp/ mcp/

# Install Python deps
RUN pip install --no-cache-dir groq fastapi uvicorn mcp web3 eth-account httpx pydantic python-dotenv

# Health check endpoint (FastAPI)
COPY scripts/health_server.py scripts/health_server.py

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "agents/nexus/main.py"]

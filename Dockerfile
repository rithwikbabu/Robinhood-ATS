FROM python:3.12-slim

LABEL org.opencontainers.image.title="Robinhood MCP Bridge" \
      org.opencontainers.image.description="Lean local MCP bridge and Python client for Robinhood Agentic Trading" \
      org.opencontainers.image.source="https://github.com/rithwikbabu/Robinhood-ATS" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STATE_DIR=/state \
    HOST=0.0.0.0 \
    PORT=8080 \
    AUTH_CALLBACK_BIND_HOST=0.0.0.0 \
    AUTH_CALLBACK_PORT=8765 \
    AUTH_REDIRECT_URI=http://127.0.0.1:8765/callback \
    ALLOW_DOCKER_LOOPBACK_BIND=true

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY robinhood_mcp_bridge ./robinhood_mcp_bridge

RUN pip install --no-cache-dir . \
    && useradd --create-home --uid 10001 appuser \
    && mkdir -p /state \
    && chown -R appuser:appuser /state

USER appuser

EXPOSE 8080

ENTRYPOINT ["robinhood-mcp-bridge"]
CMD ["serve"]

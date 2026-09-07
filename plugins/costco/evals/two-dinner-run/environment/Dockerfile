FROM python:3.13-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN git clone https://github.com/walkerhughes/claude.git /opt/claude \
    && git -C /opt/claude checkout main \
    && cd /opt/claude/plugins/costco \
    && uv sync --frozen --no-dev

RUN python -m venv /opt/rewardkit \
    && /opt/rewardkit/bin/pip install --no-cache-dir "harbor-rewardkit==0.1.*" \
    && ln -s /opt/rewardkit/bin/rewardkit /usr/local/bin/rewardkit

COPY mock_server.py start-mcp /opt/eval/
RUN chmod +x /opt/eval/start-mcp

WORKDIR /app
ENV COSTCO_PRODUCT_URL=http://127.0.0.1:8091/graphql \
    COSTCO_SEARCH_URL=http://127.0.0.1:8091/search \
    COSTCO_WAREHOUSE_URL=http://127.0.0.1:8091/warehouses \
    COSTCO_GEOCODE_URL=http://127.0.0.1:8091/geocode

# OpsGate MCP server - container image.
#
# Build context is the repository root, not mcp-server/: opsgate_mcp_server.py imports the
# engine from the sibling tools/ folder (it exits at startup if tools/opsgate.py is not next to
# mcp-server/), reads governance content live from content/**, and persists all state under
# tenants/ and runs/ at the repository root. The whole repo layout is therefore the runtime
# layout, and /app mirrors it one-to-one.
#
#   docker build -t opsgate-mcp .
#   docker run --rm -p 127.0.0.1:8765:8765 \
#     -e OPSGATE_MCP_TOKEN=... -e OPSGATE_MCP_ALLOWED_HOSTS=opsgate.example.com \
#     -v opsgate-tenants:/app/tenants -v opsgate-runs:/app/runs opsgate-mcp
#
# See mcp-server/README.md ("Docker") for the compose-based equivalent and the full list of
# environment variables.

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependencies first, on their own layer, so a code-only change does not reinstall them.
COPY mcp-server/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

# Unprivileged runtime user. tenants/registry.json is chmod'ed to 0600 (and its folder to
# 0700) on every save, so the state directories must be owned by this user - they are created
# here with that ownership so a fresh named volume inherits it on first mount.
RUN groupadd --system --gid 10001 opsgate \
    && useradd --system --uid 10001 --gid opsgate --home-dir /app --no-create-home opsgate

WORKDIR /app
COPY --chown=opsgate:opsgate . /app
RUN mkdir -p /app/tenants /app/runs && chown -R opsgate:opsgate /app/tenants /app/runs

USER opsgate

# Inside a container the server has to listen on all interfaces for the published port to
# reach it; the mcp SDK's DNS-rebinding protection still restricts which Host headers are
# accepted (127.0.0.1/localhost plus OPSGATE_MCP_ALLOWED_HOSTS), so binding 0.0.0.0 here does
# not by itself widen what the server will answer to.
ENV OPSGATE_MCP_HOST=0.0.0.0 \
    OPSGATE_MCP_PORT=8765

EXPOSE 8765

# /health is unauthenticated by design and also confirms tenants/registry.json parses, so a
# corrupted registry shows up as an unhealthy container, not just a process that answers HTTP.
# python:slim ships no curl/wget, hence the urllib one-liner.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=4).status == 200 else 1)"

VOLUME ["/app/tenants", "/app/runs"]

CMD ["python", "mcp-server/opsgate_mcp_server.py"]

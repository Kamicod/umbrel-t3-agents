# Sellbird (https://github.com/ethanplusai/sellbird, AGPL-3.0) packaged for Umbrel.
#
# The upstream source is used unmodified. Two things differ from upstream's
# own Dockerfile:
#   - state lives in /data (SELLBIRD_HOME) instead of a bind-mounted checkout;
#   - a small Caddy proxy listens on 8080 in front of the dashboard, because
#     the dashboard itself only listens on, and only answers to, 127.0.0.1:5555.
FROM caddy:2 AS caddy

FROM python:3.12-slim

# Upstream commit to build. v0.4.0 has no SELLBIRD_HOME support, so this pins
# the first main commit checked that does.
ARG SELLBIRD_REF=25ec83978b21d16ae20779d09bfea113f37f0ef8

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PYTHONPATH=/app \
    SELLBIRD_HOME=/data \
    DISABLE_AUTOUPDATER=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# The whole checkout stays in /app (pyproject.toml included) so Sellbird
# recognises it as its source of default files and seeds /data from it.
RUN curl -fsSL "https://github.com/ethanplusai/sellbird/archive/${SELLBIRD_REF}.tar.gz" -o /tmp/sellbird.tar.gz \
    && tar -xzf /tmp/sellbird.tar.gz --strip-components=1 -C /app \
    && rm -rf /tmp/sellbird.tar.gz /app/tests /app/.github \
    && test -f /app/pyproject.toml && test -f /app/sellbird/__init__.py

RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/* /root/.cache

# uid 1000 matches Umbrel's app-data owner.
RUN groupadd --gid 1000 sellbird \
    && useradd --create-home --uid 1000 --gid 1000 sellbird \
    && mkdir -p /data \
    && chown -R sellbird:sellbird /app /data /ms-playwright

COPY --from=caddy /usr/bin/caddy /usr/local/bin/caddy
COPY Caddyfile /etc/caddy/Caddyfile
COPY --chmod=755 entrypoint /usr/local/bin/sellbird-entrypoint
RUN caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile

USER sellbird
ENV PATH="/home/sellbird/.local/bin:${PATH}"

# Claude Code CLI, installed as the runtime user. Sellbird's own check fails
# the build if the CLI lacks the isolation flags it needs.
RUN installer="$(mktemp)" \
    && curl -fsSL https://claude.ai/install.sh -o "$installer" \
    && bash "$installer" \
    && rm "$installer" \
    && python -c "from sellbird.claude_runtime import check_cli; print(check_cli())"

EXPOSE 8080

# Goes through the proxy, so it fails if either Caddy or the dashboard is down.
HEALTHCHECK --interval=1m --timeout=10s --start-period=1m --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/instance', timeout=5).close()"

ENTRYPOINT ["sellbird-entrypoint"]
CMD ["dashboard"]

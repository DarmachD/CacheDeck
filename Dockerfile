FROM python:3.13-slim-trixie

LABEL org.opencontainers.image.title="CacheDeck" \
      org.opencontainers.image.description="Structured LANCache prefill control plane" \
      org.opencontainers.image.source="https://github.com/DarmachD/CacheDeck" \
      org.opencontainers.image.licenses="MIT"

ARG VERSION=""
ARG STEAMPREFILL_VERSION="3.6.1"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CACHEDECK_PROVIDER=embedded-steam \
    CACHEDECK_STEAM_ENGINE_VERSION=${STEAMPREFILL_VERSION} \
    TARGET_CONTAINER=LANCache-Prefill \
    CACHEDECK_CONFIG_DIR=/config \
    CACHEDECK_VERSION=${VERSION} \
    PORT=8080

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        docker-cli \
        libicu76 \
        tini \
        unzip \
    && mkdir -p /opt/steamprefill \
    && curl --fail --location --retry 4 --retry-delay 2 \
        "https://github.com/tpill90/steam-lancache-prefill/releases/download/v${STEAMPREFILL_VERSION}/SteamPrefill-${STEAMPREFILL_VERSION}-linux-x64.zip" \
        --output /tmp/steamprefill.zip \
    && unzip -j /tmp/steamprefill.zip -d /opt/steamprefill \
    && chmod 0755 /opt/steamprefill/SteamPrefill \
    && /opt/steamprefill/SteamPrefill --version \
    && rm -f /tmp/steamprefill.zip \
    && apt-get purge -y --auto-remove curl unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt VERSION ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY entrypoint.sh /usr/local/bin/cachedeck-entrypoint
RUN chmod 0755 /usr/local/bin/cachedeck-entrypoint

EXPOSE 8080
VOLUME ["/config"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health', timeout=3)"

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/cachedeck-entrypoint"]

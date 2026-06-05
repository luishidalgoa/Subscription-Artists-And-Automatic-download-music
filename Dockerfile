FROM python:3.11-slim

# ---- sistema base ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    tzdata \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# ---- yt-dlp ----
# Es mejor dejar que pip lo gestione para que las dependencias de Python
# que yt-dlp pueda necesitar estén presentes.
RUN pip install --no-cache-dir -U yt-dlp

# ---- usuario no root ----
RUN useradd -u 1000 -m luish
WORKDIR /Workspace

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir -e .

# Aseguramos que el usuario luish tenga acceso a todo
RUN chown -R luish:luish /Workspace

# ---- metadatos de versión (inyectados por CI; ver .github/workflows/docker-publish.yml) ----
# Se declaran al final a propósito: APP_COMMIT/APP_BUILD_TIME cambian en cada build,
# así no invalidan la caché de las capas pesadas (apt, pip) que van arriba.
ARG APP_VERSION=dev
ARG APP_COMMIT=unknown
ARG APP_BUILD_TIME=unknown
ENV APP_VERSION=${APP_VERSION} \
    APP_COMMIT=${APP_COMMIT} \
    APP_BUILD_TIME=${APP_BUILD_TIME}
LABEL org.opencontainers.image.title="yt-subs" \
      org.opencontainers.image.description="Suscripción a artistas de YouTube/YouTube Music y descarga automática de sus lanzamientos" \
      org.opencontainers.image.source="https://github.com/luishidalgoa/Subscription-Artists-And-Automatic-download-music" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.revision="${APP_COMMIT}"

USER 1000:1000
ENV YT_COMMAND="boot"
CMD ["sh", "-c", "yt-subs ${YT_COMMAND}"]

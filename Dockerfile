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

USER 1000:1000
ENV YT_COMMAND="boot"
CMD ["sh", "-c", "yt-subs ${YT_COMMAND}"]

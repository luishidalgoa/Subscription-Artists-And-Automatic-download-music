FROM python:3.11-slim

# ---- sistema base ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# ---- yt-dlp (version fija reproducible) ----
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp \
    -o /usr/local/bin/yt-dlp \
    && chmod +x /usr/local/bin/yt-dlp

# ---- usuario no root ----
RUN useradd -u 1000 -m luish

WORKDIR /Workspace

# ---- dependencias Python (cache optimizado) ----
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- código ----
COPY . .
RUN pip install --no-cache-dir -e .

USER 1000:1000

ENV YT_COMMAND="boot"

CMD ["sh", "-c", "yt-subs ${YT_COMMAND}"]
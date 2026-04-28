FROM python:3.11-slim

# Instala dependencias del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    tzdata \
    git \
    nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# Instala yt-dlp (última versión en build)
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp \
    -o /usr/local/bin/yt-dlp \
    && chmod a+rx /usr/local/bin/yt-dlp

# Crear usuario no-root con UID 1000 (igual que tu host)
RUN useradd -u 1000 -m luish

# Directorio de trabajo
WORKDIR /Workspace

# Copia requirements e instala dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código
COPY . .
RUN pip install -e .

# Dar permisos al usuario sobre el workspace
RUN chown -R 1000:1000 /Workspace

# Cambiar a usuario no root
USER 1000:1000

ENV YT_COMMAND="boot"

CMD ["sh", "-c", "yt-subs ${YT_COMMAND}"]
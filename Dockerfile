FROM python:3.11-slim

# Instala ffmpeg y otras dependencias del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    tzdata \
    git \
    nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# Instala yt-dlp
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp \
    && chmod a+rx /usr/local/bin/yt-dlp

# Crea directorio de trabajo
WORKDIR /Workspace

# Copia requirements e instala dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN yt-dlp -U

# Copia el código del proyecto
COPY . .

RUN pip install -e .

ENV YT_COMMAND="boot"

# Comando por defecto (puedes sobreescribirlo)
CMD ["sh", "-c", "yt-subs ${YT_COMMAND}"]


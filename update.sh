#!/bin/bash

# Nombre del servicio/contenedor de tu proyecto
CONTAINER_NAME="yt_subs"

echo "🚀 Deteniendo contenedores..."
docker compose down

echo "📦 Actualizando repositorio..."
git pull

echo "🟢 Levantando contenedores en background..."
docker compose up -d

echo "💻 Conectando al contenedor $CONTAINER_NAME..."
docker exec -it $CONTAINER_NAME /bin/bash


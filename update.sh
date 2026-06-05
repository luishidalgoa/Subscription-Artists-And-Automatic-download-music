#!/bin/bash
# Actualización MANUAL al modelo pull-based.
#
# La imagen la construye CI (GitHub Actions) y se publica en GHCR; en condiciones
# normales el Watchtower del host actualiza el contenedor solo (~5 min). Este script
# fuerza la actualización inmediata: descarga la última :latest y recrea el contenedor.
# Ya NO compila nada en la Pi ni necesita `git pull`.

set -e

CONTAINER_NAME="yt_subs"

echo "📥 Descargando la última imagen desde GHCR..."
docker compose pull

echo "🟢 Recreando el contenedor con la nueva imagen..."
docker compose up -d

echo "🧹 Limpiando imágenes antiguas..."
docker image prune -f

echo "✅ Listo. Mostrando logs (Ctrl+C para salir)..."
docker logs -f "$CONTAINER_NAME"

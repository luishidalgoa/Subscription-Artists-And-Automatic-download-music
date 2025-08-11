# Índice

1. [🎵 Introducción](#-introducción)  
2. [📂 Estructura del Proyecto](#-estructura-del-proyecto)  
3. [⚙️ Puesta en Marcha](#-puesta-en-marcha)  
   3.1. [Clonar el repositorio](#1-clonar-el-repositorio)  
   3.2. [Crear entorno de configuración](#2-crear-entorno-de-configuración)  
      3.2.1. [Artists.json](#21-artistsjson)  
      3.2.2. [last_run.json](#22-last_runjson)  
      3.2.3. [Cookies](#23-cookies) 
   3.3. [Variables de entorno (`.env`)](#3-variables-de-entorno-env)  
4. [🐳 Ejecución con Docker](#-ejecución-con-docker)  
   4.1. [Construir y levantar el servicio](#1-construir-y-levantar-el-servicio)  
   4.2. [Volúmenes](#2-volúmenes)  
5. [🖥️ Ejecución local (sin Docker)](#️-ejecución-local-sin-docker)  
   5.1. [Instalar dependencias del sistema](#1-instalar-dependencias-del-sistema)  
   5.2. [Instalar dependencias Python](#2-instalar-dependencias-python)  
   5.3. [Instalar yt-dlp](#3-instalar-yt-dlp)  
   5.4. [Ejecutar el servicio](#4-ejecutar-el-servicio)  
6. [🔧 Configuraciones Manuales](#-configuraciones-manuales)  
7. [📦 Funcionalidad Interna](#-funcionalidad-interna)  
   7.1. [Descarga](#1-descarga)  
   7.2. [Postprocesado](#2-postprocesado)  
   7.3. [Registro de ejecución](#3-registro-de-ejecución)  
8. [🚀 Despliegue](#-despliegue)  
9. [📜 Licencia](#-licencia)  



# 🎵 Music Channel Auto Downloader

Sistema automatizado para **suscribirse a canales de música** (YouTube / YouTube Music) y **descargar sus últimos lanzamientos** en formato MP3, con metadatos y portadas actualizadas desde la API de Deezer.

El servicio:
- Lee una lista de artistas desde `artists.json`.
- Descarga solo los lanzamientos posteriores a la última ejecución.
- Organiza la música en carpetas por artista y álbum.
- Elimina versiones *preview* y renombra las pistas con índices ordenados.
- Sustituye la portada del álbum por la mejor versión encontrada en Deezer.
- Se ejecuta automáticamente en intervalos configurables.

---

## 📂 Estructura del Proyecto

````
app/
 ├── main.py                  # Punto de entrada del servicio
 ├── config.py                # Configuración y variables de entorno
 ├── controller/
 │    └── download_controller.py  # Orquestador principal de descargas
 ├── service/
 │    └── download_service.py     # Procesamiento post-descarga
 ├── utils/
 │    └── audio_utils.py          # Extracción de metadatos y portadas
 └── ...
config/
 ├── artists.json             # Lista de artistas y URLs de canal
 └── last_run.json            # Registro de última ejecución por artista
Dockerfile
docker-compose.yml
requirements.txt
````

---

## ⚙️ Puesta en Marcha

### 1. Clonar el repositorio
````
git clone https://github.com/tuusuario/yt-music-downloader.git
cd yt-music-downloader
````

### 2. Crear entorno de configuración

#### 2.1 Artists.json
En la carpeta **config/** crea el archivo **artists.json**:
````
[
  {
    "name": "Myke Towers",
    "channel_url": "https://www.youtube.com/channel/UCLk8IJ1TwI7Xl7UUfAD8xPQ"
  }
]
````

#### 2.2 last_run.json
En la carpeta **config/** crea el archivo **last_run.json**:  
> El archivo **last_run.json** describe la última vez que se comprobaron cambios en el artista.  
> ⚠️ La key debe ser el mismo string que el campo "name" del artista en **artists.json**  

````
{
  "Myke Towers": "2020-01-09T08:31:22"
}
````

#### 2.3 Archivo de cookies
En la carpeta **config/** encontrarás el archivo de ejemplo **_cookies.example.txt**.  
Para activar la autenticación y evitar bloqueos de YouTube:  
1. Exporta tus cookies desde tu navegador.  
2. Sustituye el contenido de **_cookies.example.txt** por tus cookies reales.  
3. **Renombra el archivo a _cookies.txt** para que el sistema lo utilice durante las descargas.  

> Para exportar las cookies se recomienda usar extensiones como:   
> - [Export Cookies](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) para Chrome

> ⚠️ Si no se renombra a **_cookies.txt**, el sistema no aplicará las cookies y podría fallar con contenido restringido.

### 3. Variables de entorno (`.env`)
Ejemplo:
````
# Ruta donde se guardará la música descargada
ROOT_PATH=/music

# Ruta de configuración
CONFIG_PATH=./config

# Intervalo de ejecución del scheduler en días
SCHEDULE_INTERVAL_DAYS=5
````

---

## 🐳 Ejecución con Docker

### 1. Construir y levantar el servicio
````
docker compose up -d --build
````

### 2. Volúmenes
- `./output:/music` → Carpeta local donde se guardan las descargas.
- `./config:/app/config` → Configuración persistente (`artists.json`, `last_run.json`).
- `./app:/app/app` → Código fuente para desarrollo.

---

## 🖥️ Ejecución local (sin Docker)

1. Instalar dependencias del sistema:
````
sudo apt update && sudo apt install ffmpeg python3 python3-pip
````

2. Instalar dependencias Python:
````
pip install -r requirements.txt
````

3. Instalar yt-dlp:
````
python -m pip install -U yt-dlp
````

4. Ejecutar:
````
python -m app.main
````

---

## 🔧 Configuraciones Manuales

- **artists.json** → Lista de artistas y sus URLs de canal.
- **SCHEDULE_INTERVAL_DAYS** → Intervalo de revisiones automáticas.
- **Portadas** → El sistema intentará reemplazar automáticamente la portada de cada álbum usando la API de Deezer.
- **Rutas** → `ROOT_PATH` y `CONFIG_PATH` deben apuntar a carpetas con permisos de escritura.

---

## 📦 Funcionalidad Interna

1. **Descarga**  
   Usa `yt-dlp` con filtros de fecha (`--dateafter`) para bajar solo lo nuevo.
   
2. **Postprocesado**  
   - `mover_a_albumes` → Agrupa pistas por álbum.
   - `eliminar_previews` → Elimina pistas de prueba.
   - `renombrar_con_indice_en` → Añade índice ordenado a los nombres.
   - `actualizar_portada` → Reemplaza portada con la obtenida desde Deezer.

3. **Registro de ejecución**  
   Guarda en `last_run.json` la fecha de última descarga por artista para no repetir.

---

## 🚀 Despliegue

- **Producción en Docker** → Montar volúmenes persistentes y configurar `.env` según el entorno.
- **Logs** → Se registran en la salida estándar; se recomienda usar `docker logs -f yt-music-downloader` para seguimiento.
- **Actualización** → `docker compose pull && docker compose up -d --build`.

---

## 📜 Licencia
Este proyecto se distribuye bajo la licencia MIT.  

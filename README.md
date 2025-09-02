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
Usamos un tipo de arquitectura Onion (Capas):

````
├── 📁 .git/ 🚫 (auto-hidden)
├── 📁 config/
│   ├── 🔒 .env 🚫 (auto-hidden)
│   ├── 📄 _cookies.example.txt
│   ├── 📄 _cookies.txt 🚫 (auto-hidden)
│   ├── 📄 artists.json 🚫 (auto-hidden)
│   ├── 📄 last_run.json 🚫 (auto-hidden)
│   └── 📄 metadata_songs_cache.json 🚫 (auto-hidden)
├── 📁 data/
│   └── 🗄️ db.sqlite
├── 📁 output/
│   ├── 📁 Aitana/
│   ├── 📁 Jerry Di/
│   │   ├── 📁 ASILO COLLECTIONS VOL I - Negación/
│   │   ├── 📁 ASILO COLLECTIONS VOL II - Ira/
│   │   ├── 📁 ASILO COLLECTIONS VOL III - Negociación/
│   │   ├── 📁 ASILO COLLECTIONS VOL IV - Depresión/
│   │   ├── 📁 ASILO COLLECTIONS VOL V - Aceptación/
│   │   ├── 📁 Acelera/
│   │   ├── 📁 Adicto A Tus Sábanas/
│   │   ├── 📁 Amigos/
│   │   ├── 📁 BAD DECISIONS/
│   │   ├── 📁 Bonita (Remix)/
│   │   ├── 📁 Buscarte/
│   │   ├── 📁 CARACAS EN EL 2000/
│   │   ├── 📁 Confuzio/
│   │   ├── 📁 Cuando/
│   │   ├── 📁 Culito Nuevo/
│   │   ├── 📁 Culito Nuevo 2/
│   │   ├── 📁 DI LETRA/
│   │   ├── 📁 EN SOLEDAD/
│   │   ├── 📁 El Diablo/
│   │   ├── 📁 Hechizo/
│   │   ├── 📁 Hechizo (Remix)/
│   │   ├── 📁 Indica/
│   │   ├── 📁 Inolvidable/
│   │   ├── 📁 Invierno en Caracas/
│   │   ├── 📁 Katana/
│   │   ├── 📁 Ke onda mami/
│   │   ├── 📁 La Fama/
│   │   ├── 📁 La Mentalidad/
│   │   ├── 📁 Llorarás/
│   │   ├── 📁 Luna Llena/
│   │   ├── 📁 Mi Cuarto 2/
│   │   ├── 📁 Mortificado/
│   │   ├── 📁 OBSESIONADO/
│   │   ├── 📁 Obra De Arte/
│   │   ├── 📁 Papi Cachondo/
│   │   ├── 📁 Pirata/
│   │   ├── 📁 Playita/
│   │   ├── 📁 Ponme En Tu Boca/
│   │   ├── 📁 Por Ella/
│   │   ├── 📁 Que Fluya (Remix)/
│   │   ├── 📁 Serendipia/
│   │   ├── 📁 Shorty/
│   │   ├── 📁 Si Biri Bop/
│   │   ├── 📁 Si Supieras/
│   │   ├── 📁 Siempre Soy Yo/
│   │   ├── 📁 Sinceros/
│   │   ├── 📁 Sé que tú quieres verme llorar/
│   │   ├── 📁 TRANQUI/
│   │   ├── 📁 Te Vas/
│   │   ├── 📁 Vaticano/
│   │   ├── 📁 Verano En París/
│   │   ├── 📁 Verano En París (Remix)/
│   │   ├── 📁 Wapa/
│   │   │   ├── 📄 01. Wapa (Cobuz & Bustta Remix Extended).mp3
│   │   │   └── 📄 02. Wapa (Cobuz & Bustta Remix).mp3
│   │   └── 📁 White Wine/
│   │       └── 📄 01. Jerry Di - White Wine ｜ Lyric Video.mp3
│   └── 📁 Michael Bublé/
│       └── 📁 Christmas/
│           ├── 📄 01. All I Want for Christmas Is You.mp3
│           ├── 📄 02. Ave Maria.mp3
│           ├── 📄 03. Blue Christmas.mp3
│           ├── 📄 04. Christmas (Baby Please Come Home).mp3
│           ├── 📄 05. Cold December Night.mp3
│           ├── 📄 06. Frosty the Snowman (feat. The Puppini Sisters).mp3
│           ├── 📄 07. Have Yourself a Merry Little Christmas.mp3
│           ├── 📄 08. Holly Jolly Christmas.mp3
│           ├── 📄 09. I'll Be Home for Christmas.mp3
│           ├── 📄 10. It's Beginning to Look a Lot like Christmas.mp3
│           ├── 📄 11. Jingle Bells (feat. The Puppini Sisters).mp3
│           ├── 📄 12. Let It Snow! (10th Anniversary).mp3
│           ├── 📄 13. Maybe This Christmas.mp3
│           ├── 📄 14. Michael's Christmas Greeting.mp3
│           ├── 📄 15. Mis Deseos ⧸ Feliz Navidad (with Thalia).mp3
│           ├── 📄 16. Santa Baby.mp3
│           ├── 📄 17. Santa Claus Is Coming to Town.mp3
│           ├── 📄 18. Silent Night.mp3
│           ├── 📄 19. Silver Bells (feat. Naturally 7).mp3
│           ├── 📄 20. The Christmas Song (Chestnuts Roasting on an Open Fire).mp3
│           ├── 📄 21. The Christmas Sweater.mp3
│           ├── 📄 22. The More You Give (The More You'll Have).mp3
│           ├── 📄 23. White Christmas (with Shania Twain).mp3
│           ├── 📄 24. White Christmas.mp3
│           ├── 📄 25. Winter Wonderland (feat. Rod Stewart).mp3
│           └── 📄 26. Winter Wonderland.mp3
├── 📁 src/
│   ├── 📁 __pycache__/ 🚫 (auto-hidden)
│   ├── 📁 application/
│   │   ├── 📁 __pycache__/ 🚫 (auto-hidden)
│   │   ├── 📁 jobs/
│   │   │   ├── 📁 __pycache__/ 🚫 (auto-hidden)
│   │   │   ├── 🐍 __init__.py
│   │   │   └── 🐍 download_job.py
│   │   ├── 📁 providers/
│   │   │   ├── 📁 __pycache__/ 🚫 (auto-hidden)
│   │   │   ├── 🐍 __init__.py
│   │   │   ├── 🐍 app_provider.py
│   │   │   ├── 🐍 cli_provider.py
│   │   │   ├── 🐍 command_provider.py
│   │   │   └── 🐍 logger_provider.py
│   │   └── 🐍 __init__.py
│   ├── 📁 domain/
│   │   ├── 📁 __pycache__/ 🚫 (auto-hidden)
│   │   ├── 📁 scheduler/
│   │   │   ├── 📁 __pycache__/ 🚫 (auto-hidden)
│   │   │   ├── 🐍 __init__.py
│   │   │   ├── 🐍 base_job.py
│   │   │   └── 🐍 time_unit.py
│   │   ├── 🐍 Job.py
│   │   ├── 🐍 Metadata.py
│   │   ├── 🐍 __init__.py
│   │   └── 🐍 base_command.py
│   ├── 📁 infrastructure/
│   │   ├── 📁 audio/
│   │   │   ├── 📁 __pycache__/ 🚫 (auto-hidden)
│   │   │   ├── 🐍 __init__.py
│   │   │   ├── 🐍 base_audio_handler.py
│   │   │   ├── 🐍 handler_factory.py
│   │   │   ├── 🐍 m4a_handler.py
│   │   │   └── 🐍 mp3_handler.py
│   │   ├── 📁 config/
│   │   │   ├── 📁 __pycache__/ 🚫 (auto-hidden)
│   │   │   ├── 🐍 config.py
│   │   │   └── 🐍 file_music_extension.py
│   │   ├── 📁 repository/
│   │   │   ├── 📁 __pycache__/ 🚫 (auto-hidden)
│   │   │   ├── 🐍 __init__.py
│   │   │   └── 🐍 job_repository.py
│   │   ├── 📁 service/
│   │   │   ├── 📁 __pycache__/ 🚫 (auto-hidden)
│   │   │   ├── 🐍 __init__.py
│   │   │   ├── 🐍 album_postprocessor.py
│   │   │   ├── 🐍 scheduler_service.py
│   │   │   ├── 🐍 update_service.py
│   │   │   └── 🐍 yt_dlp_service.py
│   │   ├── 📁 system/
│   │   │   ├── 📁 __pycache__/ 🚫 (auto-hidden)
│   │   │   ├── 🐍 __init__.py
│   │   │   ├── 🐍 directory_utils.py
│   │   │   ├── 🐍 json_loader.py
│   │   │   └── 🐍 subprocess_runner.py
│   │   └── 📁 utils/
│   │       ├── 📁 __pycache__/ 🚫 (auto-hidden)
│   │       ├── 🐍 __init__.py
│   │       └── 🐍 progress_bar.py
│   ├── 📁 presentation/
│   │   ├── 📁 commands/
│   │   │   ├── 📁 __pycache__/ 🚫 (auto-hidden)
│   │   │   ├── 🐍 __init__.py
│   │   │   ├── 🐍 boot.py
│   │   │   ├── 🐍 cancel_job.py
│   │   │   ├── 🐍 check_jobs.py
│   │   │   ├── 🐍 download_metadata.py
│   │   │   ├── 🐍 list_artists.py
│   │   │   ├── 🐍 process_albums.py
│   │   │   ├── 🐍 run_now.py
│   │   │   └── 🐍 update_app.py
│   │   └── 📁 controller/
│   │       ├── 📁 __pycache__/ 🚫 (auto-hidden)
│   │       ├── 🐍 __init__.py
│   │       └── 🐍 download_controller.py
│   ├── 📁 utils/
│   │   ├── 📁 __pycache__/ 🚫 (auto-hidden)
│   │   ├── 🐍 Transform.py
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 audio_utils.py
│   │   └── 🐍 logging_config.py
│   ├── 🐍 __init__.py
│   └── 🐍 main.py
├── 🚫 .gitignore
├── 🐳 Dockerfile
├── 📖 README.md
├── ⚙️ docker-compose.yml
├── 📄 requirements.txt
├── 🐍 setup.py
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

#### 2.3 Archivo de cookies (OPCIONAL)
Si has abusado de descargas de contenido, es posible que Youtube haya bloqueado tu IP por un tiempo, y te pida credenciales de Youtube. En ese caso:

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

4. Listar comandos:
````
yt-subs --list
````

5. Arrancar en modo por defecto:
````
yt-subs
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

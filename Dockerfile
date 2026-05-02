# VoiceLingo - Dockerfile
# L'app desktop (tkinter) tourne en local.
# Docker est utilisé pour l'API FastAPI uniquement.
#
# Usage :
#   docker build -t voicelingo:latest .
#   docker run -p 8000:8000 voicelingo:latest
#   # API disponible sur http://localhost:8000/docs

FROM python:3.10-slim

# Installer ffmpeg (requis pour l'extraction audio)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier requirements en premier pour exploiter le cache Docker
COPY requirements.txt .
RUN pip install --no-cache-dir \
    fastapi==0.111.0 \
    uvicorn[standard]==0.29.0 \
    pydantic==2.7.1 \
    requests==2.31.0 \
    numpy==1.26.4
# Note : torch, faster-whisper, TTS sont volumineux (7+ Go).
# En production, les installer séparément ou utiliser un volume.

# Copier le code
COPY *.py ./
COPY config.json .

# Créer les dossiers nécessaires
RUN mkdir -p speaker_wavs outputs

# Fix OpenMP Windows - pas nécessaire sur Linux mais inoffensif
ENV KMP_DUPLICATE_LIB_OK=TRUE
ENV OMP_NUM_THREADS=1

# Exposer le port FastAPI
EXPOSE 8000

# Lancer l'API FastAPI
CMD ["uvicorn", "main_api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

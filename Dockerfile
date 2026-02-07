# === MILARIPPA - Dockerfile ===

FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier l'application
COPY app/ /app/app/
COPY config/ /app/config/
COPY .env.example /app/.env

# Créer les répertoires de données
RUN mkdir -p /app/data/chunks

# Variable d'environnement
ENV FLASK_APP=app/main.py
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Exposer le port
EXPOSE 8000

# Lancer l'application
CMD ["python", "app/main.py"]

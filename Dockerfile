FROM python:3.11-slim

# Installera systempaket som behövs
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    libffi-dev \
    libssl-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Skapa arbetskatalog
WORKDIR /app

# Kopiera requirements och installera Python-paket
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiera projektfiler
COPY . .

# Skapa katalog för bilder
RUN mkdir -p /app/images

# Skapa katalog för crawl-data (för jobdir)
RUN mkdir -p /app/crawls

# Sätt miljövariabler
ENV PYTHONPATH=/app
ENV SCRAPY_SETTINGS_MODULE=doppelganger.settings

# Exponera port (om vi vill köra en web-interface senare)
EXPOSE 8080

# Standard kommando
CMD ["scrapy", "crawl", "mpb_all"]


FROM python:3.11-slim

# Installera systempaket som behövs (inkl. Brotli-stöd)
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
    libbrotli-dev \
    libbrotli1 \
    brotli \
    libzstd-dev \
    libzstd1 \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Skapa arbetskatalog
WORKDIR /app

# Kopiera requirements och installera Python-paket
COPY requirements.txt .

# Uppgradera pip och installera wheel för bättre kompilering
RUN pip install --upgrade pip setuptools wheel

# Installera Python-paket med Brotli-stöd
RUN pip install --no-cache-dir -r requirements.txt

# Verifiera att Brotli fungerar
RUN python -c "import brotli; print('Brotli installed successfully')" && \
    python -c "import brotlicffi; print('BrotliCFFI installed successfully')"

# Kopiera projektfiler
COPY . .

# Skapa katalog för bilder
RUN mkdir -p /app/images

# Skapa katalog för crawl-data (för jobdir)
RUN mkdir -p /app/crawls

# Skapa katalog för cache
RUN mkdir -p /app/httpcache

# Sätt miljövariabler
ENV PYTHONPATH=/app
ENV SCRAPY_SETTINGS_MODULE=doppelganger.settings
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Exponera port
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import scrapy; import brotli; print('OK')" || exit 1

# Standard kommando
CMD ["scrapy", "crawl", "mpb_all"]


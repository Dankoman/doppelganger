#!/bin/bash

# Enkel installation av Camoufox-integration
# Kopierar filer direkt utan Git patch

echo "🦊 Installerar Camoufox-integration..."

# Kontrollera att vi är i rätt katalog
if [ ! -f "scrapy.cfg" ]; then
    echo "❌ Fel: Kör detta script från doppelganger root-katalogen"
    exit 1
fi

# Skapa backup
echo "📦 Skapar backup..."
cp doppelganger/settings.py doppelganger/settings.py.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
cp requirements.txt requirements.txt.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
cp run_scraper.sh run_scraper.sh.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

echo "📁 Kopierar Camoufox-filer..."

# Kopiera alla filer från /tmp
echo "Kopierar middlewares_camoufox.py..."
cp /tmp/middlewares_camoufox.py doppelganger/middlewares_camoufox.py

echo "Uppdaterar docker-compose.yml..."
cp /tmp/docker-compose-final.yml docker-compose.yml

echo "Uppdaterar requirements.txt..."
cp /tmp/requirements-camoufox.txt requirements.txt

echo "Uppdaterar run_scraper.sh..."
cp /tmp/run_scraper-final.sh run_scraper.sh
chmod +x run_scraper.sh

echo "Uppdaterar settings.py..."
cat /tmp/camoufox-settings-append.py >> doppelganger/settings.py

echo ""
echo "🎉 Camoufox-integration installerad!"
echo ""
echo "📋 Nästa steg:"
echo "1. ./run_scraper.sh build"
echo "2. ./run_scraper.sh camoufox_test"
echo ""
echo "🦊 Camoufox-servern startas automatiskt!"


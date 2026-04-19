# Doppelganger Scraper - Enhanced Anti-Blocking Edition

En kraftigt förbättrad version av doppelganger-scrapern med avancerade anti-blocking-tekniker för att undvika 403-fel och andra blockeringar.

## 🚀 Nya Förbättringar (v2.0)

### 🛡️ Avancerat Anti-Blocking System
- **12 Realistiska User Agents**: Chrome, Firefox, Safari, Edge (desktop + mobile)
- **Förbättrade Headers**: sec-ch-ua, Sec-Fetch-*, moderna browser-headers
- **Intelligent Referer-hantering**: Google → webbplats → interna länkar
- **Adaptiv Fördröjning**: Ökar automatiskt vid 403/429-fel
- **Exponential Backoff**: Smart retry-logik med ökande väntetider

### 🗜️ Komplett Komprimeringssstöd
- **Brotli-stöd**: Både `brotli` och `brotlicffi` bibliotek
- **Zstandard**: Modernaste komprimeringsformat
- **Gzip/Deflate**: Traditionellt stöd
- **Automatisk Dekodning**: Inga fler komprimeringsvarningar

### 🐳 Förbättrad Docker-integration
- **Optimerad Dockerfile**: Systempaket för alla komprimeringsformat
- **Healthcheck**: Automatisk verifiering av container-status
- **Behörighetsfixar**: Inga fler permission denied-fel
- **HTTP Cache**: Persistent caching för bättre prestanda

### ⚙️ Smarta Scrapy-inställningar
- **Mycket Konservativ**: 5s delay, 1 concurrent request
- **AutoThrottle**: Intelligent anpassning baserat på server-respons
- **Enhanced Retry**: Retry på 403-fel med exponential backoff
- **HTTP Caching**: Minskar onödiga requests

## 📦 Installation

### Snabbstart:
```bash
git clone https://github.com/Dankoman/doppelganger.git
cd doppelganger
git checkout anti_blocking_docker_support

# Bygg och testa
./run_scraper.sh build
./run_scraper.sh test
```

### Manuell installation:
```bash
# Installera Docker och docker-compose först
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Klona och bygg
git clone https://github.com/Dankoman/doppelganger.git
cd doppelganger
git checkout anti_blocking_docker_support
chmod +x run_scraper.sh
./run_scraper.sh build
```

## 🔧 Användning

### Grundläggande kommandon:
```bash
./run_scraper.sh test     # Testa med 5 items
./run_scraper.sh run      # Kör full scraping
./run_scraper.sh logs     # Visa loggar
./run_scraper.sh stop     # Stoppa scraper
```

### Avancerade inställningar:
```bash
# Extremt konservativ scraping
docker-compose run --rm doppelganger-scraper scrapy crawl mpb_all \
  -s DOWNLOAD_DELAY=10 \
  -s CONCURRENT_REQUESTS=1 \
  -s RETRY_TIMES=10

# Debug-läge
docker-compose run --rm doppelganger-scraper scrapy crawl mpb_all \
  -L DEBUG -s CLOSESPIDER_ITEMCOUNT=1
```

## 🛠️ Tekniska Förbättringar

### Enhanced Middleware Classes:
1. **EnhancedUserAgentMiddleware**: 12 roterande user agents
2. **AdvancedAntiBlockingMiddleware**: Adaptiva headers och timing
3. **EnhancedRetryMiddleware**: Exponential backoff för retries

### Komprimeringsbibliotek:
- `brotli>=1.0.9` - Officiella Google-biblioteket
- `brotlicffi>=1.0.9` - Pure Python fallback
- `zstandard>=0.19.0` - Modernaste komprimering
- Systempaket: `libbrotli-dev`, `libzstd-dev`

### Säkerhetsförbättringar:
- Uppdaterade TLS/SSL-bibliotek
- Bättre charset-detektering
- HTTP/2-stöd för mindre fingerprinting
- Proxy-stöd för IP-rotation

## 📊 Prestanda och Statistik

### Före vs Efter:
```
Före (v1.0):
❌ 403 Forbidden på första requesten
❌ Brotli-komprimeringsvarningar
❌ Behörighetsproblem i Docker
❌ Grundläggande user agents

Efter (v2.0):
✅ Framgångsrika 200 OK-responses
✅ Komplett komprimeringssstöd
✅ Smidig Docker-körning
✅ 12 realistiska user agents
✅ Adaptiv anti-blocking
```

### Rekommenderade Inställningar:
- **Konservativ**: 5-10s delay, 1 concurrent
- **Normal**: 3-5s delay, 1-2 concurrent
- **Aggressiv**: 1-3s delay, 2-4 concurrent (ej rekommenderat)

## 🔍 Felsökning

### Vanliga Problem och Lösningar:

#### 403 Forbidden:
```bash
# Öka fördröjning
docker-compose run --rm doppelganger-scraper scrapy crawl mpb_all \
  -s DOWNLOAD_DELAY=15 -s CONCURRENT_REQUESTS=1

# Kontrollera IP-status
curl ifconfig.me
curl -I "https://www.mypornstarbook.net/"
```

#### Brotli-problem:
```bash
# Verifiera installation
docker-compose run --rm doppelganger-scraper python -c "
import brotli, brotlicffi
print('✅ Brotli support OK')
"
```

#### Behörighetsproblem:
```bash
# Skapa kataloger med rätt behörigheter
mkdir -p images crawls logs httpcache
chmod 755 images crawls logs httpcache
```

## 📈 Monitoring och Analys

### Aktivera monitoring:
```bash
./run_scraper.sh monitor  # Startar nginx på port 8080
```

### Loggar och statistik:
```bash
./run_scraper.sh logs                    # Live loggar
docker-compose exec doppelganger-scraper cat /app/logs/scrapy.log
```

### Prestanda-mätning:
- Requests per minut
- Framgångsfrekvens (200 vs 403)
- Genomsnittlig response-tid
- Komprimeringseffektivitet

## 🚨 Etiska Riktlinjer

### Använd Ansvarsfullt:
- Respektera robots.txt (kan aktiveras)
- Överbelasta inte målservrar
- Följ webbplatsers användarvillkor
- Använd endast för lagliga ändamål

### Rate Limiting:
- Standard: Max 1 request per 5 sekunder
- Konservativ: Max 1 request per 10 sekunder
- Respektfullt: Max 1 request per 15 sekunder

## 🔄 Uppdateringar och Underhåll

### Håll bibliotek uppdaterade:
```bash
# Uppdatera requirements.txt regelbundet
pip list --outdated
```

### Övervaka user agents:
```bash
# Kontrollera att user agents fortfarande är aktuella
# Uppdatera listan var 3-6 månad
```

## 📞 Support och Bidrag

### Rapportera Problem:
1. Kontrollera loggar först
2. Testa med debug-läge
3. Inkludera systeminfo och felmeddelanden
4. Skapa GitHub issue med detaljer

### Bidra till Projektet:
1. Forka repot
2. Skapa feature-branch
3. Testa noggrant
4. Skicka pull request

## 📄 Licens

Se originalrepots licens för detaljer.

---

**Version**: 2.0 Enhanced Anti-Blocking Edition  
**Senast uppdaterad**: 2025-07-25  
**Kompatibilitet**: Python 3.11+, Docker 20.10+


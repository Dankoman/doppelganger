# Doppelganger Scraper med Anti-Blocking

En förbättrad version av doppelganger-scrapern som använder avancerade anti-blocking-tekniker för att undvika 403-fel och andra blockeringar.

## Förändringar från Original

### Anti-Blocking Funktioner
- **Roterande User Agents**: Använder olika realistiska user agents för varje request
- **Förbättrade Headers**: Lägger till realistiska browser-headers
- **Slumpmässiga Fördröjningar**: Varierar tiden mellan requests för att undvika detektering
- **Intelligent Referer-hantering**: Sätter korrekta referer-headers för interna länkar

### Docker-Support
- Komplett Docker-konfiguration för enkel deployment
- Volymer för bildlagring och crawl-data
- Monitoring-möjligheter via nginx
- Resurs-begränsningar för säker körning

## Installation och Användning

### Förutsättningar
- Docker och docker-compose installerat
- Git för att klona repot

### Snabbstart

1. **Klona repot:**
   ```bash
   git clone https://github.com/Dankoman/doppelganger.git
   cd doppelganger
   ```

2. **Bygg Docker-imagen:**
   ```bash
   ./run_scraper.sh build
   ```

3. **Testa scrapern:**
   ```bash
   ./run_scraper.sh test
   ```

4. **Kör full scraping:**
   ```bash
   ./run_scraper.sh run
   ```

### Kommandoreferens

```bash
# Bygg Docker-image
./run_scraper.sh build

# Kör scraper (interaktivt)
./run_scraper.sh run

# Kör scraper i bakgrunden
./run_scraper.sh run-detached

# Kör med web-monitoring på port 8080
./run_scraper.sh monitor

# Stoppa scraper
./run_scraper.sh stop

# Visa loggar
./run_scraper.sh logs

# Öppna shell i container
./run_scraper.sh shell

# Testa med begränsad scraping (5 items)
./run_scraper.sh test

# Rensa Docker-resurser
./run_scraper.sh clean

# Visa hjälp
./run_scraper.sh help
```

### Manuell Körning utan Docker

Om du föredrar att köra utan Docker:

1. **Installera beroenden:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Kör scrapern:**
   ```bash
   scrapy crawl mpb_all
   ```

## Konfiguration

### Anti-Blocking Inställningar

I `doppelganger/settings.py` kan du justera:

```python
# Anti-blocking inställningar
ANTIBLOCK_ENABLED = True
ANTIBLOCK_DELAY_RANGE = (1, 4)  # Slumpmässig fördröjning mellan 1-4 sekunder

# Scrapy-inställningar för försiktig scraping
DOWNLOAD_DELAY = 3.0
CONCURRENT_REQUESTS = 2
CONCURRENT_REQUESTS_PER_DOMAIN = 1
```

### Docker-miljövariabler

Du kan överskrida inställningar via miljövariabler i `docker-compose.yml`:

```yaml
environment:
  - DOWNLOAD_DELAY=5.0
  - CONCURRENT_REQUESTS=1
  - ANTIBLOCK_ENABLED=true
```

## Filstruktur

```
doppelganger/
├── doppelganger/           # Scrapy-projekt
│   ├── spiders/           # Spider-filer
│   ├── middlewares.py     # Anti-blocking middleware
│   ├── settings.py        # Scrapy-inställningar
│   └── ...
├── images/                # Nedladdade bilder (skapas automatiskt)
├── crawls/                # Crawl-data för återupptagning
├── logs/                  # Loggfiler
├── Dockerfile             # Docker-konfiguration
├── docker-compose.yml     # Docker Compose-konfiguration
├── requirements.txt       # Python-beroenden
├── run_scraper.sh         # Start-script
└── README.md              # Denna fil
```

## Tekniska Detaljer

### Anti-Blocking Middleware

Scrapern använder två huvudsakliga middleware:

1. **RotatingUserAgentMiddleware**: Roterar mellan olika realistiska user agents
2. **AntiBlockingMiddleware**: Lägger till realistiska headers och slumpmässiga fördröjningar

### User Agents

Middleware använder en lista med aktuella user agents från:
- Chrome (Windows, macOS, Linux)
- Firefox (Windows)
- Safari (macOS)
- Edge (Windows)

### Headers

Följande headers läggs automatiskt till:
- Accept
- Accept-Language
- Accept-Encoding
- DNT (Do Not Track)
- Connection
- Upgrade-Insecure-Requests
- Sec-Fetch-* headers
- Cache-Control
- Referer (för interna länkar)

## Felsökning

### Vanliga Problem

1. **403 Forbidden-fel**: Öka `DOWNLOAD_DELAY` och minska `CONCURRENT_REQUESTS`
2. **Timeout-fel**: Kontrollera internetanslutning och öka timeout-värden
3. **Docker-problem**: Kontrollera att Docker körs och att du har tillräckligt med diskutrymme

### Loggar

Kontrollera loggar för detaljerad information:
```bash
./run_scraper.sh logs
```

### Debug-läge

För mer detaljerade loggar, ändra log-nivån:
```bash
docker-compose run --rm doppelganger-scraper scrapy crawl mpb_all -L DEBUG
```

## Bidrag

För att bidra till projektet:
1. Forka repot
2. Skapa en feature-branch
3. Gör dina ändringar
4. Testa noggrant
5. Skicka en pull request

## Licens

Se originalrepots licens för detaljer.

## Varningar

- Använd scrapern ansvarsfullt och respektera robots.txt
- Överbelasta inte målservrar med för många requests
- Kontrollera lokala lagar och webbplatsers användarvillkor
- Använd endast för lagliga ändamål


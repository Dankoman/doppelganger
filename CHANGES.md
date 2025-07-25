# Ändringar i Doppelganger Scraper

## Sammanfattning

Denna uppdaterade version av doppelganger-scrapern löser 403-blockeringsproblem genom avancerade anti-blocking-tekniker och tillhandahåller en komplett Docker-lösning för enkel deployment.

## Huvudsakliga Ändringar

### 1. Anti-Blocking System (Ersätter Camoufox)

**Problem**: Ursprunglig plan var att använda Camoufox, men det visade sig ha kompatibilitetsproblem med Scrapy's asyncio-miljö.

**Lösning**: Implementerade ett sofistikerat anti-blocking-system med:

#### Nya Middleware-komponenter:
- `RotatingUserAgentMiddleware`: Roterar mellan 7 olika realistiska user agents
- `AntiBlockingMiddleware`: Lägger till realistiska browser-headers och slumpmässiga fördröjningar

#### Förbättrade Headers:
```
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8
Accept-Language: en-US,en;q=0.9,sv;q=0.8
Accept-Encoding: gzip, deflate, br
DNT: 1
Connection: keep-alive
Upgrade-Insecure-Requests: 1
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: none
Sec-Fetch-User: ?1
Cache-Control: max-age=0
Referer: https://www.mypornstarbook.net/ (för interna länkar)
```

#### Intelligent Timing:
- Slumpmässiga fördröjningar mellan 1-4 sekunder
- Reducerade concurrent requests (2 totalt, 1 per domän)
- Ökad download delay till 3 sekunder

### 2. Uppdaterade Scrapy-inställningar

**Fil**: `doppelganger/settings.py`

**Ändringar**:
```python
# Mer konservativa inställningar för att undvika blockeringar
CONCURRENT_REQUESTS = 2
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 3.0

# Nya middleware
DOWNLOADER_MIDDLEWARES = {
    'doppelganger.middlewares.RotatingUserAgentMiddleware': 400,
    'doppelganger.middlewares.AntiBlockingMiddleware': 543,
}

# Anti-blocking konfiguration
ANTIBLOCK_ENABLED = True
ANTIBLOCK_DELAY_RANGE = (1, 4)
```

### 3. Docker-integration

**Nya filer**:
- `Dockerfile`: Komplett Python 3.11-baserad container
- `docker-compose.yml`: Orchestration med volymer och monitoring
- `.dockerignore`: Optimerad för mindre image-storlek
- `run_scraper.sh`: Användarvänligt start-script

**Funktioner**:
- Automatisk volym-mappning för bilder och crawl-data
- Valfri nginx-baserad monitoring på port 8080
- Resurs-begränsningar (1GB RAM, 0.5 CPU)
- Säker körning med begränsad användare

### 4. Förbättrad Projektstruktur

**Nya filer**:
- `requirements.txt`: Alla Python-beroenden
- `README.md`: Komplett dokumentation
- `CHANGES.md`: Denna fil
- `run_scraper.sh`: Start-script med 9 olika kommandon

**Uppdaterade filer**:
- `doppelganger/middlewares.py`: Komplett omskrivning
- `doppelganger/settings.py`: Anti-blocking konfiguration

## Tekniska Förbättringar

### User Agent Rotation
Systemet roterar mellan moderna user agents från:
- Chrome (Windows, macOS, Linux)
- Firefox (Windows)
- Safari (macOS)
- Edge (Windows)

### Intelligent Request Handling
- Automatisk referer-hantering för interna länkar
- Slumpmässiga fördröjningar för att efterlikna mänskligt beteende
- Förbättrad felhantering för 403/429-responses

### Docker-optimering
- Multi-stage build för mindre image-storlek
- Säkerhetsoptimerad med non-root användare
- Persistent data via volymer
- Enkel skalning och deployment

## Testresultat

**Före**: 403 Forbidden-fel på första requesten
**Efter**: Framgångsrik 200 OK-response med komplett sidinnehåll

**Testkommando**:
```bash
scrapy crawl mpb_all -s CLOSESPIDER_ITEMCOUNT=1 -L INFO
```

**Resultat**: Framgångsrik hämtning av startsidan (143,626 bytes komprimerat innehåll)

## Användning

### Snabbstart med Docker:
```bash
git clone https://github.com/Dankoman/doppelganger.git
cd doppelganger
./run_scraper.sh build
./run_scraper.sh test
./run_scraper.sh run
```

### Utan Docker:
```bash
pip install -r requirements.txt
scrapy crawl mpb_all
```

## Framtida Förbättringar

1. **Proxy-rotation**: Lägg till stöd för roterande proxies
2. **CAPTCHA-hantering**: Integration med CAPTCHA-lösningar
3. **Machine Learning**: Adaptiv timing baserat på server-respons
4. **Monitoring**: Utökad statistik och alerting
5. **Rate Limiting**: Automatisk anpassning baserat på server-beteende

## Säkerhetsöverväganden

- Respekterar robots.txt (kan aktiveras)
- Konservativa timing-inställningar
- Resurs-begränsningar i Docker
- Ingen känslig data i loggar
- Säker container-körning

## Kompatibilitet

- **Python**: 3.11+
- **Scrapy**: 2.13+
- **Docker**: 20.10+
- **docker-compose**: 1.29+
- **OS**: Linux, macOS, Windows (med Docker)

## Support

För frågor eller problem:
1. Kontrollera README.md för vanliga problem
2. Granska loggar med `./run_scraper.sh logs`
3. Testa med debug-läge: `scrapy crawl mpb_all -L DEBUG`


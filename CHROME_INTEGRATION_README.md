# Chrome Headless Integration

## 🎯 Översikt

Denna integration ansluter Scrapy till befintliga `chromedp/headless-shell` Docker-instanser för att kringgå bot-detektering genom att använda en riktig browser istället för HTTP-requests.

## 🚀 Fördelar

### **✅ Ultimat Bot-Bypass:**
- **Riktig browser** - Ingen bot-fingerprinting möjlig
- **JavaScript-rendering** - Hanterar moderna anti-bot-skript
- **Naturliga headers** - Chrome sätter perfekta headers automatiskt
- **Session-hantering** - Cookies och state hanteras naturligt

### **✅ Använder befintlig infrastruktur:**
- **Ansluter till dina Chrome-instanser** på 192.168.0.50:9222 och 9223
- **Load balancing** mellan instanser
- **Ingen extra kostnad** - Använder redan körande containers

## 🛠️ Konfiguration

### Chrome-instanser
```yaml
# Dina befintliga chromedp/headless-shell instanser
CHROME_HOST: '192.168.0.50'
CHROME_PORTS: [9222, 9223]
```

### Aktivering
Chrome-middleware aktiveras endast när `CHROME_ENABLED=True` sätts:

```bash
# Aktivera Chrome för en körning
./run_scraper.sh chrome_test

# Eller manuellt
scrapy crawl mpb_from_urls -s CHROME_ENABLED=True
```

## 📋 Kommandon

| Kommando | Beskrivning | Antal profiler |
|----------|-------------|----------------|
| `chrome_test` | Testa Chrome-integration | 1 |
| `chrome_sample` | Medelstor test | 10 |
| `chrome_run` | Full scraping | Alla 6,360 |
| `chrome_debug` | Debug-läge | 1 |

## 🧪 Test och verifiering

### 1. Testa Chrome-anslutning
```bash
# Kör test-script
python3 test_chrome.py

# Eller via Docker
./run_scraper.sh chrome_test
```

### 2. Verifiera Chrome-instanser
```bash
# Kontrollera att Chrome körs
curl http://192.168.0.50:9222/json/version
curl http://192.168.0.50:9223/json/version
```

## 🔧 Teknisk implementation

### Chrome Middleware
- **ChromeHeadlessMiddleware** - Huvudmiddleware med load balancing
- **ChromeDownloaderMiddleware** - Förenklad version för en instans
- **Anti-detection** - Inbyggda funktioner för att undvika detektering

### Selenium WebDriver
```python
options = Options()
options.add_experimental_option("debuggerAddress", f"{host}:{port}")
options.add_argument('--disable-blink-features=AutomationControlled')
driver = webdriver.Chrome(options=options)
```

### Mänskligt beteende
- **Slumpmässig scrollning** på sidor
- **Musrörelse-simulering** via JavaScript
- **Realistiska fördröjningar** mellan requests
- **Fokus-hantering** för naturligt beteende

## ⚙️ Inställningar

### Chrome-specifika settings
```python
CHROME_ENABLED = False  # Aktiveras med -s CHROME_ENABLED=True
CHROME_HOST = '192.168.0.50'
CHROME_PORTS = [9222, 9223]
CHROME_TIMEOUT = 30
CHROME_DOWNLOAD_DELAY = 8  # Längre delay för Chrome
CHROME_CONCURRENT_REQUESTS = 1  # En åt gången
```

### Optimerade Scrapy-settings för Chrome
```python
DOWNLOAD_DELAY = 8
CONCURRENT_REQUESTS = 1
RETRY_TIMES = 3  # Färre retries - Chrome är mer tillförlitlig
```

## 🔍 Felsökning

### Chrome-anslutning misslyckas
```bash
# Kontrollera att Chrome körs
docker ps | grep headless-shell

# Kontrollera nätverksanslutning
telnet 192.168.0.50 9222
```

### WebDriver-fel
```bash
# Kontrollera ChromeDriver-version
chromedriver --version

# Uppdatera ChromeDriver om nödvändigt
```

### Prestanda-problem
```bash
# Öka fördröjningar
-s CHROME_DOWNLOAD_DELAY=15

# Minska samtidighet
-s CHROME_CONCURRENT_REQUESTS=1
```

## 📊 Förväntade resultat

### Med Chrome headless:
- ✅ **200 OK** istället för 403 Forbidden
- ✅ **Komplett JavaScript-rendering**
- ✅ **Naturlig browser-fingerprint**
- ✅ **Mycket hög success rate** (>95%)

### Prestanda:
- **Långsammare** än HTTP-requests (8s delay)
- **Mer resurskrävande** (Chrome-instanser)
- **Mycket mer tillförlitlig** för bot-detektering

## 🎯 Användningsfall

### Rekommenderat för:
- **Webbplatser med avancerad bot-detektering**
- **JavaScript-tunga sidor**
- **När HTTP-metoder misslyckas**
- **Högkvalitativ data-extraktion**

### Inte rekommenderat för:
- **Enkla API-endpoints**
- **Mycket stora volymer** (>10,000 sidor)
- **Tidskritiska applikationer**

## 🔄 Workflow

1. **Testa anslutning** med `chrome_test`
2. **Verifiera med sample** med `chrome_sample`
3. **Kör full scraping** med `chrome_run`
4. **Övervaka med** `logs`

## 🎉 Slutsats

Chrome headless-integration ger den ultimata lösningen för bot-detektering genom att använda en riktig browser. Kombinerat med din befintliga Chrome-infrastruktur ger detta en kraftfull och kostnadseffektiv scraping-lösning.


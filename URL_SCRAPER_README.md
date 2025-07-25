# URL-Baserad Scraper - Kringgå Blockerad Huvudsida

## 🎯 Problemlösning

Den ursprungliga scrapern blockerades på huvudsidan (`all-porn-stars.php`) med 403 Forbidden-fel. Denna lösning kringgår problemet genom att:

1. **Extrahera alla profillänkar** från en sparad HTML-fil
2. **Scrapa individuella profiler** direkt istället för huvudsidan
3. **Använda samma anti-blocking system** för varje profil

## 📊 Statistik

- **6,360 profillänkar** extraherade från HTML-fil
- **Individuella pornstar-profiler** (format: `/pornstars/a/aali_kali/index.php`)
- **Filtrerat bort navigeringslänkar** automatiskt

## 🚀 Användning

### Snabbstart
```bash
# Bygg imagen
./run_scraper.sh build

# Testa med 5 profiler
./run_scraper.sh url_test

# Scrapa 100 profiler (rekommenderat för test)
./run_scraper.sh url_sample

# Scrapa alla 6,360 profiler
./run_scraper.sh url_run
```

### Debug och felsökning
```bash
# Debug-läge för en profil
./run_scraper.sh url_debug

# Visa första 10 URL:er
head -10 profile_urls.txt

# Kontrollera antal URL:er
wc -l profile_urls.txt
```

## 📁 Filer

### `profile_urls.txt`
Innehåller alla 6,360 profillänkar extraherade från HTML-filen:
```
https://www.mypornstarbook.net/pornstars/a/aali_kali/index.php
https://www.mypornstarbook.net/pornstars/a/aaliyah_grey/index.php
...
```

### `mpb_spider_from_urls.py`
Ny spider som:
- Läser URL:er från `profile_urls.txt`
- Scrapar varje profil individuellt
- Extraherar namn, bilder och bio
- Använder samma anti-blocking middleware

## 🛡️ Anti-Blocking Funktioner

Samma avancerade anti-blocking system som v2.0:
- ✅ **12 realistiska User Agents** (Chrome, Firefox, Safari, Edge)
- ✅ **Avancerade headers** (sec-ch-ua, Sec-Fetch-*)
- ✅ **Adaptiv fördröjning** (ökar vid 403-fel)
- ✅ **Exponential backoff** retry-logik
- ✅ **Brotli-komprimeringssstöd**
- ✅ **Intelligent referer-hantering**

## 📈 Fördelar

### Jämfört med ursprunglig metod:
1. **Kringgår blockering** - Ingen åtkomst till blockerad huvudsida
2. **Mindre misstänkt** - Inga upprepade requests till samma sida
3. **Mer effektivt** - Direkt åtkomst till målsidor
4. **Skalbart** - Kan hantera tusentals profiler
5. **Robust** - Fortsätter även om enskilda profiler misslyckas

### Prestanda:
- **Konservativa inställningar**: 5s delay mellan requests
- **Begränsad samtidighet**: 1 concurrent request
- **Intelligent retry**: 6 försök med exponential backoff
- **Adaptiv timing**: Ökar delay vid problem

## 🔧 Teknisk Implementation

### Docker-integration
```yaml
volumes:
  - ./profile_urls.txt:/app/profile_urls.txt:ro
```

### Spider-konfiguration
```python
class MpbFromUrlsSpider(scrapy.Spider):
    name = 'mpb_from_urls'
    
    def start_requests(self):
        with open('/app/profile_urls.txt', 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)
```

## 📋 Kommandoreferens

| Kommando | Beskrivning | Antal profiler |
|----------|-------------|----------------|
| `url_test` | Snabb test | 5 |
| `url_sample` | Medelstor test | 100 |
| `url_run` | Full scraping | 6,360 |
| `url_debug` | Debug-läge | 1 |

## 🎯 Rekommendationer

1. **Börja med `url_test`** för att verifiera att allt fungerar
2. **Använd `url_sample`** för att testa prestanda
3. **Kör `url_run`** endast när du är säker på konfigurationen
4. **Övervaka med `logs`** under längre körningar

## 🔍 Felsökning

### Om profile_urls.txt saknas:
```bash
# Kontrollera att filen finns
ls -la profile_urls.txt

# Kopiera från backup om nödvändigt
cp backup/profile_urls.txt .
```

### Om 403-fel kvarstår:
1. Öka delay: `-s DOWNLOAD_DELAY=15`
2. Använd proxy: Lägg till proxy-konfiguration
3. Kontrollera IP-status: Kör IP-test

### Om inga bilder hittas:
- Kontrollera image-selektorer i spider
- Verifiera att målsidorna har bilder
- Kontrollera nätverksanslutning

## 📊 Förväntade Resultat

Med denna metod bör du få:
- **200 OK** istället för 403 Forbidden
- **Framgångsrik bildnedladdning** från profiler
- **Minimal risk för blockering** (distribuerade requests)
- **Hög success rate** (>90% av profiler)

## 🎉 Slutsats

URL-baserade scrapern löser det ursprungliga 403-problemet genom att helt undvika den blockerade huvudsidan. Kombinerat med det avancerade anti-blocking-systemet ger detta en robust och effektiv scraping-lösning.


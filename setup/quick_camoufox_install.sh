#!/bin/bash

# Snabb Camoufox-installation för doppelganger scraper
echo "🦊 Installerar Camoufox-integration..."

# Kontrollera att vi är i rätt katalog
if [ ! -f "scrapy.cfg" ]; then
    echo "❌ Fel: Kör detta script från doppelganger root-katalogen"
    exit 1
fi

# Backup befintliga filer
echo "📦 Skapar backup..."
cp doppelganger/settings.py doppelganger/settings.py.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
cp requirements.txt requirements.txt.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
cp run_scraper.sh run_scraper.sh.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

echo "📁 Skapar Camoufox middleware..."

# Skapa Camoufox middleware
cat > doppelganger/middlewares_camoufox.py << 'EOF'
"""
Camoufox Middleware för att kringgå Cloudflare bot-protection
"""

import time
import random
import logging
from urllib.parse import urlparse
from scrapy.http import HtmlResponse
from scrapy.exceptions import NotConfigured
import requests

logger = logging.getLogger(__name__)

class CamoufoxMiddleware:
    def __init__(self, crawler):
        self.crawler = crawler
        self.settings = crawler.settings
        
        self.camoufox_enabled = self.settings.getbool('CAMOUFOX_ENABLED', True)
        self.camoufox_host = self.settings.get('CAMOUFOX_HOST', 'camoufox-server')
        self.camoufox_port = self.settings.getint('CAMOUFOX_PORT', 4444)
        
        self.page_load_timeout = self.settings.getint('CAMOUFOX_PAGE_LOAD_TIMEOUT', 30)
        self.cloudflare_wait_time = self.settings.getint('CAMOUFOX_CLOUDFLARE_WAIT', 15)
        self.human_delay_min = self.settings.getint('CAMOUFOX_HUMAN_DELAY_MIN', 2)
        self.human_delay_max = self.settings.getint('CAMOUFOX_HUMAN_DELAY_MAX', 8)
        
        self.cf_clearance_cache = {}
        self.session_cookies = {}
        
        if not self.camoufox_enabled:
            raise NotConfigured('Camoufox middleware är inaktiverat')
            
        logger.info(f"🦊 Camoufox Middleware aktiverat - {self.camoufox_host}:{self.camoufox_port}")
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)
    
    def process_request(self, request, spider):
        if not self.camoufox_enabled:
            return None
            
        try:
            domain = urlparse(request.url).netloc
            if self._has_valid_clearance(domain):
                logger.debug(f"🍪 Använder cachad cf_clearance för {domain}")
                return self._make_request_with_cookies(request)
            
            logger.info(f"🦊 Använder Camoufox för {request.url}")
            response = self._fetch_with_camoufox(request, spider)
            
            if response:
                return response
                
        except Exception as e:
            logger.error(f"❌ Camoufox fel för {request.url}: {e}")
            return None
    
    def _has_valid_clearance(self, domain):
        if domain not in self.cf_clearance_cache:
            return False
            
        cookie_data = self.cf_clearance_cache[domain]
        if time.time() - cookie_data['timestamp'] > 1800:
            del self.cf_clearance_cache[domain]
            return False
            
        return True
    
    def _make_request_with_cookies(self, request):
        domain = urlparse(request.url).netloc
        
        if domain not in self.session_cookies:
            return None
            
        try:
            session = requests.Session()
            
            for cookie in self.session_cookies[domain]:
                session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            if '/pornstars/' in request.url and '/index.php' in request.url:
                headers['Referer'] = f"https://{domain}/pornstars/index.php"
            
            response = session.get(request.url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"✅ Framgångsrik request med cookies: {request.url}")
                return HtmlResponse(
                    url=request.url,
                    body=response.content,
                    encoding='utf-8',
                    request=request
                )
            else:
                logger.warning(f"⚠️ HTTP {response.status_code} med cookies: {request.url}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Cookie request fel: {e}")
            return None
    
    def _fetch_with_camoufox(self, request, spider):
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.firefox.options import Options
            
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            
            driver = webdriver.Remote(
                command_executor=f'http://{self.camoufox_host}:{self.camoufox_port}/wd/hub',
                options=options
            )
            
            try:
                logger.info(f"🦊 Navigerar till {request.url}")
                driver.get(request.url)
                
                WebDriverWait(driver, self.page_load_timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                if self._handle_cloudflare_challenge(driver):
                    logger.info("🛡️ Cloudflare challenge hanterat")
                
                self._simulate_human_behavior(driver)
                self._save_cookies(driver, request.url)
                
                page_source = driver.page_source
                
                logger.info(f"✅ Camoufox framgångsrik: {request.url}")
                
                return HtmlResponse(
                    url=request.url,
                    body=page_source.encode('utf-8'),
                    encoding='utf-8',
                    request=request
                )
                
            finally:
                driver.quit()
                
        except ImportError:
            logger.error("❌ Selenium inte installerat")
            return None
        except Exception as e:
            logger.error(f"❌ Camoufox fel: {e}")
            return None
    
    def _handle_cloudflare_challenge(self, driver):
        try:
            time.sleep(2)
            
            cloudflare_indicators = [
                "Checking your browser before accessing",
                "DDoS protection by Cloudflare",
                "cf-browser-verification",
                "cf-challenge-running"
            ]
            
            page_source = driver.page_source.lower()
            is_cloudflare_challenge = any(indicator.lower() in page_source for indicator in cloudflare_indicators)
            
            if is_cloudflare_challenge:
                logger.info("🛡️ Cloudflare challenge detekterat, väntar...")
                
                max_wait = self.cloudflare_wait_time
                for i in range(max_wait):
                    time.sleep(1)
                    page_source = driver.page_source.lower()
                    
                    if not any(indicator.lower() in page_source for indicator in cloudflare_indicators):
                        logger.info(f"✅ Cloudflare challenge löst efter {i+1} sekunder")
                        return True
                
                logger.warning("⚠️ Cloudflare challenge tog för lång tid")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Cloudflare challenge fel: {e}")
            return False
    
    def _simulate_human_behavior(self, driver):
        try:
            delay = random.uniform(self.human_delay_min, self.human_delay_max)
            time.sleep(delay)
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
            time.sleep(random.uniform(0.5, 1.5))
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(random.uniform(0.5, 1.5))
            
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(random.uniform(0.5, 1.0))
            
        except Exception as e:
            logger.debug(f"Mänskligt beteende simulation fel: {e}")
    
    def _save_cookies(self, driver, url):
        try:
            domain = urlparse(url).netloc
            cookies = driver.get_cookies()
            
            self.session_cookies[domain] = cookies
            
            for cookie in cookies:
                if cookie['name'] == 'cf_clearance':
                    self.cf_clearance_cache[domain] = {
                        'value': cookie['value'],
                        'timestamp': time.time()
                    }
                    logger.info(f"🍪 cf_clearance cookie sparad för {domain}")
                    break
            
        except Exception as e:
            logger.error(f"❌ Cookie sparning fel: {e}")


class CamoufoxDownloaderMiddleware:
    def __init__(self, settings):
        self.enabled = settings.getbool('CAMOUFOX_ENABLED', False)
        self.stats = {}
        
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)
    
    def process_request(self, request, spider):
        if not self.enabled:
            return None
            
        request.headers.setdefault('User-Agent', 
            'Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0')
        request.headers.setdefault('Accept', 
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8')
        request.headers.setdefault('Accept-Language', 'en-US,en;q=0.5')
        request.headers.setdefault('Accept-Encoding', 'gzip, deflate, br, zstd')
        request.headers.setdefault('DNT', '1')
        request.headers.setdefault('Connection', 'keep-alive')
        request.headers.setdefault('Upgrade-Insecure-Requests', '1')
        
        return None
    
    def process_response(self, request, response, spider):
        status = response.status
        if status not in self.stats:
            self.stats[status] = 0
        self.stats[status] += 1
        
        if status == 403:
            logger.warning(f"🚫 403 Forbidden: {request.url}")
        elif status == 200:
            logger.info(f"✅ 200 OK: {request.url}")
            
        return response
EOF

echo "📋 Uppdaterar requirements.txt..."

# Lägg till Selenium i requirements.txt
if ! grep -q "selenium" requirements.txt; then
    echo "selenium>=4.15.0" >> requirements.txt
    echo "webdriver-manager>=4.0.0" >> requirements.txt
fi

echo "🐳 Uppdaterar docker-compose.yml..."

# Backup och uppdatera docker-compose.yml
cat > docker-compose.yml << 'EOF'
services:
  doppelganger-scraper:
    build: .
    volumes:
      - ./crawls:/app/crawls
      - ./images:/app/images
      - ./logs:/app/logs
      - ./profile_urls.txt:/app/profile_urls.txt:ro
    environment:
      - SCRAPY_SETTINGS_MODULE=doppelganger.settings
      - PYTHONPATH=/app
    networks:
      - scraper-network
    depends_on:
      - camoufox-server

  camoufox-scraper:
    build: .
    volumes:
      - ./crawls:/app/crawls
      - ./images:/app/images
      - ./logs:/app/logs
      - ./profile_urls.txt:/app/profile_urls.txt:ro
    environment:
      - SCRAPY_SETTINGS_MODULE=doppelganger.settings
      - PYTHONPATH=/app
      - CAMOUFOX_ENABLED=true
      - CAMOUFOX_HOST=camoufox-server
      - CAMOUFOX_PORT=4444
    networks:
      - scraper-network
    depends_on:
      - camoufox-server

  camoufox-server:
    image: selenium/standalone-firefox:latest
    ports:
      - "9224:4444"
    environment:
      - SE_NODE_MAX_SESSIONS=2
      - SE_NODE_SESSION_TIMEOUT=300
    shm_size: 2gb
    networks:
      - scraper-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4444/wd/hub/status"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  scraper-network:
    driver: bridge
EOF

echo "⚙️ Uppdaterar settings.py..."

# Lägg till Camoufox-inställningar i settings.py
cat >> doppelganger/settings.py << 'EOF'

# Camoufox-specifika inställningar
CAMOUFOX_ENABLED = True
CAMOUFOX_HOST = 'camoufox-server'
CAMOUFOX_PORT = 4444

CAMOUFOX_PAGE_LOAD_TIMEOUT = 30
CAMOUFOX_CLOUDFLARE_WAIT = 15
CAMOUFOX_HUMAN_DELAY_MIN = 2
CAMOUFOX_HUMAN_DELAY_MAX = 8

DOWNLOADER_MIDDLEWARES.update({
    'doppelganger.middlewares_camoufox.CamoufoxMiddleware': 543,
    'doppelganger.middlewares_camoufox.CamoufoxDownloaderMiddleware': 544,
})

DOWNLOAD_DELAY = 8
RANDOMIZE_DOWNLOAD_DELAY = 0.5
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1

RETRY_TIMES = 3
RETRY_HTTP_CODES = [403, 429, 500, 502, 503, 504, 522, 524]

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 8
AUTOTHROTTLE_MAX_DELAY = 30
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

COOKIES_ENABLED = True
COOKIES_DEBUG = True

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0'

DOWNLOADER_MIDDLEWARES.update({
    'doppelganger.middlewares_chrome.ChromeHeadlessMiddleware': None,
    'doppelganger.middlewares_chrome.ChromeDevToolsMiddleware': None,
    'doppelganger.middlewares_chrome.SuperSimpleChromeMiddleware': None,
})

print("🦊 Camoufox-konfiguration laddad!")
print(f"   Host: {CAMOUFOX_HOST}:{CAMOUFOX_PORT}")
print(f"   Delay: {DOWNLOAD_DELAY}s")
print(f"   Cloudflare wait: {CAMOUFOX_CLOUDFLARE_WAIT}s")
EOF

echo "🚀 Uppdaterar run_scraper.sh..."

# Lägg till Camoufox-funktioner i run_scraper.sh
cat >> run_scraper.sh << 'EOF'

# Camoufox-specifika funktioner
camoufox_test() {
    echo "🦊 Testar Camoufox-integration..."
    docker-compose up -d camoufox-server
    sleep 10
    
    echo "🧪 Testar scraping med Camoufox (1 profil)..."
    docker-compose run --rm camoufox-scraper scrapy crawl mpb_from_urls \
        -s CLOSESPIDER_ITEMCOUNT=1 \
        -s CAMOUFOX_ENABLED=True \
        -s LOG_LEVEL=INFO \
        -s DOWNLOAD_DELAY=10
}

camoufox_sample() {
    echo "🦊 Scrapar 10 profiler med Camoufox..."
    docker-compose up -d camoufox-server
    sleep 5
    
    docker-compose run --rm camoufox-scraper scrapy crawl mpb_from_urls \
        -s CLOSESPIDER_ITEMCOUNT=10 \
        -s CAMOUFOX_ENABLED=True \
        -s LOG_LEVEL=INFO \
        -s DOWNLOAD_DELAY=8
}

camoufox_run() {
    echo "🦊 Scrapar alla profiler med Camoufox..."
    echo "⚠️ Detta kommer att ta mycket lång tid (6360 profiler)"
    read -p "Är du säker? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose up -d camoufox-server
        sleep 5
        
        docker-compose run --rm camoufox-scraper scrapy crawl mpb_from_urls \
            -s CAMOUFOX_ENABLED=True \
            -s LOG_LEVEL=INFO \
            -s DOWNLOAD_DELAY=8
    else
        echo "Avbrutet."
    fi
}

camoufox_debug() {
    echo "🦊 Debug-läge för Camoufox..."
    docker-compose up -d camoufox-server
    sleep 5
    
    docker-compose run --rm camoufox-scraper scrapy crawl mpb_from_urls \
        -s CLOSESPIDER_ITEMCOUNT=1 \
        -s CAMOUFOX_ENABLED=True \
        -s LOG_LEVEL=DEBUG \
        -s DOWNLOAD_DELAY=15 \
        -s CAMOUFOX_CLOUDFLARE_WAIT=20
}

camoufox_verify() {
    echo "🔍 Verifierar Camoufox-installation..."
    docker-compose up -d camoufox-server
    sleep 10
    
    echo "🦊 Kontrollerar Camoufox-server..."
    if docker-compose exec camoufox-server curl -s http://localhost:4444/wd/hub/status > /dev/null 2>&1; then
        echo "✅ Camoufox-server fungerar"
    else
        echo "❌ Camoufox-server svarar inte"
    fi
}

camoufox_stop() {
    echo "🛑 Stoppar Camoufox-server..."
    docker-compose stop camoufox-server
}

camoufox_logs() {
    echo "📋 Visar Camoufox-server loggar..."
    docker-compose logs camoufox-server
}
EOF

# Uppdatera case-statement i run_scraper.sh
sed -i '/^case "\${1:-help}" in$/,/^esac$/ {
    /^esac$/ i\
    "camoufox_test")\
        camoufox_test\
        ;;\
    "camoufox_sample")\
        camoufox_sample\
        ;;\
    "camoufox_run")\
        camoufox_run\
        ;;\
    "camoufox_debug")\
        camoufox_debug\
        ;;\
    "camoufox_verify")\
        camoufox_verify\
        ;;\
    "camoufox_stop")\
        camoufox_stop\
        ;;\
    "camoufox_logs")\
        camoufox_logs\
        ;;
}' run_scraper.sh

echo ""
echo "🎉 Camoufox-integration installerad!"
echo ""
echo "📋 Nästa steg:"
echo "1. ./run_scraper.sh build"
echo "2. ./run_scraper.sh camoufox_test"
echo ""
echo "🦊 Camoufox-servern startas automatiskt!"


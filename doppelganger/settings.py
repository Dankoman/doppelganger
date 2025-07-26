# -*- coding: utf-8 -*-

# Enhanced Scrapy settings for doppelganger project with advanced anti-blocking

BOT_NAME = 'doppelganger'

SPIDER_MODULES = ['doppelganger.spiders']
NEWSPIDER_MODULE = 'doppelganger.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Obey robots.txt rules (disabled for scraping)
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (very conservative)
CONCURRENT_REQUESTS = 1

# Configure a delay for requests for the same website
DOWNLOAD_DELAY = 5.0  # Ökat till 5 sekunder
RANDOMIZE_DOWNLOAD_DELAY = 0.5  # Randomisera ±50%

# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 1
CONCURRENT_REQUESTS_PER_IP = 1

# Disable cookies (enabled by default) - vi hanterar detta manuellt
COOKIES_ENABLED = True

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

MEDIA_ALLOW_REDIRECTS = True

# Aktivera jobb-katalog för återupptagning
JOBDIR = 'crawls/book-3'

# Override the default request headers med mer realistiska värden
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,sv-SE;q=0.8,sv;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

# Enable or disable spider middlewares
SPIDER_MIDDLEWARES = {
    'doppelganger.middlewares.DoppelgangerSpiderMiddleware': 543,
}

# Enable or disable downloader middlewares med förbättrade klasser
DOWNLOADER_MIDDLEWARES = {
    'doppelganger.middlewares.EnhancedUserAgentMiddleware': 400,
    'doppelganger.middlewares.AdvancedAntiBlockingMiddleware': 543,
    'doppelganger.middlewares.EnhancedRetryMiddleware': 550,
}

# Anti-blocking inställningar (förbättrade)
ANTIBLOCK_ENABLED = True
ANTIBLOCK_DELAY_RANGE = (3, 10)  # Längre fördröjningar

# Retry-inställningar
RETRY_ENABLED = True
RETRY_TIMES = 5  # Fler försök
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429, 403]  # Inkludera 403
RETRY_PRIORITY_ADJUST = -1

# Download timeout
DOWNLOAD_TIMEOUT = 30

# Enable or disable extensions
EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,
}

# Configure item pipelines
ITEM_PIPELINES = {
    "doppelganger.pipelines.PerformerImagePipeline": 1,
}

IMAGES_STORE = '/app/images'

# Enable and configure the AutoThrottle extension (mycket konservativt)
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5  # Starta med 5 sekunder
AUTOTHROTTLE_MAX_DELAY = 60   # Max 60 sekunder
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5  # Mycket låg concurrency
AUTOTHROTTLE_DEBUG = True  # Visa throttling-statistik

# Enable and configure HTTP caching (för att minska requests)
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600  # Cache i 1 timme
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [403, 404, 500, 503]

# Logging
LOG_LEVEL = 'INFO'

# Request fingerprinting (för att undvika duplicates)
DUPEFILTER_DEBUG = True

# Memory usage extension
MEMUSAGE_ENABLED = True
MEMUSAGE_LIMIT_MB = 2048
MEMUSAGE_WARNING_MB = 1024

# Close spider on various conditions
CLOSESPIDER_TIMEOUT = 3600  # Stäng efter 1 timme
CLOSESPIDER_ITEMCOUNT = 1000  # Eller efter 1000 items
CLOSESPIDER_PAGECOUNT = 500   # Eller efter 500 sidor
CLOSESPIDER_ERRORCOUNT = 50   # Eller efter 50 fel

# DNS timeout
DNSCACHE_ENABLED = True
DNSCACHE_SIZE = 10000
DNS_TIMEOUT = 60

# Reactor settings
REACTOR_THREADPOOL_MAXSIZE = 20

# Ajaxcrawl settings (för JavaScript-heavy sites)
AJAXCRAWL_ENABLED = False

# Compression
COMPRESSION_ENABLED = True

# Stats
STATS_CLASS = 'scrapy.statscollectors.MemoryStatsCollector'


# Chrome Headless Settings
# Ansluter till befintliga chromedp/headless-shell Docker-instanser

# Chrome-konfiguration
CHROME_HOST = '192.168.0.50'
CHROME_PORT = 9222  # Primär port
CHROME_PORTS = [9222, 9223]  # För load balancing mellan instanser
CHROME_ENABLED = False  # Aktiveras med -s CHROME_ENABLED=True

# Chrome middleware (aktiveras endast när CHROME_ENABLED=True)
# Lägg till i DOWNLOADER_MIDDLEWARES när Chrome används
CHROME_MIDDLEWARE = {
    'doppelganger.middlewares_chrome.SuperSimpleChromeMiddleware': 585,
}

# Chrome-specifika inställningar
CHROME_TIMEOUT = 30
CHROME_PAGE_LOAD_TIMEOUT = 20
CHROME_IMPLICIT_WAIT = 10

# Justera inställningar för Chrome-användning
CHROME_DOWNLOAD_DELAY = 8  # Längre delay för Chrome
CHROME_CONCURRENT_REQUESTS = 1  # En åt gången för Chrome
CHROME_RETRY_TIMES = 3  # Färre retries eftersom Chrome är mer tillförlitlig

DOWNLOADER_MIDDLEWARES['doppelganger.middlewares_chrome.SuperSimpleChromeMiddleware'] = 585

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

# FÖRBÄTTRADE Camoufox timeout-inställningar för att förhindra hanging
CAMOUFOX_PAGE_LOAD_TIMEOUT = 15      # Kortare sidladdning timeout
CAMOUFOX_CLOUDFLARE_WAIT = 10        # Kortare Cloudflare wait
CAMOUFOX_WEBDRIVER_TIMEOUT = 10      # WebDriver timeout
CAMOUFOX_CONNECTION_TIMEOUT = 5      # HTTP connection timeout
CAMOUFOX_HUMAN_DELAY_MIN = 1         # Kortare minimum delay
CAMOUFOX_HUMAN_DELAY_MAX = 3         # Kortare maximum delay

print("🔧 Förbättrade Camoufox timeout-inställningar laddade!")
print(f"   Page load timeout: {CAMOUFOX_PAGE_LOAD_TIMEOUT}s")
print(f"   WebDriver timeout: {CAMOUFOX_WEBDRIVER_TIMEOUT}s")
print(f"   Connection timeout: {CAMOUFOX_CONNECTION_TIMEOUT}s")

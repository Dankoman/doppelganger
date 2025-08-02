# -*- coding: utf-8 -*-

BOT_NAME = 'doppelganger'

SPIDER_MODULES = ['doppelganger.spiders']
NEWSPIDER_MODULE = 'doppelganger.spiders'

# Crawl responsibly by identifying dig på user‐agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Ignorera robots.txt
ROBOTSTXT_OBEY = False

# ‣ Concurrency & delays
DOWNLOAD_DELAY = 4
RANDOMIZE_DOWNLOAD_DELAY = True
CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 2
CONCURRENT_REQUESTS_PER_IP = 2

# ‣ Cookies
COOKIES_ENABLED = True
COOKIES_DEBUG = False

# ‣ Media redirects
MEDIA_ALLOW_REDIRECTS = True

# ‣ Jobdir för återupptagning
JOBDIR = 'crawls/book-ppics'

# ‣ Standard‐headers
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

# ‣ Spider middlewares
SPIDER_MIDDLEWARES = {
    'doppelganger.middlewares.DoppelgangerSpiderMiddleware': 543,
}

# ‣ Downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    'doppelganger.middlewares.EnhancedUserAgentMiddleware': 400,
    'doppelganger.middlewares_proxy.ProxyRotatorMiddleware': None,
    'doppelganger.middlewares.AdvancedAntiBlockingMiddleware': 543,
    'doppelganger.middlewares.EnhancedRetryMiddleware': 550,
}

# ‣ Anti-blocking
ANTIBLOCK_ENABLED = True
ANTIBLOCK_DELAY_RANGE = (3, 10)

# ‣ Proxy
PROXY_LIST_PATH = '/home/ubuntu/doppelganger/proxy/proxies.txt'
PROXY_ENABLED = False

# ‣ Retry
RETRY_ENABLED = True
RETRY_TIMES = 5
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429, 403]
RETRY_PRIORITY_ADJUST = -1

# ‣ Timeouts
DOWNLOAD_TIMEOUT = 30

# ‣ AutoThrottle
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 20
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
AUTOTHROTTLE_DEBUG = False

# ‣ HTTP caching
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [403, 404, 500, 503]

# ‣ Extensions
EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,
}

# ‣ Pipelines & bildlagring
ITEM_PIPELINES = {
    'doppelganger.pipelines.PerformerImagePipeline': 1,
}
IMAGES_STORE = '/root/doppelganger/images-ppic'

# ‣ Loggning
LOG_LEVEL = 'INFO'
DUPEFILTER_DEBUG = True

# ‣ Minne
MEMUSAGE_ENABLED = True
MEMUSAGE_LIMIT_MB = 2048
MEMUSAGE_WARNING_MB = 1024

# ‣ Stäng spider vid villkor
#CLOSESPIDER_TIMEOUT = 3600
#CLOSESPIDER_ITEMCOUNT = 2000
#CLOSESPIDER_PAGECOUNT = 500
CLOSESPIDER_ERRORCOUNT = 2

# ‣ DNS & reactor
DNSCACHE_ENABLED = True
DNSCACHE_SIZE = 10000
DNS_TIMEOUT = 60
REACTOR_THREADPOOL_MAXSIZE = 20

# --- Lokal Camoufox-konfiguration ---
CAMOUFOX_ENABLED = True
CAMOUFOX_PAGE_LOAD_TIMEOUT = 30      # sekunder
CAMOUFOX_CLOUDFLARE_WAIT = 15        # sekunder
CAMOUFOX_HUMAN_DELAY_MIN = 2         # sekunder
CAMOUFOX_HUMAN_DELAY_MAX = 8         # sekunder

# Om du vill aktivera lokal Camoufox middleware, avkommentera nedan:
# DOWNLOADER_MIDDLEWARES.update({
#     'doppelganger.middlewares_camoufox_local.CamoufoxLocalMiddleware': 543,
#     'doppelganger.middlewares_camoufox_local.CamoufoxLocalDownloaderMiddleware': 544,
# })

print("🦊 Lokal Camoufox-konfiguration laddad!")
print(f"   Lokal installation aktiverad")
print(f"   Delay: {DOWNLOAD_DELAY}s")
print(f"   Cloudflare wait: {CAMOUFOX_CLOUDFLARE_WAIT}s")

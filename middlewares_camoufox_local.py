"""
Camoufox Middleware för att kringgå Cloudflare bot-protection
Använder lokal Camoufox installation istället för Docker Compose
"""

import time
import random
import logging
import asyncio
from urllib.parse import urlparse
from scrapy.http import HtmlResponse
from scrapy.exceptions import NotConfigured

logger = logging.getLogger(__name__)

class CamoufoxLocalMiddleware:
    """
    Middleware som använder lokal Camoufox för att kringgå Cloudflare bot-protection
    """
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.settings = crawler.settings
        
        # Camoufox konfiguration
        self.camoufox_enabled = self.settings.getbool('CAMOUFOX_ENABLED', True)
        
        # Anti-detection inställningar
        self.page_load_timeout = self.settings.getint('CAMOUFOX_PAGE_LOAD_TIMEOUT', 30)
        self.cloudflare_wait_time = self.settings.getint('CAMOUFOX_CLOUDFLARE_WAIT', 15)
        self.human_delay_min = self.settings.getint('CAMOUFOX_HUMAN_DELAY_MIN', 2)
        self.human_delay_max = self.settings.getint('CAMOUFOX_HUMAN_DELAY_MAX', 8)
        
        # Session hantering
        self.cf_clearance_cache = {}
        self.session_cookies = {}
        self.failed_attempts = 0
        self.max_failed_attempts = 3
        
        if not self.camoufox_enabled:
            raise NotConfigured('Camoufox middleware är inaktiverat')
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)
    
    def process_request(self, request, spider):
        """Bearbeta request med lokal Camoufox"""
        
        if not self.camoufox_enabled:
            return None
        
        if self.failed_attempts >= self.max_failed_attempts:
            logger.warning(f"🚫 Camoufox inaktiverat efter {self.failed_attempts} misslyckade försök")
            return None
        
        try:
            # Kontrollera om vi redan har en giltig cf_clearance cookie
            domain = urlparse(request.url).netloc
            if self._has_valid_clearance(domain):
                logger.debug(f"🍪 Använder cachad cf_clearance för {domain}")
                return self._make_request_with_cookies(request)
            
            # Använd lokal Camoufox för att hämta sidan och hantera Cloudflare
            logger.info(f"🦊 Använder lokal Camoufox för {request.url}")
            
            # Kör async Camoufox i sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(self._fetch_with_camoufox_async(request, spider))
            finally:
                loop.close()
            
            if response:
                self.failed_attempts = 0
                return response
            else:
                self.failed_attempts += 1
                logger.warning(f"⚠️ Camoufox misslyckades ({self.failed_attempts}/{self.max_failed_attempts})")
                return None
                
        except Exception as e:
            self.failed_attempts += 1
            logger.error(f"❌ Camoufox fel för {request.url}: {e}")
            return None
    
    def _has_valid_clearance(self, domain):
        """Kontrollera om vi har en giltig cf_clearance cookie"""
        if domain not in self.cf_clearance_cache:
            return False
        
        cookie_data = self.cf_clearance_cache[domain]
        if time.time() - cookie_data['timestamp'] > 1800:  # 30 minuter
            del self.cf_clearance_cache[domain]
            return False
        
        return True
    
    def _make_request_with_cookies(self, request):
        """Gör HTTP request med sparade cookies"""
        domain = urlparse(request.url).netloc
        
        if domain not in self.session_cookies:
            return None
        
        try:
            import requests
            session = requests.Session()
            
            # Lägg till sparade cookies
            for cookie in self.session_cookies[domain]:
                session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain', domain))
            
            # Lägg till realistiska headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Priority': 'u=1'
            }
            
            # Lägg till referer om det är en profil-URL
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
    
    async def _fetch_with_camoufox_async(self, request, spider):
        """Hämta sida med lokal Camoufox browser (async)"""
        try:
            from camoufox.async_api import AsyncCamoufox
        except ImportError:
            logger.error("❌ Camoufox inte installerat. Kör: pip install camoufox[geoip]")
            return None
        
        try:
            # Skapa Camoufox browser instance med korrekt async syntax
            async with AsyncCamoufox(
                headless=True,
                geoip=True,
                os='linux',
                humanize=True,  # Humanisera cursor movement
                # Proxy kan konfigureras här om behövs
                # proxy={'server': 'http://proxy:port', 'username': 'user', 'password': 'pass'}
            ) as browser:
                logger.info(f"🦊 Camoufox browser startad för {request.url}")
                
                # Skapa ny sida
                page = await browser.new_page()
                
                # Sätt timeout
                page.set_default_timeout(self.page_load_timeout * 1000)  # millisekunder
                
                try:
                    logger.info(f"🌐 Navigerar till {request.url}")
                    start_time = time.time()
                    
                    # Navigera till sidan
                    await page.goto(request.url, wait_until='domcontentloaded')
                    
                    load_time = time.time() - start_time
                    logger.info(f"⏱️ Sida laddad på {load_time:.2f}s")
                    
                    # Kontrollera för Cloudflare challenge
                    if await self._handle_cloudflare_challenge_async(page):
                        logger.info("🛡️ Cloudflare challenge hanterat")
                    
                    # Simulera mänskligt beteende
                    await self._simulate_human_behavior_async(page)
                    
                    # Hämta cookies (speciellt cf_clearance)
                    await self._save_cookies_async(page, request.url)
                    
                    # Hämta sidans innehåll
                    content = await page.content()
                    
                    logger.info(f"✅ Camoufox framgångsrik: {request.url} ({len(content)} tecken)")
                    
                    return HtmlResponse(
                        url=request.url,
                        body=content.encode('utf-8'),
                        encoding='utf-8',
                        request=request
                    )
                    
                except Exception as e:
                    logger.error(f"❌ Sida-fel för {request.url}: {e}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Camoufox browser-fel: {e}")
            return None
    
    async def _handle_cloudflare_challenge_async(self, page):
        """Hantera Cloudflare challenge (async)"""
        try:
            # Kolla efter Cloudflare challenge
            challenge_selectors = [
                '[data-ray]',
                '.cf-browser-verification',
                '.cf-checking-browser',
                '#challenge-form',
                '.cf-challenge-running'
            ]
            
            for selector in challenge_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    logger.info("🛡️ Cloudflare challenge upptäckt - väntar...")
                    
                    # Vänta tills challenge är klar
                    await asyncio.sleep(self.cloudflare_wait_time)
                    
                    # Kontrollera om challenge fortfarande finns
                    remaining_elements = await page.query_selector_all(selector)
                    if not remaining_elements:
                        logger.info("✅ Cloudflare challenge klarad")
                        return True
                    else:
                        logger.warning("⚠️ Cloudflare challenge kvarstår")
                        # Vänta lite till
                        await asyncio.sleep(5)
                        return True
                        
        except Exception as e:
            logger.warning(f"⚠️ Cloudflare challenge hantering fel: {e}")
        
        return False
    
    async def _simulate_human_behavior_async(self, page):
        """Simulera mänskligt beteende (async)"""
        try:
            # Slumpmässig delay
            delay = random.uniform(self.human_delay_min, self.human_delay_max)
            await asyncio.sleep(delay)
            
            # Scrolla lite för att simulera läsning
            await page.evaluate("window.scrollTo(0, Math.floor(Math.random() * 500));")
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Scrolla tillbaka upp
            await page.evaluate("window.scrollTo(0, 0);")
            await asyncio.sleep(random.uniform(0.3, 1.0))
            
        except Exception as e:
            logger.debug(f"Simulering av mänskligt beteende fel: {e}")
    
    async def _save_cookies_async(self, page, url):
        """Spara cookies för framtida användning (async)"""
        try:
            domain = urlparse(url).netloc
            cookies = await page.context.cookies()
            
            # Filtrera cookies för denna domain
            domain_cookies = [
                cookie for cookie in cookies 
                if domain in cookie.get('domain', '') or cookie.get('domain', '').startswith('.')
            ]
            
            # Spara alla cookies
            self.session_cookies[domain] = domain_cookies
            
            # Spara cf_clearance specifikt
            for cookie in domain_cookies:
                if cookie['name'] == 'cf_clearance':
                    self.cf_clearance_cache[domain] = {
                        'value': cookie['value'],
                        'timestamp': time.time()
                    }
                    logger.info(f"🍪 cf_clearance cookie sparad för {domain}")
                    break
                    
        except Exception as e:
            logger.warning(f"Cookie sparning fel: {e}")
    
    def spider_closed(self, spider):
        """Cleanup när spider stängs"""
        logger.info("🔒 Camoufox middleware stängd")


class CamoufoxLocalDownloaderMiddleware:
    """
    Downloader middleware för lokal Camoufox integration
    """
    
    def __init__(self, settings):
        self.camoufox_enabled = settings.getbool('CAMOUFOX_ENABLED', True)
        
        if self.camoufox_enabled:
            logger.info("🦊 Camoufox Lokal Downloader Middleware aktiverat")
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)
    
    def process_request(self, request, spider):
        """Process requests through local Camoufox if needed"""
        # Denna middleware arbetar tillsammans med CamoufoxLocalMiddleware
        return None


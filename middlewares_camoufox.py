"""
Camoufox Middleware för att kringgå Cloudflare bot-protection
Använder Camoufox browser för att automatiskt hantera cf_clearance cookies
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
    """
    Middleware som använder Camoufox för att kringgå Cloudflare bot-protection
    """
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.settings = crawler.settings
        
        # Camoufox konfiguration
        self.camoufox_enabled = self.settings.getbool('CAMOUFOX_ENABLED', True)
        self.camoufox_host = self.settings.get('CAMOUFOX_HOST', 'camoufox-server')
        self.camoufox_port = self.settings.getint('CAMOUFOX_PORT', 4444)
        
        # Anti-detection inställningar
        self.page_load_timeout = self.settings.getint('CAMOUFOX_PAGE_LOAD_TIMEOUT', 30)
        self.cloudflare_wait_time = self.settings.getint('CAMOUFOX_CLOUDFLARE_WAIT', 15)
        self.human_delay_min = self.settings.getint('CAMOUFOX_HUMAN_DELAY_MIN', 2)
        self.human_delay_max = self.settings.getint('CAMOUFOX_HUMAN_DELAY_MAX', 8)
        
        # Session hantering
        self.cf_clearance_cache = {}
        self.session_cookies = {}
        
        if not self.camoufox_enabled:
            raise NotConfigured('Camoufox middleware är inaktiverat')
            
        logger.info(f"🦊 Camoufox Middleware aktiverat - {self.camoufox_host}:{self.camoufox_port}")
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)
    
    def process_request(self, request, spider):
        """Bearbeta request med Camoufox"""
        
        if not self.camoufox_enabled:
            return None
            
        try:
            # Kontrollera om vi redan har en giltig cf_clearance cookie
            domain = urlparse(request.url).netloc
            if self._has_valid_clearance(domain):
                logger.debug(f"🍪 Använder cachad cf_clearance för {domain}")
                return self._make_request_with_cookies(request)
            
            # Använd Camoufox för att hämta sidan och hantera Cloudflare
            logger.info(f"🦊 Använder Camoufox för {request.url}")
            response = self._fetch_with_camoufox(request, spider)
            
            if response:
                return response
                
        except Exception as e:
            logger.error(f"❌ Camoufox fel för {request.url}: {e}")
            # Fallback till vanlig HTTP request
            return None
    
    def _has_valid_clearance(self, domain):
        """Kontrollera om vi har en giltig cf_clearance cookie"""
        if domain not in self.cf_clearance_cache:
            return False
            
        cookie_data = self.cf_clearance_cache[domain]
        # Kontrollera om cookie är för gammal (Cloudflare cookies varar vanligtvis 30 min)
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
            session = requests.Session()
            
            # Lägg till sparade cookies
            for cookie in self.session_cookies[domain]:
                session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
            
            # Lägg till realistiska headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'DNT': '1',
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
    
    def _fetch_with_camoufox(self, request, spider):
        """Hämta sida med Camoufox browser"""
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.firefox.options import Options
            
            # Camoufox options
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            # Anslut till remote Camoufox
            driver = webdriver.Remote(
                command_executor=f'http://{self.camoufox_host}:{self.camoufox_port}/wd/hub',
                options=options
            )
            
            try:
                logger.info(f"🦊 Navigerar till {request.url}")
                driver.get(request.url)
                
                # Vänta på att sidan laddas
                WebDriverWait(driver, self.page_load_timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Kontrollera för Cloudflare challenge
                if self._handle_cloudflare_challenge(driver):
                    logger.info("🛡️ Cloudflare challenge hanterat")
                
                # Simulera mänskligt beteende
                self._simulate_human_behavior(driver)
                
                # Hämta cookies (speciellt cf_clearance)
                self._save_cookies(driver, request.url)
                
                # Hämta sidans innehåll
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
            logger.error("❌ Selenium inte installerat. Kör: pip install selenium")
            return None
        except Exception as e:
            logger.error(f"❌ Camoufox fel: {e}")
            return None
    
    def _handle_cloudflare_challenge(self, driver):
        """Hantera Cloudflare bot challenge"""
        try:
            # Vänta på Cloudflare challenge att visas
            time.sleep(2)
            
            # Kontrollera för Cloudflare challenge indikatorer
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
                
                # Vänta på att challenge löses automatiskt
                max_wait = self.cloudflare_wait_time
                for i in range(max_wait):
                    time.sleep(1)
                    current_url = driver.current_url
                    page_source = driver.page_source.lower()
                    
                    # Kontrollera om vi har kommit förbi challenge
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
        """Simulera mänskligt beteende"""
        try:
            # Slumpmässig fördröjning
            delay = random.uniform(self.human_delay_min, self.human_delay_max)
            time.sleep(delay)
            
            # Simulera scrollning
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
            time.sleep(random.uniform(0.5, 1.5))
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(random.uniform(0.5, 1.5))
            
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(random.uniform(0.5, 1.0))
            
        except Exception as e:
            logger.debug(f"Mänskligt beteende simulation fel: {e}")
    
    def _save_cookies(self, driver, url):
        """Spara cookies från Camoufox session"""
        try:
            domain = urlparse(url).netloc
            cookies = driver.get_cookies()
            
            # Spara alla cookies
            self.session_cookies[domain] = cookies
            
            # Hitta och cacha cf_clearance cookie
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
    """
    Förenklad Camoufox middleware som kan användas som fallback
    """
    
    def __init__(self, settings):
        self.enabled = settings.getbool('CAMOUFOX_ENABLED', False)
        self.stats = {}
        
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)
    
    def process_request(self, request, spider):
        if not self.enabled:
            return None
            
        # Lägg till Camoufox-specifika headers
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
        # Logga statistik
        status = response.status
        if status not in self.stats:
            self.stats[status] = 0
        self.stats[status] += 1
        
        if status == 403:
            logger.warning(f"🚫 403 Forbidden: {request.url}")
        elif status == 200:
            logger.info(f"✅ 200 OK: {request.url}")
            
        return response


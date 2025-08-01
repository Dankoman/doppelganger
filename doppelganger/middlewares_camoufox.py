"""
Camoufox Middleware för att kringgå Cloudflare bot-protection
FÖRBÄTTRAD VERSION med timeout-hantering och debug
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
        
        # FÖRBÄTTRADE timeout-inställningar
        self.page_load_timeout = self.settings.getint('CAMOUFOX_PAGE_LOAD_TIMEOUT', 15)
        self.cloudflare_wait_time = self.settings.getint('CAMOUFOX_CLOUDFLARE_WAIT', 10)
        self.webdriver_timeout = self.settings.getint('CAMOUFOX_WEBDRIVER_TIMEOUT', 10)
        self.connection_timeout = self.settings.getint('CAMOUFOX_CONNECTION_TIMEOUT', 5)
        
        self.human_delay_min = self.settings.getint('CAMOUFOX_HUMAN_DELAY_MIN', 1)
        self.human_delay_max = self.settings.getint('CAMOUFOX_HUMAN_DELAY_MAX', 3)
        
        self.cf_clearance_cache = {}
        self.session_cookies = {}
        self.failed_attempts = 0
        self.max_failed_attempts = 3
        
        if not self.camoufox_enabled:
            raise NotConfigured('Camoufox middleware är inaktiverat')
            
        logger.info(f"🦊 Camoufox Middleware aktiverat - {self.camoufox_host}:{self.camoufox_port}")
        logger.info(f"   WebDriver timeout: {self.webdriver_timeout}s")
        logger.info(f"   Connection timeout: {self.connection_timeout}s")
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)
    
    def process_request(self, request, spider):
        if not self.camoufox_enabled:
            return None
            
        if self.failed_attempts >= self.max_failed_attempts:
            logger.warning(f"🚫 Camoufox inaktiverat efter {self.failed_attempts} misslyckade försök")
            return None
            
        try:
            domain = urlparse(request.url).netloc
            if self._has_valid_clearance(domain):
                logger.debug(f"🍪 Använder cachad cf_clearance för {domain}")
                return self._make_request_with_cookies(request)
            
            logger.info(f"🦊 Använder Camoufox för {request.url}")
            response = self._fetch_with_camoufox(request, spider)
            
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
            
            response = session.get(request.url, headers=headers, timeout=self.connection_timeout)
            
            if response.status_code == 200:
                logger.info(f"✅ Framgångsrik request med cookies: {request.url}")
                return HtmlResponse(url=request.url, body=response.content, encoding='utf-8', request=request)
            else:
                logger.warning(f"⚠️ HTTP {response.status_code} med cookies: {request.url}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Cookie request fel: {e}")
            return None
    
    def _fetch_with_camoufox(self, request, spider):
        driver = None
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.firefox.options import Options
            from selenium.common.exceptions import TimeoutException, WebDriverException
            
            logger.info(f"🔗 Ansluter till Camoufox server {self.camoufox_host}:{self.camoufox_port}")
            
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            logger.info(f"⏱️ Skapar WebDriver med {self.webdriver_timeout}s timeout")
            
            driver = webdriver.Remote(
                command_executor=f'http://{self.camoufox_host}:{self.camoufox_port}/wd/hub',
                options=options
            )
            
            driver.set_page_load_timeout(self.page_load_timeout)
            driver.implicitly_wait(self.webdriver_timeout)
            
            logger.info(f"🦊 Navigerar till {request.url} (timeout: {self.page_load_timeout}s)")
            
            start_time = time.time()
            driver.get(request.url)
            load_time = time.time() - start_time
            logger.info(f"📄 Sida laddad på {load_time:.2f}s")
            
            try:
                WebDriverWait(driver, self.webdriver_timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                logger.info("✅ Body-element hittat")
            except TimeoutException:
                logger.warning(f"⚠️ Timeout vid väntan på body-element ({self.webdriver_timeout}s)")
            
            if self._handle_cloudflare_challenge(driver):
                logger.info("🛡️ Cloudflare challenge hanterat")
            
            self._simulate_human_behavior(driver)
            self._save_cookies(driver, request.url)
            
            page_source = driver.page_source
            
            if len(page_source) < 1000:
                logger.warning(f"⚠️ Kort sida ({len(page_source)} tecken), möjlig blockering")
            
            logger.info(f"✅ Camoufox framgångsrik: {request.url} ({len(page_source)} tecken)")
            
            return HtmlResponse(url=request.url, body=page_source.encode('utf-8'), encoding='utf-8', request=request)
            
        except ImportError:
            logger.error("❌ Selenium inte installerat. Kör: pip install selenium")
            return None
        except TimeoutException as e:
            logger.error(f"⏱️ Camoufox timeout: {e}")
            return None
        except WebDriverException as e:
            logger.error(f"🚫 WebDriver fel: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Camoufox oväntat fel: {e}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                    logger.debug("🔒 WebDriver stängd")
                except Exception as e:
                    logger.warning(f"⚠️ Fel vid stängning av WebDriver: {e}")
    
    def _handle_cloudflare_challenge(self, driver):
        try:
            time.sleep(1)
            cloudflare_indicators = [
                "Checking your browser before accessing",
                "DDoS protection by Cloudflare",
                "cf-browser-verification",
                "cf-challenge-running"
            ]
            
            page_source = driver.page_source.lower()
            is_cloudflare_challenge = any(indicator.lower() in page_source for indicator in cloudflare_indicators)
            
            if is_cloudflare_challenge:
                logger.info(f"🛡️ Cloudflare challenge detekterat, väntar max {self.cloudflare_wait_time}s...")
                
                for i in range(self.cloudflare_wait_time):
                    time.sleep(1)
                    page_source = driver.page_source.lower()
                    
                    if not any(indicator.lower() in page_source for indicator in cloudflare_indicators):
                        logger.info(f"✅ Cloudflare challenge löst efter {i+1} sekunder")
                        return True
                
                logger.warning(f"⚠️ Cloudflare challenge tog för lång tid ({self.cloudflare_wait_time}s)")
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
            time.sleep(0.2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(0.2)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.1)
            
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

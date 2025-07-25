import json
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrapy.http import HtmlResponse
from scrapy.exceptions import NotConfigured
import time
import random

logger = logging.getLogger(__name__)

class ChromeHeadlessMiddleware:
    """
    Middleware som använder headless Chrome för att kringgå bot-detektering
    Ansluter till befintliga chromedp/headless-shell Docker-instanser
    """
    
    def __init__(self, chrome_host='192.168.0.50', chrome_ports=[9222, 9223]):
        self.chrome_host = chrome_host
        self.chrome_ports = chrome_ports
        self.drivers = []
        self.current_driver_index = 0
        
        # Initiera Chrome-drivers
        self._init_drivers()
        
        logger.info(f"ChromeHeadlessMiddleware initialiserad med {len(self.drivers)} Chrome-instanser")
    
    @classmethod
    def from_crawler(cls, crawler):
        chrome_host = crawler.settings.get('CHROME_HOST', '192.168.0.50')
        chrome_ports = crawler.settings.getlist('CHROME_PORTS', [9222, 9223])
        chrome_enabled = crawler.settings.getbool('CHROME_ENABLED', False)
        
        if not chrome_enabled:
            raise NotConfigured('Chrome middleware disabled')
        
        if not chrome_ports:
            raise NotConfigured('Chrome ports not configured')
        
        return cls(chrome_host, chrome_ports)
    
    def _init_drivers(self):
        """Initiera Chrome WebDriver-instanser"""
        for port in self.chrome_ports:
            try:
                options = Options()
                options.add_experimental_option("debuggerAddress", f"{self.chrome_host}:{port}")
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-web-security')
                options.add_argument('--disable-features=VizDisplayCompositor')
                
                # Anti-detection inställningar
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
                
                driver = webdriver.Chrome(options=options)
                
                # Sätt realistiska egenskaper
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                    "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })
                
                self.drivers.append(driver)
                logger.info(f"Chrome-driver ansluten till {self.chrome_host}:{port}")
                
            except Exception as e:
                logger.error(f"Kunde inte ansluta till Chrome på port {port}: {e}")
    
    def get_driver(self):
        """Hämta nästa tillgängliga driver (round-robin)"""
        if not self.drivers:
            raise Exception("Inga Chrome-drivers tillgängliga")
        
        driver = self.drivers[self.current_driver_index]
        self.current_driver_index = (self.current_driver_index + 1) % len(self.drivers)
        return driver
    
    def process_request(self, request, spider):
        """Bearbeta request med Chrome headless"""
        
        # Endast för specifika domäner
        if 'mypornstarbook.net' not in request.url and 'mypromstarbook.net' not in request.url:
            return None
        
        try:
            driver = self.get_driver()
            
            # Slumpmässig fördröjning
            delay = random.uniform(3, 8)
            logger.debug(f"Chrome väntar {delay:.1f}s innan {request.url}")
            time.sleep(delay)
            
            logger.debug(f"Hämtar {request.url} med Chrome headless")
            
            # Navigera till sidan
            driver.get(request.url)
            
            # Vänta på att sidan laddas
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Extra väntetid för JavaScript och dynamiskt innehåll
            time.sleep(random.uniform(2, 4))
            
            # Simulera mänskligt beteende
            self._simulate_human_behavior(driver)
            
            # Hämta sidans innehåll
            body = driver.page_source.encode('utf-8')
            
            # Kontrollera om vi fick blockerat innehåll
            if b'403 Forbidden' in body or b'Access Denied' in body or len(body) < 1000:
                logger.warning(f"Möjlig blockering för {request.url} (längd: {len(body)})")
                return None
            
            # Skapa Scrapy response
            response = HtmlResponse(
                url=request.url,
                body=body,
                encoding='utf-8',
                request=request
            )
            
            logger.info(f"Chrome hämtade {request.url} framgångsrikt (längd: {len(body)} bytes)")
            
            return response
            
        except Exception as e:
            logger.error(f"Chrome headless fel för {request.url}: {e}")
            return None
    
    def _simulate_human_behavior(self, driver):
        """Simulera mänskligt beteende för att undvika detektering"""
        try:
            # Scrolla slumpmässigt
            scroll_height = driver.execute_script("return document.body.scrollHeight")
            if scroll_height > 1000:
                scroll_to = random.randint(100, min(scroll_height - 100, 2000))
                driver.execute_script(f"window.scrollTo(0, {scroll_to});")
                time.sleep(random.uniform(0.5, 1.5))
                
                # Scrolla tillbaka upp lite
                scroll_back = random.randint(0, scroll_to // 2)
                driver.execute_script(f"window.scrollTo(0, {scroll_back});")
                time.sleep(random.uniform(0.3, 1.0))
            
            # Slumpmässig musrörelse (simulerad)
            driver.execute_script("""
                var event = new MouseEvent('mousemove', {
                    'view': window,
                    'bubbles': true,
                    'cancelable': true,
                    'clientX': Math.random() * window.innerWidth,
                    'clientY': Math.random() * window.innerHeight
                });
                document.dispatchEvent(event);
            """)
            
            # Simulera fokus på sidan
            driver.execute_script("window.focus();")
            
        except Exception as e:
            logger.debug(f"Kunde inte simulera mänskligt beteende: {e}")
    
    def spider_closed(self, spider):
        """Stäng alla Chrome-drivers när spider stängs"""
        for driver in self.drivers:
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Fel vid stängning av Chrome-driver: {e}")
        
        self.drivers.clear()
        logger.info("Alla Chrome-drivers stängda")

class ChromeDownloaderMiddleware:
    """
    Förenklad Chrome middleware för Scrapy med en Chrome-instans
    """
    
    def __init__(self, chrome_host='192.168.0.50', chrome_port=9222):
        self.chrome_host = chrome_host
        self.chrome_port = chrome_port
        self.driver = None
        self._init_driver()
    
    @classmethod
    def from_crawler(cls, crawler):
        chrome_host = crawler.settings.get('CHROME_HOST', '192.168.0.50')
        chrome_port = crawler.settings.get('CHROME_PORT', 9222)
        chrome_enabled = crawler.settings.getbool('CHROME_ENABLED', False)
        
        if not chrome_enabled:
            raise NotConfigured('Chrome middleware disabled')
        
        return cls(chrome_host, chrome_port)
    
    def _init_driver(self):
        """Initiera Chrome WebDriver"""
        try:
            options = Options()
            options.add_experimental_option("debuggerAddress", f"{self.chrome_host}:{self.chrome_port}")
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            self.driver = webdriver.Chrome(options=options)
            
            # Anti-detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info(f"Chrome-driver ansluten till {self.chrome_host}:{self.chrome_port}")
            
        except Exception as e:
            logger.error(f"Kunde inte initiera Chrome-driver: {e}")
            raise NotConfigured(f"Chrome connection failed: {e}")
    
    def process_request(self, request, spider):
        """Bearbeta request med Chrome"""
        if not self.driver:
            return None
        
        if 'mypornstarbook.net' not in request.url and 'mypromstarbook.net' not in request.url:
            return None
        
        try:
            # Fördröjning
            delay = random.uniform(4, 9)
            time.sleep(delay)
            
            # Hämta sidan
            self.driver.get(request.url)
            
            # Vänta på laddning
            time.sleep(random.uniform(2, 5))
            
            # Hämta innehåll
            body = self.driver.page_source.encode('utf-8')
            
            # Kontrollera om vi fick rätt innehåll
            if b'403 Forbidden' in body or b'Access Denied' in body or len(body) < 1000:
                logger.warning(f"Möjlig blockering för {request.url}")
                return None
            
            response = HtmlResponse(
                url=request.url,
                body=body,
                encoding='utf-8',
                request=request
            )
            
            logger.info(f"Chrome hämtade {request.url} framgångsrikt")
            return response
            
        except Exception as e:
            logger.error(f"Chrome fel för {request.url}: {e}")
            return None
    
    def spider_closed(self, spider):
        """Stäng driver när spider stängs"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Chrome-driver stängd")
            except Exception as e:
                logger.error(f"Fel vid stängning av Chrome-driver: {e}")


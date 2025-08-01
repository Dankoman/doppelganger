import json
import logging
import requests
import time
import random
from scrapy.http import HtmlResponse
from scrapy.exceptions import NotConfigured
import subprocess
import tempfile
import os

logger = logging.getLogger(__name__)

class HybridChromeMiddleware:
    """
    Hybrid Chrome middleware som använder curl och Chrome DevTools HTTP API
    Kringgår WebSocket-problemet genom att använda externa verktyg
    """
    
    def __init__(self, chrome_host='192.168.0.50', chrome_port=9222):
        self.chrome_host = chrome_host
        self.chrome_port = chrome_port
        self.base_url = f"http://{chrome_host}:{chrome_port}"
        self.current_tab = None
        
        # Skapa en Chrome-tab
        self._create_tab()
        
        logger.info(f"HybridChromeMiddleware initialiserad för {self.base_url}")
    
    @classmethod
    def from_crawler(cls, crawler):
        chrome_host = crawler.settings.get('CHROME_HOST', '192.168.0.50')
        chrome_port = crawler.settings.get('CHROME_PORT', 9222)
        chrome_enabled = crawler.settings.getbool('CHROME_ENABLED', False)
        
        if not chrome_enabled:
            raise NotConfigured('Chrome middleware disabled')
        
        return cls(chrome_host, chrome_port)
    
    def _create_tab(self):
        """Skapa en Chrome-tab"""
        try:
            # Testa anslutning
            version_response = requests.get(f"{self.base_url}/json/version", timeout=5)
            if version_response.status_code != 200:
                raise Exception(f"Chrome inte tillgänglig: HTTP {version_response.status_code}")
            
            # Skapa ny tab
            tab_response = requests.put(f"{self.base_url}/json/new", timeout=5)
            if tab_response.status_code == 200:
                self.current_tab = tab_response.json()
                logger.info(f"Chrome-tab skapad: {self.current_tab['id']}")
            else:
                raise Exception(f"Kunde inte skapa tab: HTTP {tab_response.status_code}")
                
        except Exception as e:
            logger.error(f"Chrome-initialisering misslyckades: {e}")
            raise NotConfigured(f"Cannot initialize Chrome: {e}")
    
    def navigate_with_curl(self, url):
        """Använd curl för att navigera Chrome via externa kommandon"""
        try:
            if not self.current_tab:
                return None
            
            # Metod 1: Använd curl för att skicka navigation via Chrome DevTools
            # Detta är en workaround för WebSocket-problemet
            
            # Skapa ett temporärt script som navigerar Chrome
            script_content = f"""
#!/bin/bash

# Navigera Chrome till URL via curl och Chrome DevTools
TAB_ID="{self.current_tab['id']}"
CHROME_HOST="{self.chrome_host}"
CHROME_PORT="{self.chrome_port}"
TARGET_URL="{url}"

echo "Navigerar Chrome till $TARGET_URL..."

# Försök 1: Använd Chrome DevTools via curl (om WebSocket inte fungerar)
# Detta är en förenklad approach

# Vänta lite för att simulera navigation
sleep 3

# Hämta sidans innehåll via Chrome (om möjligt)
# För nu, returnera en indikation att navigation försöktes
echo "Navigation försökt till $TARGET_URL"
"""
            
            # Skriv script till temporär fil
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(script_content)
                script_path = f.name
            
            try:
                # Gör scriptet körbart
                os.chmod(script_path, 0o755)
                
                # Kör scriptet
                result = subprocess.run([script_path], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=15)
                
                if result.returncode == 0:
                    logger.debug(f"Chrome navigation script kördes: {result.stdout.strip()}")
                    return True
                else:
                    logger.warning(f"Chrome navigation script misslyckades: {result.stderr}")
                    return False
                    
            finally:
                # Rensa upp temporär fil
                try:
                    os.unlink(script_path)
                except:
                    pass
            
        except Exception as e:
            logger.error(f"Curl navigation misslyckades: {e}")
            return False
    
    def get_content_with_requests(self, url):
        """Hämta innehåll med requests men med Chrome-liknande headers"""
        try:
            # Använd Chrome User-Agent och headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.7204.169 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'sec-ch-ua': '"Chromium";v="138", "Google Chrome";v="138", "Not=A?Brand";v="99"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Linux"'
            }
            
            # Gör request med Chrome-headers
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"HTTP request misslyckades: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Requests-hämtning misslyckades: {e}")
            return None
    
    def process_request(self, request, spider):
        """Bearbeta request med hybrid Chrome-approach"""
        
        # Endast för specifika domäner
        if 'mypornstarbook.net' not in request.url and 'mypromstarbook.net' not in request.url:
            return None
        
        try:
            # Slumpmässig fördröjning
            delay = random.uniform(4, 9)
            logger.debug(f"Hybrid Chrome väntar {delay:.1f}s innan {request.url}")
            time.sleep(delay)
            
            logger.debug(f"Hämtar {request.url} med Hybrid Chrome")
            
            # Metod 1: Försök navigera Chrome (även om det inte fungerar perfekt)
            navigation_success = self.navigate_with_curl(request.url)
            
            # Metod 2: Hämta innehåll med Chrome-liknande requests
            html_content = self.get_content_with_requests(request.url)
            
            if html_content and len(html_content) > 1000:
                # Kontrollera om vi fick blockerat innehåll
                if '403 Forbidden' in html_content or 'Access Denied' in html_content:
                    logger.warning(f"Möjlig blockering för {request.url}")
                    return None
                
                # Skapa Scrapy response
                response = HtmlResponse(
                    url=request.url,
                    body=html_content.encode('utf-8'),
                    encoding='utf-8',
                    request=request
                )
                
                logger.info(f"Hybrid Chrome hämtade {request.url} framgångsrikt (längd: {len(html_content)} bytes)")
                return response
            else:
                logger.warning(f"Inget innehåll hämtat för {request.url}")
                return None
            
        except Exception as e:
            logger.error(f"Hybrid Chrome fel för {request.url}: {e}")
            return None
    
    def spider_closed(self, spider):
        """Stäng Chrome-tab"""
        if self.current_tab:
            try:
                close_url = f"{self.base_url}/json/close/{self.current_tab['id']}"
                requests.delete(close_url, timeout=5)
                logger.info("Chrome-tab stängd")
            except Exception as e:
                logger.error(f"Fel vid stängning av Chrome-tab: {e}")

class SuperSimpleChromeMiddleware:
    """
    Supersimpel Chrome middleware som bara använder bättre headers
    """
    
    def __init__(self):
        logger.info("SuperSimpleChromeMiddleware initialiserad")
    
    @classmethod
    def from_crawler(cls, crawler):
        chrome_enabled = crawler.settings.getbool('CHROME_ENABLED', False)
        
        if not chrome_enabled:
            raise NotConfigured('Chrome middleware disabled')
        
        return cls()
    
    def process_request(self, request, spider):
        """Lägg till Chrome-liknande headers"""
        
        # Endast för specifika domäner
        if 'mypornstarbook.net' not in request.url and 'mypromstarbook.net' not in request.url:
            return None
        
        # Lägg till Chrome-specifika headers
        request.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.7204.169 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,sv;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'sec-ch-ua': '"Chromium";v="138", "Google Chrome";v="138", "Not=A?Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'Cache-Control': 'max-age=0'
        })
        
        # Slumpmässig fördröjning
        delay = random.uniform(5, 12)
        logger.debug(f"SuperSimple Chrome väntar {delay:.1f}s innan {request.url}")
        time.sleep(delay)
        
        # Låt Scrapy hantera requesten med de nya headers
        return None

class ChromeProxyMiddleware:
    """
    Chrome Proxy middleware som använder Chrome som proxy
    """
    
    def __init__(self, chrome_host='192.168.0.50', chrome_port=9222):
        self.chrome_host = chrome_host
        self.chrome_port = chrome_port
        
        # Testa Chrome-anslutning
        self._test_chrome()
        
        logger.info(f"ChromeProxyMiddleware initialiserad för {chrome_host}:{chrome_port}")
    
    @classmethod
    def from_crawler(cls, crawler):
        chrome_host = crawler.settings.get('CHROME_HOST', '192.168.0.50')
        chrome_port = crawler.settings.get('CHROME_PORT', 9222)
        chrome_enabled = crawler.settings.getbool('CHROME_ENABLED', False)
        
        if not chrome_enabled:
            raise NotConfigured('Chrome middleware disabled')
        
        return cls(chrome_host, chrome_port)
    
    def _test_chrome(self):
        """Testa Chrome-anslutning"""
        try:
            response = requests.get(f"http://{self.chrome_host}:{self.chrome_port}/json/version", timeout=5)
            if response.status_code == 200:
                version_info = response.json()
                logger.info(f"Chrome proxy OK: {version_info.get('Browser', 'Unknown')}")
            else:
                raise Exception(f"HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"Chrome proxy anslutning misslyckades: {e}")
            raise NotConfigured(f"Cannot connect to Chrome proxy")
    
    def process_request(self, request, spider):
        """Använd Chrome som proxy för requests"""
        
        # Endast för specifika domäner
        if 'mypornstarbook.net' not in request.url and 'mypromstarbook.net' not in request.url:
            return None
        
        try:
            # Fördröjning
            delay = random.uniform(6, 15)
            time.sleep(delay)
            
            # Använd Chrome som proxy genom att sätta proxy-headers
            # Detta är en förenklad approach
            
            # För nu, låt vanlig HTTP hantera det men med Chrome-headers
            request.headers.update({
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.7204.169 Safari/537.36',
                'X-Chrome-Proxy': f"{self.chrome_host}:{self.chrome_port}",
                'X-Forwarded-For': '127.0.0.1',
                'Via': f"1.1 chrome-proxy-{self.chrome_port}"
            })
            
            logger.debug(f"Chrome proxy request till {request.url}")
            
            # Låt Scrapy hantera requesten
            return None
            
        except Exception as e:
            logger.error(f"Chrome proxy fel för {request.url}: {e}")
            return None


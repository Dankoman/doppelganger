import random
import logging

class ProxyRotatorMiddleware:
    """
    Middleware för att rotera proxies för varje request.
    Läser proxies från en fil och väljer slumpmässigt för varje request.
    """
    
    def __init__(self, proxy_list):
        self.proxy_list = proxy_list
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"ProxyRotatorMiddleware initialiserad med {len(proxy_list)} proxies")

    @classmethod
    def from_crawler(cls, crawler):
        """Skapa middleware från crawler settings"""
        path = crawler.settings.get('PROXY_LIST_PATH', '/home/ubuntu/doppelganger/proxy/proxies.txt')
        try:
            with open(path, 'r') as f:
                proxies = [line.strip() for line in f if line.strip()]
            if not proxies:
                raise ValueError("Inga proxies hittades i filen")
            return cls(proxies)
        except FileNotFoundError:
            raise FileNotFoundError(f"Proxy-fil hittades inte: {path}")
        except Exception as e:
            raise Exception(f"Fel vid läsning av proxy-fil {path}: {e}")

    def process_request(self, request, spider):
        """Välj en slumpmässig proxy för varje request"""
        if self.proxy_list:
            proxy = random.choice(self.proxy_list)
            request.meta['proxy'] = proxy
            spider.logger.debug(f"Använder proxy: {proxy} för URL: {request.url}")
        else:
            spider.logger.warning("Inga proxies tillgängliga")
        return None

    def process_response(self, request, response, spider):
        """Hantera response - logga eventuella problem"""
        if response.status in [403, 429, 503]:
            spider.logger.warning(f"Proxy blockerad (status {response.status}) för {request.url}")
        return response

    def process_exception(self, request, exception, spider):
        """Hantera exceptions relaterade till proxy"""
        spider.logger.error(f"Proxy-fel för {request.url}: {exception}")
        return None

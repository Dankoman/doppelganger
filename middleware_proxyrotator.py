import random

class ProxyRotatorMiddleware:
    def __init__(self, proxy_list):
        self.proxy_list = proxy_list

    @classmethod
    def from_crawler(cls, crawler):
        path = crawler.settings.get('PROXY_LIST_PATH')
        with open(path, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        return cls(proxies)

    def process_request(self, request, spider):
        proxy = random.choice(self.proxy_list)
        request.meta['proxy'] = proxy

# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import logging
import random
import time
from scrapy import signals
from scrapy.http import HtmlResponse
from scrapy.exceptions import NotConfigured
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware

logger = logging.getLogger(__name__)


class DoppelgangerSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn't have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class RotatingUserAgentMiddleware(UserAgentMiddleware):
    """Middleware för att rotera user agents för att undvika detektering"""
    
    def __init__(self, user_agent=''):
        self.user_agent = user_agent
        # Lista med realistiska user agents
        self.user_agent_list = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
        ]
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.get('USER_AGENT'))
    
    def process_request(self, request, spider):
        # Välj en slumpmässig user agent
        ua = random.choice(self.user_agent_list)
        request.headers['User-Agent'] = ua
        return None


class AntiBlockingMiddleware:
    """Middleware för att undvika blockeringar med förbättrade headers och beteende"""
    
    def __init__(self, settings):
        self.settings = settings
        self.delay_range = settings.get('ANTIBLOCK_DELAY_RANGE', (1, 3))
        
    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        if not settings.getbool('ANTIBLOCK_ENABLED', True):
            raise NotConfigured('Anti-blocking middleware is not enabled')
        
        middleware = cls(settings)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware
    
    def spider_opened(self, spider):
        logger.info(f'Anti-blocking middleware aktiverad för spider: {spider.name}')
    
    def process_request(self, request, spider):
        """Lägg till realistiska headers och beteende"""
        
        # Lägg till realistiska headers
        headers = {
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
            'Cache-Control': 'max-age=0',
        }
        
        # Lägg till referer för interna länkar
        if 'mypornstarbook.net' in request.url:
            headers['Referer'] = 'https://www.mypornstarbook.net/'
        
        # Uppdatera request headers
        for key, value in headers.items():
            request.headers[key] = value
        
        # Lägg till slumpmässig fördröjning
        delay = random.uniform(*self.delay_range)
        request.meta['download_delay'] = delay
        
        logger.debug(f"Bearbetar request till {request.url} med {delay:.1f}s fördröjning")
        
        return None
    
    def process_response(self, request, response, spider):
        """Hantera response och kontrollera för blockeringar"""
        
        if response.status == 403:
            logger.warning(f"403 Forbidden för {request.url} - kan vara blockerad")
        elif response.status == 429:
            logger.warning(f"429 Too Many Requests för {request.url} - för många requests")
        elif response.status >= 400:
            logger.warning(f"HTTP {response.status} för {request.url}")
        
        return response


class MyCustomDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


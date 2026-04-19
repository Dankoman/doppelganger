# -*- coding: utf-8 -*-

# Enhanced anti-blocking middleware for doppelganger scraper

import logging
import random
import time
import json
from scrapy import signals
from scrapy.http import HtmlResponse
from scrapy.exceptions import NotConfigured
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
from scrapy.downloadermiddlewares.retry import RetryMiddleware

logger = logging.getLogger(__name__)


class DoppelgangerSpiderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        return None

    def process_spider_output(self, response, result, spider):
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        pass

    def process_start_requests(self, start_requests, spider):
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class EnhancedUserAgentMiddleware(UserAgentMiddleware):
    """Förbättrad middleware för user agent rotation med mer realistiska agents"""
    
    def __init__(self, user_agent=''):
        self.user_agent = user_agent
        # Utökad lista med mycket realistiska och aktuella user agents
        self.user_agent_list = [
            # Chrome Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            
            # Chrome macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            
            # Firefox
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',
            
            # Safari
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
            
            # Edge
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            
            # Mobile (för variation)
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        ]
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.get('USER_AGENT'))
    
    def process_request(self, request, spider):
        ua = random.choice(self.user_agent_list)
        request.headers['User-Agent'] = ua
        logger.debug(f"Använder User-Agent: {ua[:50]}...")
        return None


class AdvancedAntiBlockingMiddleware:
    """Avancerad anti-blocking middleware med förbättrade tekniker"""
    
    def __init__(self, settings):
        self.settings = settings
        self.delay_range = settings.get('ANTIBLOCK_DELAY_RANGE', (2, 8))
        self.session_cookies = {}
        self.request_count = 0
        
    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        if not settings.getbool('ANTIBLOCK_ENABLED', True):
            raise NotConfigured('Advanced anti-blocking middleware is not enabled')
        
        middleware = cls(settings)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware
    
    def spider_opened(self, spider):
        logger.info(f'Avancerad anti-blocking middleware aktiverad för spider: {spider.name}')
    
    def process_request(self, request, spider):
        """Lägg till avancerade anti-blocking headers och beteende"""
        
        self.request_count += 1
        
        # Grundläggande realistiska headers
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,sv-SE;q=0.8,sv;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }
        
        # Lägg till referer för interna länkar
        if 'mypornstarbook.net' in request.url:
            if self.request_count == 1:
                # Första requesten - kom från Google
                headers['Referer'] = 'https://www.google.com/'
            else:
                # Efterföljande requests - kom från startsidan
                headers['Referer'] = 'https://www.mypornstarbook.net/'
        
        # Variera vissa headers baserat på request
        if self.request_count > 1:
            headers['Sec-Fetch-Site'] = 'same-origin'
            headers['Cache-Control'] = 'max-age=0'
        
        # Lägg till slumpmässiga headers ibland
        if random.random() < 0.3:
            headers['X-Requested-With'] = 'XMLHttpRequest'
        
        if random.random() < 0.2:
            headers['Purpose'] = 'prefetch'
        
        # Uppdatera request headers
        for key, value in headers.items():
            request.headers[key] = value
        
        # Lägg till längre slumpmässig fördröjning
        delay = random.uniform(*self.delay_range)
        request.meta['download_delay'] = delay
        
        # Lägg till timeout
        request.meta['download_timeout'] = 30
        
        logger.debug(f"Request #{self.request_count} till {request.url} med {delay:.1f}s fördröjning")
        
        return None
    
    def process_response(self, request, response, spider):
        """Hantera response och förbättra strategin baserat på resultat"""
        
        if response.status == 403:
            logger.warning(f"403 Forbidden för {request.url}")
            # Öka fördröjningen för nästa request
            self.delay_range = (max(5, self.delay_range[0]), max(15, self.delay_range[1]))
            logger.info(f"Ökar fördröjning till {self.delay_range}")
            
        elif response.status == 429:
            logger.warning(f"429 Too Many Requests för {request.url}")
            # Öka fördröjningen drastiskt
            self.delay_range = (10, 30)
            logger.info(f"Drastisk ökning av fördröjning till {self.delay_range}")
            
        elif response.status == 200:
            logger.info(f"Framgångsrik 200 för {request.url}")
            # Minska fördröjningen lite om vi får framgång
            if self.delay_range[0] > 2:
                self.delay_range = (max(2, self.delay_range[0] - 1), max(8, self.delay_range[1] - 2))
        
        elif response.status >= 400:
            logger.warning(f"HTTP {response.status} för {request.url}")
        
        return response


class EnhancedRetryMiddleware(RetryMiddleware):
    """Förbättrad retry middleware med exponential backoff"""
    
    def __init__(self, settings):
        super().__init__(settings)
        self.max_retry_times = settings.getint('RETRY_TIMES', 3)
        self.retry_http_codes = settings.getlist('RETRY_HTTP_CODES', [500, 502, 503, 504, 408, 429, 403])
        self.priority_adjust = settings.getint('RETRY_PRIORITY_ADJUST', -1)
    
    def retry(self, request, reason, spider):
        """Retry med exponential backoff"""
        retries = request.meta.get('retry_times', 0) + 1
        
        if retries <= self.max_retry_times:
            logger.info(f"Retry #{retries} för {request.url}: {reason}")
            
            # Exponential backoff
            delay = min(60, (2 ** retries) + random.uniform(1, 5))
            
            retryreq = request.copy()
            retryreq.meta['retry_times'] = retries
            retryreq.meta['download_delay'] = delay
            retryreq.dont_filter = True
            retryreq.priority = request.priority + self.priority_adjust
            
            logger.info(f"Väntar {delay:.1f}s innan retry")
            return retryreq
        else:
            logger.error(f"Gav upp efter {retries} försök för {request.url}: {reason}")
            return None


class MyCustomDownloaderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        return None

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


import scrapy
from doppelganger.items import DoppelgangerItem


class MpbFromUrlsSpider(scrapy.Spider):
    name = 'mpb_from_urls'
    allowed_domains = ['mypornstarbook.net']

    def __init__(self, urls_file=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.urls_file = urls_file or '/app/profile_urls.txt'
        self.proxy_failures = {}  # Håll koll på proxy-fel

    def start_requests(self):
        """Läs URL:er från fil och skapa requests"""
        try:
            with open(self.urls_file, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            self.logger.info(f"Läste {len(urls)} URL:er från {self.urls_file}")
            for url in urls:
                yield scrapy.Request(
                    url=url, 
                    callback=self.parse, 
                    meta={
                        'dont_cache': True,
                        'download_timeout': 30,  # Längre timeout för proxy
                        'max_retry_times': 5,    # Fler försök med proxy
                    },
                    dont_filter=True  # Tillåt återförsök även för samma URL
                )
        except FileNotFoundError:
            self.logger.error(f"Kunde inte hitta URL-fil: {self.urls_file}")

    def parse(self, response):
        # Logga proxy-information om tillgänglig
        proxy_used = response.meta.get('proxy', 'Ingen proxy')
        self.logger.info(f"Svar från {response.url} via proxy: {proxy_used}")
        
        if response.status != 200:
            self.logger.warning(f"Fick status {response.status} för {response.url} via proxy {proxy_used}")
            # Räkna proxy-fel
            if proxy_used != 'Ingen proxy':
                self.proxy_failures[proxy_used] = self.proxy_failures.get(proxy_used, 0) + 1
                if self.proxy_failures[proxy_used] > 3:
                    self.logger.warning(f"Proxy {proxy_used} har misslyckats {self.proxy_failures[proxy_used]} gånger")
            return

        # Försök hitta ett namn
        name_from_url = response.url.split('/')[-2].replace('_', ' ').title()
        name = None
        for selector in ['h1::text', '.profile-name::text', '.pornstar-name::text', 'title::text']:
            candidates = response.css(selector).getall()
            if candidates:
                name = candidates[0].strip()
                break
        name = name or name_from_url

        # Rensa bort suffix
        for suffix in [' - MyPornstarBook.net', ' Porn Pics', ' Pictures']:
            if name.endswith(suffix):
                name = name.replace(suffix, '').strip()

        # Extrahera alla relevanta bilder
        image_urls = []
        selectors = [
            'img[src*="pornstars"]::attr(src)',
            'img[src*="photos"]::attr(src)',
            'img[src*="gallery"]::attr(src)',
            '.gallery img::attr(src)',
            'img::attr(src)'
        ]
        for selector in selectors:
            for img in response.css(selector).getall():
                if any(ext in img.lower() for ext in ['.jpg', '.jpeg', '.png']):
                    if img.startswith('//'):
                        img = 'https:' + img
                    elif img.startswith('/'):
                        img = 'https://www.mypornstarbook.net' + img
                    if not img.startswith('http'):
                        continue
                    if any(skip in img.lower() for skip in ['icon', 'logo', 'banner', 'ad']):
                        continue
                    image_urls.append(img)

        image_urls = list(dict.fromkeys(image_urls))  # Ta bort dubletter

        item = DoppelgangerItem()
        item['name'] = name
        item['image_urls'] = image_urls
        item['source_url'] = response.url

        self.logger.info(f"Scrapad profil: {name} med {len(image_urls)} bilder via proxy: {proxy_used}")
        yield item

    def closed(self, reason):
        """Logga proxy-statistik när spider stängs"""
        self.logger.info(f"Spider stängd: {reason}")
        if self.proxy_failures:
            self.logger.info("Proxy-fel statistik:")
            for proxy, failures in self.proxy_failures.items():
                self.logger.info(f"  {proxy}: {failures} fel")
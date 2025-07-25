import scrapy
import os
from doppelganger.items import DoppelgangerItem


class MpbFromUrlsSpider(scrapy.Spider):
    name = 'mpb_from_urls'
    allowed_domains = ['mypornstarbook.net']
    
    def __init__(self, urls_file=None, *args, **kwargs):
        super(MpbFromUrlsSpider, self).__init__(*args, **kwargs)
        self.urls_file = urls_file or '/app/profile_urls.txt'
        
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
                    meta={'dont_cache': True}
                )
                
        except FileNotFoundError:
            self.logger.error(f"Kunde inte hitta URL-fil: {self.urls_file}")
            return
    
    def parse(self, response):
        """Parse pornstar profile page"""
        if response.status != 200:
            self.logger.warning(f"Fick status {response.status} för {response.url}")
            return
            
        # Extrahera namn från URL eller sida
        name_from_url = response.url.split('/')[-2].replace('_', ' ').title()
        
        # Försök hitta namn på sidan
        name_selectors = [
            'h1::text',
            '.profile-name::text', 
            '.pornstar-name::text',
            'title::text'
        ]
        
        name = None
        for selector in name_selectors:
            name_candidates = response.css(selector).getall()
            if name_candidates:
                name = name_candidates[0].strip()
                if name and name != 'MyPornstarBook.net':
                    break
        
        if not name or name == 'MyPornstarBook.net':
            name = name_from_url
            
        # Extrahera bilder
        image_urls = []
        
        # Olika selektorer för bilder
        image_selectors = [
            'img[src*="pornstars"]::attr(src)',
            'img[src*="photos"]::attr(src)', 
            'img[src*="gallery"]::attr(src)',
            '.profile-image img::attr(src)',
            '.gallery img::attr(src)',
            'img::attr(src)'
        ]
        
        for selector in image_selectors:
            imgs = response.css(selector).getall()
            for img in imgs:
                if img and any(ext in img.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                    if img.startswith('//'):
                        img = 'https:' + img
                    elif img.startswith('/'):
                        img = 'https://www.mypornstarbook.net' + img
                    elif not img.startswith('http'):
                        continue
                    
                    # Filtrera bort små ikoner och ads
                    if any(skip in img.lower() for skip in ['icon', 'logo', 'banner', 'ad']):
                        continue
                        
                    if img not in image_urls:
                        image_urls.append(img)
        
        # Extrahera metadata
        bio_selectors = [
            '.bio::text',
            '.description::text',
            '.profile-info::text',
            'p::text'
        ]
        
        bio = ""
        for selector in bio_selectors:
            bio_parts = response.css(selector).getall()
            if bio_parts:
                bio = ' '.join([part.strip() for part in bio_parts if part.strip()])
                if len(bio) > 50:  # Endast om vi får någon substantiell text
                    break
        
        # Skapa item
        item = DoppelgangerItem()
        item['name'] = name
        item['image_urls'] = image_urls[:10]  # Begränsa till 10 bilder per profil
        item['bio'] = bio
        item['source_url'] = response.url
        
        self.logger.info(f"Scrapad profil: {name} med {len(image_urls)} bilder")
        
        yield item


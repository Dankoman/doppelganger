# -*- coding: utf-8 -*-
from string import ascii_uppercase

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from doppelganger.items import Actress

class BestpornstardbSpider(CrawlSpider):
    name = "bestpornstardb"
    allowed_domains = ["bestpornstardb.com"]

    # 1) Använd HTTPS utan "www", och indexera med VERSALA bokstäver
    start_urls = [
        f"https://bestpornstardb.com/stars/{letter}"
        for letter in ascii_uppercase
    ]

    rules = (
        # 2) Följ just index-sidorna /stars/A, /stars/B osv.
        Rule(
            LinkExtractor(allow=r"/stars/[A-Z]$"),
            follow=True
        ),
        # 3) Extrahera sedan alla profilsidor /stars/<slug>
        Rule(
            LinkExtractor(allow=r"/stars/[A-Za-z0-9\-_]+$"),
            callback="parse_actress_response"
        ),
    )

    def parse_actress_response(self, response):
        """Bygger ett Actress-item per profilsida."""
        # Namnet i URL: https://bestpornstardb.com/stars/jane-doe →
        # 'jane-doe'
        actress_name = response.url.rstrip("/").rsplit("/", 1)[-1]

        item = Actress()
        item["name"] = actress_name

        # Alla thumb-bilder ligger i <img class="t">
        raws = response.xpath('//img[@class="t"]/@src').getall()
        # Gör relativ → absolut
        item["image_urls"] = [response.urljoin(u) for u in raws]

        yield item

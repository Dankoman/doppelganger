# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from doppelganger.items import Actress

class ThumbnailSeriesSpider(CrawlSpider):
    name = "thumbnailseries"
    allowed_domains = ["thumbnailseries.com"]
    start_urls = ["https://www.thumbnailseries.com/pornstars/"]

    rules = (
        # Följ länkar till varje profilsida under /pornstars/<namn>/
        Rule(
            LinkExtractor(allow=r"/pornstars/[a-z0-9\-]+/?$"),
            callback="parse_profile",
            follow=True
        ),
    )

    def parse_profile(self, response):
        # 1) Namnet på stjärnan
        name = response.css('h1.entry-title::text').get(default='').strip()

        # 2) Alla img-taggar i huvudtexten (kan justeras om site-strukturen ändras)
        image_urls = response.css('.entry-content img::attr(src)').getall()

        # 3) Skapa och yield:a item som ImagesPipeline kan hantera
        item = Actress()
        item['name'] = name
        item['image_urls'] = image_urls
        item['profile_url'] = response.url
        yield item

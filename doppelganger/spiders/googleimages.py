# doppelganger/spiders/googleimages.py
# -*- coding: utf-8 -*-
import os
import urllib.parse
import scrapy
from doppelganger.items import Actress

class GoogleImagesSpider(scrapy.Spider):
    name = "googleimages"
    allowed_domains = ["www.googleapis.com", "googleusercontent.com", "reddit.it", "m.media-amazon.com", "upload.wikimedia.org"]
    name = "googleimages"
    allowed_domains = ["www.googleapis.com"]
    custom_settings = {
        'EXTENSIONS': {'scrapy.extensions.closespider.CloseSpider': 500},
        'CLOSESPIDER_ITEMCOUNT': 100,
        'JOBDIR': 'crawls/googleimages-1',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key   = os.getenv("GOOGLE_API_KEY")
        self.cx        = os.getenv("GOOGLE_CX")
        self.source_dir = "/home/marqs/Bilder/pr0n/full"

    def start_requests(self):
        base_url = "https://www.googleapis.com/customsearch/v1"
        for dirname in os.listdir(self.source_dir):
            dirpath = os.path.join(self.source_dir, dirname)
            if not os.path.isdir(dirpath):
                continue
            query = dirname.replace("_", " ")
            # Bygg URL med GET-parametrar enligt API-spec
            params = {
                "key":        self.api_key,
                "cx":         self.cx,
                "q":          query,
                "searchType": "image",
                "num":        "10",
            }
            url = base_url + "?" + urllib.parse.urlencode(params)
            yield scrapy.Request(
                url,
                callback=self.parse,
                meta={"dir_name": dirname},
                dont_filter=True
            )

    def parse(self, response):
        """
        Parsar JSON-svaret från Google Custom Search.
        """
        data = response.json()
        item = Actress()
        item["name"] = response.meta["dir_name"]
        # Extrahera bild-URL:er från "items" → "link"
        urls = [hit.get("link") for hit in data.get("items", []) if hit.get("link")]
        item["image_urls"] = urls
        yield item

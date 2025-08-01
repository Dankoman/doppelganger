# doppelganger/spiders/pornpics.py
import re
from typing import Iterable, Optional
import scrapy


class PornpicsItem(scrapy.Item):
    """Item med bild-URL och modellnamn."""
    name = scrapy.Field()
    star = scrapy.Field()
    image_urls = scrapy.Field()
    images = scrapy.Field()


class PornpicsSpider(scrapy.Spider):
    """Scrapy-spider för att crawla modeller och bilder på pornpics.com."""

    name = "pornpics"
    allowed_domains = ["pornpics.com"]
    start_urls = [
        f"https://www.pornpics.com/pornstars/list/{chr(letter)}/"
        for letter in range(ord("a"), ord("z") + 1)
    ]

    custom_settings = {
        "ITEM_PIPELINES": {
            "doppelganger.pipelines.PerformerImagePipeline": 1,
        },
        "IMAGES_STORE": "/root/doppelganger/images-ppic",
        "LOG_LEVEL": "INFO",
    }

    def parse(self, response: scrapy.http.Response) -> Iterable[scrapy.Request]:
        """Parsa list-sida och följ profiler med fler än 3 bilder."""
        for link in response.css("a"):
            href = link.attrib.get("href")
            if not href or not href.startswith("/pornstars/"):
                continue

            # Extrahera text och räkna bilder
            text = "".join(
                part.strip() for part in link.css("::text").getall() if part.strip()
            )
            match = re.search(r"\(([\d,]+)\)", text)
            if not match:
                continue
            try:
                count = int(match.group(1).replace(",", ""))
            except ValueError:
                continue
            if count <= 3:
                continue

            star_name = text[: text.rfind("(")].strip()
            yield scrapy.Request(
                response.urljoin(href),
                callback=self.parse_profile,
                meta={"name": star_name},
            )

    def parse_profile(self, response: scrapy.http.Response) -> Iterable[PornpicsItem]:
        """Extrahera upp till 15 bilder från en profil-sida."""
        star_name = response.meta.get("name", "")
        count = 0
        for anchor in response.css("a.rel-link"):
            href = anchor.attrib.get("href")
            if not href or "/channels/" in href:
                continue

            img_url = (
                anchor.css("img::attr(data-src)").get()
                or anchor.css("img::attr(src)").get()
            )
            if not img_url:
                continue

            item = PornpicsItem()
            item["name"] = star_name
            item["star"] = star_name
            item["image_urls"] = [img_url]
            yield item

            count += 1
            if count >= 15:
                break

"""
Spider för att hämta bilder från PornPics.
"""

import re
from typing import Iterable, Optional

import scrapy
from scrapy.pipelines.images import ImagesPipeline


class PornpicsItem(scrapy.Item):
    """Item med bild-URL och namn."""
    name = scrapy.Field()
    star = scrapy.Field()
    image_urls = scrapy.Field()
    images = scrapy.Field()


class PerformerImagePipeline(ImagesPipeline):
    """Döp varje bild med FörnamnEfternamn-XXX.jpg i undermapp med samma namn."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._counters: dict[str, int] = {}

    def file_path(
        self,
        request: scrapy.http.Request,
        response: Optional[scrapy.http.Response] = None,
        info: Optional[object] = None,
        *,
        item: Optional[scrapy.Item] = None,
    ) -> str:
        star_name = "unknown"
        if item:
            if "name" in item and item["name"]:
                star_name = str(item["name"]).strip().replace(" ", "").replace("/", "-")
            elif "star" in item and item["star"]:
                star_name = str(item["star"]).strip().replace(" ", "").replace("/", "-")

        index = self._counters.get(star_name, 0) + 1
        self._counters[star_name] = index

        filename = f"{star_name}-{index:03d}.jpg"
        return f"{star_name}/{filename}"


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
            "doppelganger.spiders.pornpics.PerformerImagePipeline": 1,
        },
        "IMAGES_STORE": "/root/doppelganger/images-ppic",
        "LOG_LEVEL": "INFO",
    }

    def parse(self, response: scrapy.http.Response) -> Iterable[scrapy.Request]:
        """Parsa en listsida och hämta profiler med fler än tre bilder."""
        for link in response.css("a"):
            href: Optional[str] = link.attrib.get("href")
            if not href or not href.startswith("/pornstars/"):
                continue

            text_parts = link.css("::text").getall()
            full_text = "".join(part.strip() for part in text_parts if part.strip())
            if not full_text:
                continue

            match = re.search(r"\(([^)]+)\)", full_text)
            if not match:
                continue
            try:
                count = int(match.group(1).replace(",", ""))
            except ValueError:
                continue

            if count <= 3:
                continue

            profile_url = response.urljoin(href)
            star_name = full_text[: full_text.rfind("(")].strip()
            yield scrapy.Request(
                profile_url,
                callback=self.parse_profile,
                meta={"name": star_name},
            )

    def parse_profile(self, response: scrapy.http.Response) -> Iterable[PornpicsItem]:
        """Extrahera bilder från en profilsida."""
        star_name: str = response.meta.get("name", "")
        image_count = 0
        for anchor in response.css("a.rel-link"):
            href: Optional[str] = anchor.attrib.get("href")
            if not href or "/channels/" in href:
                continue

            img_url = anchor.css("img::attr(data-src)").get() or anchor.css(
                "img::attr(src)"
            ).get()
            if not img_url:
                continue

            item = PornpicsItem()
            item["name"] = star_name
            item["star"] = star_name
            item["image_urls"] = [img_url]
            yield item

            image_count += 1
            if image_count >= 15:
                break

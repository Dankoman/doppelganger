import re
from typing import Iterable, Optional

import scrapy
from itemadapter import ItemAdapter


class PornpicsItem(scrapy.Item):
    """Item med bild-URL och namn."""
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
        """Parsa en listsida och hämta profiler med fler än tre bilder."""
        for link in response.css("a"): 
            href: Optional[str] = link.attrib.get("href")
            if not href or not href.startswith("/pornstars/"):
                continue

            text = "".join(part.strip() for part in link.css("::text").getall() if part.strip())
            if not text:
                continue

            m = re.search(r"\(([^)]+)\)", text)
            if not m:
                continue
            try:
                count = int(m.group(1).replace(",", ""))
            except ValueError:
                continue

            if count <= 3:
                continue

            profile_url = response.urljoin(href)
            star_name = text[: text.rfind("(")].strip()
            yield scrapy.Request(
                profile_url,
                callback=self.parse_profile,
                meta={"name": star_name},
            )

    def parse_profile(self, response: scrapy.http.Response) -> Iterable[PornpicsItem]:
        """Extrahera bilder från en profilsida, utan att följa galleri-länkar."""
        star_name: str = response.meta.get("name", "")
        image_count = 0
        for anchor in response.css("a.rel-link"):  # välj bilderelaterade länkar
            # filtrera bort kanal- och galleri-länkar
            href: Optional[str] = anchor.attrib.get("href")
            if not href or "/channels/" in href:
                continue
            if anchor.css("span.g-count"):  # galleri-länk med g-count
                continue

            # extrahera bild-URL
            img_url = anchor.css("img::attr(data-src)").get() or anchor.css("img::attr(src)").get()
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

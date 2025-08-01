"""
Spider för att hämta bilder från PornPics.

Den här Scrapy‑spidern besöker listorna över porrstjärnor på
`https://www.pornpics.com/pornstars/list/a/` till
`https://www.pornpics.com/pornstars/list/z/`. På varje listsida letar den upp
länkar till individuella profiler (URL:er som börjar med `/pornstars/`) och
kontrollerar antalet bilder som anges inom parentes efter namnet. Endast
profiler med fler än tre bilder kommer att crawlas. För varje profil samlar
spidern upp till 15 bildlänkar från element av typen:

    <a class="rel-link" href="…" ...><img data-src="…" /></a>

Länkar vars `href` innehåller `/channels/` filtreras bort. Varje bild URL
skickas till Scrapy’s inbyggda ImagesPipeline via fältet `image_urls` för
nedladdning. För att spidern ska ladda ned bilderna behöver `IMAGES_STORE`
ange en mapp i projektets inställningar eller i `custom_settings` nedan.

Observera att du behöver lägga till spidern i ditt Scrapy‑projekt och
se till att `scrapy.pipelines.images.ImagesPipeline` är aktiverad.
"""

import re
from typing import Iterable, Optional

import scrapy
from scrapy.pipelines.images import ImagesPipeline  # för anpassad namngivning

class PornpicsItem(scrapy.Item):
    """
    Definierar de fält som används av spidern.
    `image_urls` kommer att läsas av Scrapy’s ImagesPipeline och `images`
    innehåller resultatmetadata efter nedladdning. För att vår
    ``PerformerImagePipeline`` ska kunna sätta rätt filnamn behöver
    objektet exponera fältet ``name`` som innehåller modellens namn.
    """

    name = scrapy.Field()
    star = scrapy.Field()
    image_urls = scrapy.Field()
    images = scrapy.Field()

class PornPicsImagesPipeline(ImagesPipeline):
    """
    Anpassad ImagesPipeline som döper filer efter modellen.

    Den här pipelinen används inte längre av spidern men behålls här för
    framtida referens. Filnamn genereras från ``item['name']`` eller ``item['star']``
    om tillgängligt. Om du vill använda denna klass måste du aktivera den i
    ``ITEM_PIPELINES`` i projektinställningarna.
    """

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
                star_name = str(item["name"]).replace(" ", "").replace("/", "-")
            elif "star" in item and item["star"]:
                star_name = str(item["star"]).replace(" ", "").replace("/", "-")
        index = self._counters.get(star_name, 0) + 1
        self._counters[star_name] = index
        return f"{star_name}-{index:03d}.jpg"

class PornpicsSpider(scrapy.Spider):
    """Spindel som crawlar PornPics listor och profiler."""

    name = "pornpics"
    allowed_domains = ["pornpics.com"]
    start_urls = [
        f"https://www.pornpics.com/pornstars/list/{chr(letter)}/"
        for letter in range(ord("a"), ord("z") + 1)
    ]

    # Använd projektets PerformerImagePipeline och spara bilder i images-ppic.
    custom_settings = {
        "ITEM_PIPELINES": {
            "doppelganger.pipelines.PerformerImagePipeline": 1,
        },
        "IMAGES_STORE": "/root/doppelganger/images-ppic",
        "LOG_LEVEL": "INFO",
    }

    def parse(self, response: scrapy.http.Response) -> Iterable[scrapy.Request]:
        """Parsa en listsida och generera requests till varje relevant profil."""
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
        """Extrahera bildlänkar från en profilsida."""
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

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


class PornpicsItem(scrapy.Item):
    """Definierar de fält som används av spidern.

    `image_urls` kommer att läsas av Scrapy’s ImagesPipeline och `images`
    innehåller resultatmetadata efter nedladdning. Fältet `star` används för
    att spara namnet på modellen.
    """

    star = scrapy.Field()
    image_urls = scrapy.Field()
    images = scrapy.Field()


class PornpicsSpider(scrapy.Spider):
    """Spindel som crawlar PornPics listor och profiler.

    Start‑URL:er genereras dynamiskt för bokstäverna a–z. För varje namn på en
    listsida filtreras bara de profiler som har fler än tre bilder (enligt
    siffran inom parentes). På profilsidan samlas upp till 15 bild‑URL:er från
    element med CSS‑klassen `rel-link`, så länge länken inte pekar på
    kanaler. Resultaten levereras som ``PornpicsItem`` så att en
    ImagesPipeline kan ta hand om nedladdningen.
    """

    name = "pornpics"
    allowed_domains = ["pornpics.com"]
    # Skapa start‑URL:er för varje bokstav a–z
    start_urls = [
        f"https://www.pornpics.com/pornstars/list/{chr(letter)}/"
        for letter in range(ord("a"), ord("z") + 1)
    ]

    # Anpassade inställningar: aktivera ImagesPipeline och definiera var
    # bilderna ska sparas. Justera IMAGES_STORE efter behov.
    custom_settings = {
        "ITEM_PIPELINES": {"scrapy.pipelines.images.ImagesPipeline": 1},
        # Standardmapp för nedladdade bilder
        "IMAGES_STORE": "downloaded_images/pornpics",
        # Minska loggningsnivån för att inte spamma utdata
        "LOG_LEVEL": "INFO",
    }

    def parse(self, response: scrapy.http.Response) -> Iterable[scrapy.Request]:
        """Parsa en listsida och generera requests till varje relevant profil.

        På listsidan finns namn på porrstjärnor med antal bilder inom
        parentes. Den här metoden extraherar varje länk, läser siffran i
        parentesen och följer bara länkar där antalet är större än tre. För
        att undvika att följa andra länkar (t.ex. navigation eller reklam)
        filtreras bara länkar vars ``href`` börjar med ``/pornstars/``.
        """
        # Hämta alla ankar‑element på sidan
        for link in response.css("a"):
            href: Optional[str] = link.attrib.get("href")
            if not href:
                continue
            # Vi är bara intresserade av länkar som leder till en pornstars‑profil
            # De börjar med '/pornstars/' enligt sidans struktur.
            if not href.startswith("/pornstars/"):
                continue

            # Extrahera hela texten i länken, inklusive eventuella barnnoder.
            text_parts = link.css("::text").getall()
            full_text = "".join(part.strip() for part in text_parts if part.strip())
            if not full_text:
                continue

            # Matcha antalet bilder inom parentes, t.ex. "Aaliyah Love (1,337)"
            match = re.search(r"\(([^)]+)\)", full_text)
            if not match:
                continue
            # Ta bort eventuella kommatecken i siffran och konvertera till int
            try:
                count = int(match.group(1).replace(",", ""))
            except ValueError:
                continue

            # Hoppa över profiler med tre eller färre bilder
            if count <= 3:
                continue

            # Följ länken till profilsidan. Använd response.urljoin för att bygga
            # absolut URL.
            profile_url = response.urljoin(href)
            # Star‑namnet är texten före parentesen
            star_name = full_text[: full_text.rfind("(")].strip()
            yield scrapy.Request(
                profile_url,
                callback=self.parse_profile,
                meta={"star": star_name},
            )

    def parse_profile(self, response: scrapy.http.Response) -> Iterable[PornpicsItem]:
        """Extrahera bildlänkar från en profilsida.

        Den här metoden letar efter alla ``<a>`` med CSS‑klassen ``rel-link``.
        För varje länk ignoreras de som leder till kanaler (``/channels/`` i
        ``href``). Därefter extraheras bildlänken från ``data-src`` eller
        ``src``-attributet i ``<img>``. Högst 15 bilder per profil kommer att
        genereras som ``PornpicsItem``.
        """
        star_name: str = response.meta.get("star", "")
        image_count = 0
        # Loopa igenom alla relevanta ankar‑element
        for anchor in response.css("a.rel-link"):
            href: Optional[str] = anchor.attrib.get("href")
            if not href:
                continue
            # Hoppa över länkar till kanaler
            if "/channels/" in href:
                continue

            # Hämta bildens URL, helst från data-src (lazy loading)
            img_url = anchor.css("img::attr(data-src)").get() or anchor.css(
                "img::attr(src)"
            ).get()
            if not img_url:
                continue

            item = PornpicsItem()
            item["star"] = star_name
            item["image_urls"] = [img_url]
            yield item

            image_count += 1
            if image_count >= 15:
                break
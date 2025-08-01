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
    """Definierar de fält som används av spidern.

    `image_urls` kommer att läsas av Scrapy’s ImagesPipeline och `images`
    innehåller resultatmetadata efter nedladdning. För att vår
    ``PerformerImagePipeline`` ska kunna sätta rätt filnamn behöver
    objektet exponera fältet ``name`` som innehåller modellens namn. För den
    som vill spara namnet separat finns även fältet ``star`` kvar.
    """

    # Pipelines kommer att läsa detta fält för att generera filnamn
    name = scrapy.Field()
    # Behåll även star som alias, men det används inte av pipelinen
    star = scrapy.Field()
    # URL:er till bilder som ska laddas ned av ImagesPipeline
    image_urls = scrapy.Field()
    # Metadata om nedladdade bilder
    images = scrapy.Field()


class PornPicsImagesPipeline(ImagesPipeline):
    """Anpassad ImagesPipeline som döper filer efter modellen.

    Den här pipelinen används inte längre av spidern men behålls här för
    framtida referens. Filnamn genereras från ``item['star']`` om
    tillgängligt, annars faller den tillbaka på ``unknown``. Om du vill
    använda denna klass måste du aktivera den i ``ITEM_PIPELINES`` i
    projektinställningarna.
    """

    def __init__(self, *args, **kwargs):  # type: ignore[override]
        super().__init__(*args, **kwargs)
        self._counters: dict[str, int] = {}

    def file_path(
        self,
        request: scrapy.http.Request,
        response: Optional[scrapy.http.Response] = None,
        info: Optional[scrapy.pipelines.media.MediaPipelineStats] = None,
        *,
        item: Optional[scrapy.Item] = None,
    ) -> str:
        star_name = "unknown"
        if item:
            # Prio: använd name om tillgängligt, annars star
            if "name" in item:
                star_name = str(item["name"]).replace(" ", "").replace("/", "-")
            elif "star" in item:
                star_name = str(item["star"]).replace(" ", "").replace("/", "-")
        index = self._counters.get(star_name, 0) + 1
        self._counters[star_name] = index
        return f"{star_name}-{index:03d}.jpg"


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

    # Anpassade inställningar: använd projektets PerformerImagePipeline för att
    # generera filnamn (förnamnEfternamn-001.jpg osv.) och spara bilderna i
    # katalogen från doppelganger/settings.py. Justera IMAGES_STORE vid behov.
    custom_settings = {
        "ITEM_PIPELINES": {
            "doppelganger.pipelines.PerformerImagePipeline": 1,
        },
        # Sökvägen där bilder lagras. Denna bör matcha IMAGES_STORE i dina
        # projektinställningar för konsekvens. Standardvärdet är
        # "/root/doppelganger/images-ppic" enligt settings.py.
        "IMAGES_STORE": "/root/doppelganger/images-ppic",
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
            # Skicka med modellens namn i meta under nyckeln "name".
            # Detta används i parse_profile för att sätta item['name'] och
            # av pipelinen för att generera filnamn.
            yield scrapy.Request(
                profile_url,
                callback=self.parse_profile,
                meta={"name": star_name},
            )

    def parse_profile(self, response: scrapy.http.Response) -> Iterable[PornpicsItem]:
        """Extrahera bildlänkar från en profilsida.

        Den här metoden letar efter alla ``<a>`` med CSS‑klassen ``rel-link``.
        För varje länk ignoreras de som leder till kanaler (``/channels/`` i
        ``href``). Därefter extraheras bildlänken från ``data-src`` eller
        ``src``-attributet i ``<img>``. Högst 15 bilder per profil kommer att
        genereras som ``PornpicsItem``.
        """
        # Hämta modellens namn från meta (satt i parse()). Använd "name" som nyckel.
        star_name: str = response.meta.get("name", "")
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
            # Sätt både name och star för att vara kompatibel med PerformerImagePipeline
            item["name"] = star_name
            item["star"] = star_name
            item["image_urls"] = [img_url]
            yield item

            image_count += 1
            if image_count >= 15:
                break
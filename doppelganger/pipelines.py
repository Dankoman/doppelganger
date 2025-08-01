import os
import re
import unicodedata
from urllib.parse import urlparse

import scrapy
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline


def clean_name(name: str) -> str:
    # Normalisera Unicode och ta bort ogiltiga filsystemtecken men behåll mellanslag
    name = unicodedata.normalize("NFKD", name)
    name = re.sub(r"[^\w\s-]", "", name, flags=re.UNICODE)
    return re.sub(r"\s+", " ", name).strip()


class PerformerImagePipeline(ImagesPipeline):
    """Döp varje bild med Förnamn Efternamn-XXX.jpg i undermapp med samma namn."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._counters: dict[str, int] = {}

    def get_media_requests(self, item, info):
        adapter = ItemAdapter(item)
        performer = adapter.get("name") or "unknown"
        cleaned = clean_name(performer)
        for url in adapter.get("image_urls", []):
            # Skicka med modellens namn; idx räknas i file_path
            yield scrapy.Request(url, meta={"performer": cleaned})

    def file_path(self, request, response=None, info=None, *, item=None) -> str:
        raw_name = request.meta.get("performer", "unknown")
        cleaned_name = clean_name(raw_name)

        # Uppdatera räknare per modell
        count = self._counters.get(cleaned_name, 0) + 1
        self._counters[cleaned_name] = count

        # Prefix utan mellanslag
        prefix = cleaned_name.replace(" ", "") or "unknown"
        # Filändelse
        url_path = urlparse(request.url).path
        ext = os.path.splitext(url_path)[1].lower() or ".jpg"

        filename = f"{prefix}-{count:03d}{ext}"
        # Spara i mapp med mellanslag i namnet
        return f"{cleaned_name}/{filename}"

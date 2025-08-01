# doppelganger/pipelines.py
import os
import re
import unicodedata
from urllib.parse import urlparse

import scrapy
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline

def clean_name(name: str) -> str:
    """
    Normalisera och rensa modellens namn, men behåll mellanslag.
    """
    # Normalisera Unicode (så Å ≠ A)
    name = unicodedata.normalize("NFKD", name)
    # Ta bort ogiltiga filsystemtecken men behåll mellanslag och bindestreck
    name = re.sub(r"[^\w\s-]", "", name, flags=re.UNICODE)
    # Ersätt flera mellanslag med ett enda mellanslag
    return re.sub(r"\s+", " ", name).strip()


class PerformerImagePipeline(ImagesPipeline):
    """Döp varje bild med FörnamnEfternamn-XXX.jpg i undermapp med mellanslag i namnet."""

    def get_media_requests(self, item, info):
        adapter = ItemAdapter(item)
        performer = adapter.get("name") or "unknown"
        for idx, url in enumerate(adapter.get("image_urls", []), start=1):
            yield scrapy.Request(url, meta={"performer": performer, "idx": idx})

    def file_path(
        self,
        request: scrapy.http.Request,
        response: scrapy.http.Response = None,
        info: object = None,
        *,
        item: scrapy.Item = None,
    ) -> str:
        # 1) Rensa modellens namn – behåll mellanslag
        raw_name = request.meta.get("performer", "unknown")
        cleaned_name = clean_name(raw_name)

        # 2) Prefix utan mellanslag (används i filnamnet)
        prefix = cleaned_name.replace(" ", "") or "unknown"

        # 3) Filändelse från URL
        url_path = urlparse(request.url).path
        ext = os.path.splitext(url_path)[1].lower() or ".jpg"

        # 4) Index för numrering från meta
        idx = int(request.meta.get("idx", 0))

        # 5) Skapa filnamn
        filename = f"{prefix}-{idx:03d}{ext}"

        # 6) Spara i undermapp med mellanslag i mappnamnet
        return f"{cleaned_name}/{filename}"
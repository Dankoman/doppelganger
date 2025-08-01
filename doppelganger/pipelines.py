import os
import re
import unicodedata
from urllib.parse import urlparse

import scrapy
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline


def clean_name(name: str) -> str:
    # Normalisera Unicode (så Å ≠ A)
    name = unicodedata.normalize("NFKD", name)
    # Ta bort ogiltiga filsystemtecken men behåll mellanslag
    name = re.sub(r"[^\w\s-]", "", name, flags=re.UNICODE)
    # Ersätt flera mellanslag med ett enda mellanslag
    return re.sub(r"\s+", " ", name).strip()


class PerformerImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        adapter = ItemAdapter(item)
        performer = adapter.get("name") or "unknown"
        for idx, url in enumerate(adapter.get("image_urls", []), start=1):
            yield scrapy.Request(url, meta={"performer": performer, "idx": idx})

    def file_path(
    self,
    request: scrapy.http.Request,
    response: Optional[scrapy.http.Response] = None,
    info: Optional[object] = None,
    *,
    item: Optional[scrapy.Item] = None,
) -> str:
    raw_name = request.meta.get("performer", "unknown")

    # Rensa bort specialtecken men behåll mellanslag
    cleaned_name = re.sub(r"[^\w\s-]", "", raw_name)
    cleaned_name = re.sub(r"\s+", " ", cleaned_name).strip()

    # Använd detta för prefix utan mellanslag
    prefix = cleaned_name.replace(" ", "") or "unknown"

    # Filändelse
    url_path = urlparse(request.url).path
    ext = os.path.splitext(url_path)[1].lower() or ".jpg"

    # Index för numrering
    idx = int(request.meta.get("idx", 0))

    # Spara i mapp med mellanslag i namnet
    return f"{cleaned_name}/{prefix}-{idx:03d}{ext}"

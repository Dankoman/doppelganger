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

    def file_path(self, request, response=None, info=None, *, item=None):
        # 1) Rensa namn och bygg prefix
        raw_name = request.meta.get("performer", "unknown")
        cleaned_name = clean_name(raw_name)
        prefix = cleaned_name.replace(" ", "") or "unknown"

        # 2) Hämta filändelse från URL
        url_path = urlparse(request.url).path
        ext = os.path.splitext(url_path)[1].lower() or ".jpg"

        # 3) Numrera bilder
        idx = int(request.meta.get("idx", 0))

        # 4) Returnera sökväg: "Claudia Valentine/ClaudiaValentine-001.jpg"
        return os.path.join(cleaned_name, f"{prefix}-{idx:03d}{ext}")

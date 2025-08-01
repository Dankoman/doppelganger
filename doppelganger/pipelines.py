import os
import re
from urllib.parse import urlparse

import scrapy
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline


class PerformerImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        adapter = ItemAdapter(item)
        performer = adapter.get("name") or "unknown"
        for idx, url in enumerate(adapter.get("image_urls", []), start=1):
            yield scrapy.Request(url, meta={"performer": performer, "idx": idx})

    def file_path(self, request, response=None, info=None, *, item=None):
        # 1) Rensa modellens namn för mappnamnet (med mellanslag kvar)
        raw_name = request.meta.get("performer", "unknown")
        cleaned_name = re.sub(r"[^\w\s-]", "", raw_name)  # Tillåt mellanslag och bindestreck
        cleaned_name = re.sub(r"\s+", " ", cleaned_name).strip()

        # 2) Ta bort mellanslag för prefix (filnamn)
        prefix = cleaned_name.replace(" ", "") or "unknown"

        # 3) Hämta filändelse
        url_path = urlparse(request.url).path
        ext = os.path.splitext(url_path)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            ext = ".jpg"  # fallback om otillförlitlig

        # 4) Bildindex
        idx = int(request.meta.get("idx", 0))

        # 5) Slutlig path
        return f"{cleaned_name}/{prefix}-{idx:03d}{ext}"

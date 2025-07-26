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
        # 1) Rensa mappnamn – endast bokstäver, siffror, mellanslag
        raw_name = request.meta.get("performer", "unknown")
        cleaned_name = re.sub(r"[^\w\s]", "", raw_name)        # Ta bort specialtecken
        cleaned_name = re.sub(r"\s+", " ", cleaned_name).strip()  # Trimma mellanslag

        # 2) Hämta filändelse från URL
        url_path = urlparse(request.url).path
        ext = os.path.splitext(url_path)[1].lower() or ".jpg"

        # 3) Numrera bilder
        idx = int(request.meta.get("idx", 0))

        return f"{cleaned_name}/{idx:03d}{ext}"

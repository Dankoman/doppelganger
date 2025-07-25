import os
import re
from urllib.parse import urlparse

import scrapy
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline


class PerformerImagePipeline(ImagesPipeline):

    def get_media_requests(self, item, info):
        adapter   = ItemAdapter(item)
        performer = adapter.get("performer") or adapter.get("name") or "unknown"

        for idx, url in enumerate(adapter.get("image_urls", []), start=1):
            yield scrapy.Request(url, meta={"performer": performer, "idx": idx})

    def file_path(self, request, response=None, info=None, *, item=None):
        # 1) Mappnamn – behåll mellanslag, ta bort ogiltiga FS-tecken
        raw = request.meta.get("performer", "unknown")
        safe_dir = re.sub(r'[\\/*?:"<>|]', " ", raw).strip()

        # 2) Filändelse
        path = urlparse(request.url).path
        ext = os.path.splitext(path)[1].lower() or ".jpg"

        # 3) Löpnummer per person (000, 001, 002 …)
        idx = int(request.meta.get("idx", 0))
        return f"{safe_dir}/{idx:03d}{ext}"

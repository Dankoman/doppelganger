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
            # skicka med namn och index för numrering
            yield scrapy.Request(url, meta={"performer": performer, "idx": idx})

    def file_path(self, request, response=None, info=None, *, item=None):
        # 1) Hämta namnet från meta och rensa specialtecken (men behåll mellanslag)
        raw_name = request.meta.get("performer", "unknown")
        folder_name = re.sub(r"[^\w\s]", "", raw_name).strip()

        # 2) Skapa prefix (för filnamnet) utan mellanslag
        prefix = folder_name.replace(" ", "") or "unknown"

        # 3) Hämta filändelse från URL
        url_path = urlparse(request.url).path
        ext = os.path.splitext(url_path)[1].lower() or ".jpg"

        # 4) Numrera bilder
        idx = int(request.meta.get("idx", 0))

        # 5) Sätt sökväg: 'Förnamn Efternamn/FörnamnEfternamn-001.jpg'
        return f"{folder_name}/{prefix}-{idx:03d}{ext}"

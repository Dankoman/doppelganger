import re
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline

class PerformerImagePipeline(ImagesPipeline):          # <-- namn matchar spidern

    def file_path(self, request, response=None, info=None, *, item=None):
        """
        Spara varje bild som <sanerat_namn>/<originalfil>.jpg
        """
        performer = ItemAdapter(item).get("performer", "unknown")
        safe_dir  = re.sub(r"[^a-zA-Z0-9 -]", "_", performer)
        image_name = request.url.split("/")[-1]
        return f"{safe_dir}/{image_name}"

import scrapy
from urllib.parse import urljoin
from ..items import PerformerThumb


class ThumbnailSeriesSpider(scrapy.Spider):
    name = "thumbnailseries"
    allowed_domains = ["thumbnailseries.com"]
    start_urls = ["https://www.thumbnailseries.com/pornstars/"]

    custom_settings = {                       # aktivera pipelinen endast för denna spindel
        "ITEM_PIPELINES": {
            "doppelganger.pipelines.PerformerImagePipeline": 1,
        }
    }

    def parse(self, response):
        # 1) Hitta alla performer-länkar på list­nings­sidan
        for a in response.css("main.archives a[href*='/pornstars/']"):
            url = a.attrib["href"]
            yield response.follow(url, self.parse_performer)

    def parse_performer(self, response):
        name = response.css("header h1::text").get().strip()
        # 2) Plocka ut samtliga thumbnail-URL:er (relativa → absolut via urljoin)
        thumbs = [
            urljoin(response.url, img.attrib["src"])
            for img in response.css("div.picture-gallery img[src]")
        ]
        if thumbs:
            yield PerformerThumb(performer=name, image_urls=thumbs)

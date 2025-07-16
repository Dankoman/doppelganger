import re
import scrapy
from urllib.parse import urljoin
from ..items import EgafdGalleryItem


class EgafdGallerySpider(scrapy.Spider):
    name = "egafd_gallery"
    allowed_domains = ["egafd.com"]

    # index-sidorna a–z
    start_urls = [
        f"https://www.egafd.com/actresses/index.php/index/{l}"
        for l in "abcdefghijklmnopqrstuvwxyz"
    ]

    custom_settings = {
        "ITEM_PIPELINES": {"doppelganger.pipelines.PerformerImagePipeline": 1},
        "DOWNLOAD_DELAY": 0.5,                # var snäll mot sajten
    }

    # ---------- 1) Index ----------
    def parse(self, response):
        for row in response.css("table tr"):
            cells = row.css("td")
            if len(cells) >= 3 and cells[2].xpath("normalize-space()").get() == "Yes":
                href = cells[0].css("a::attr(href)").get()
                if href:
                    yield response.follow(href, self.parse_detail)

    # ---------- 2) Detaljsida ----------
    def parse_detail(self, response):
        name = response.css("title::text").get(default="unknown").strip()

        # a) vanlig ikon-länk   <a href="...gallery.php..."><img alt="Gallery"></a>
        gallery_href = response.css('a[href*="gallery.php"]::attr(href)').get()

        # b) fallback: textlänk med IMAGE GALLERY (ifall sajtstrukturen ändras)
        if not gallery_href:
            gallery_href = response.xpath(
                '//a[translate(normalize-space(text()), '
                '"abcdefghijklmnopqrstuvwxyz","ABCDEFGHIJKLMNOPQRSTUVWXYZ")='
                '"IMAGE GALLERY"]/@href'
            ).get()

        if gallery_href:
            yield response.follow(gallery_href,
                                  self.parse_gallery,
                                  cb_kwargs={"name": name})

    # ---------- 3) Galleri ----------
    def parse_gallery(self, response, name):
        img_urls = [
            urljoin(response.url, src)
            for src in response.css("img::attr(src)").getall()
            if re.search(r"\.(jpe?g|png|gif)$", src, re.I)
        ]
        if img_urls:
            yield EgafdGalleryItem(performer=name, image_urls=img_urls)

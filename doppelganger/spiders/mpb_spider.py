import re
import scrapy
from urllib.parse import urljoin
from doppelganger.items import PerformerThumb

class MPBSpider(scrapy.Spider):
    name = "mpb_all"
    allowed_domains = ["mypornstarbook.net"]
    start_urls = ["https://www.mypornstarbook.net/pornstars/all-porn-stars.php"]

    def parse(self, response):
        # alla profil-länkar (både /pornstars/ och ev. /promstars/)
        for a in response.xpath('//a[(contains(@href,"/pornstars/")) and contains(@href,"index.php")]'):
            href = a.xpath('@href').get()
            if not href:
                continue
            profile_url = response.urljoin(href)

            # Namn i alt-attributet
            name = (a.xpath('.//img/@alt').get() or
                    a.xpath('normalize-space(string())').get() or "")

            if not name:
                m = re.search(r'/pornstars/.+?/(.+?)/index\\.php', href)
                if m:
                    name = m.group(1).replace('_', ' ').title()

            # profilbild på list-sidan (face.jpg)
            first_img = a.xpath('.//img/@src').re_first(r'.*/face\\.(?:jpg|jpeg|png|webp)$')
            collected = []
            if first_img:
                collected.append(response.urljoin(first_img))

            yield scrapy.Request(
                profile_url,
                callback=self.parse_profile,
                cb_kwargs={'name': name, 'collected': collected}
            )

    def parse_profile(self, response, name, collected):
        urls = set(collected)

        # alla img-taggar på profilsidan
        for src in response.css('img::attr(src)').getall():
            if src.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                urls.add(urljoin(response.url, src))

        # följ alla galleri-sidor
        for gl in response.xpath('//a[contains(@href,"/gallery") and contains(@href,"index.php")]/@href').getall():
            yield response.follow(gl,
                                  callback=self.parse_gallery,
                                  cb_kwargs={'name': name, 'collected': urls})

        # Om inga gallerier hittades, yield direkt
        if not any("gallery" in u for u in response.xpath('//a/@href').getall()):
            yield PerformerThumb(performer=name, image_urls=list(urls))

    def parse_gallery(self, response, name, collected):
        urls = set(collected)
        for src in response.xpath('//img[contains(@src,"/thumbnails/")]/@src').getall():
            if src.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                urls.add(response.urljoin(src))
        yield PerformerThumb(performer=name, image_urls=list(urls))

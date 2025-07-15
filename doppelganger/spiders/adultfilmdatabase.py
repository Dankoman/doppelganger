# doppelganger/spiders/adultfilmdatabase.py

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from doppelganger.items import Actress

class AdultfilmdatabaseSpider(CrawlSpider):
    name = "adultfilmdatabase"
    allowed_domains = ["adultfilmdatabase.com"]
    start_urls = [
        "https://www.adultfilmdatabase.com/browse.cfm?type=actor"
    ]

    rules = (
        # 1) Fånga startsidan OCH alla pagineringssidor för actor
        Rule(
            LinkExtractor(
                allow=r"browse\.cfm\?type=actor(?:&startFilter=\d+)?"
            ),
            follow=True
        ),
        # 2) Extrahera varje skådespelar-sida
        Rule(
            LinkExtractor(
                allow=r"/actor/[^/]+"
            ),
            callback="parse_actress_link"
        ),
    )

    def parse_actress_link(self, response):
        item = Actress()
        item["name"] = response.xpath('//h1/text()').get().strip()
        rel = response.xpath('//img[contains(@src,"Graphics/PornStars")]/@src').get()
        item["image_urls"] = [response.urljoin(rel)] if rel else []
        yield item

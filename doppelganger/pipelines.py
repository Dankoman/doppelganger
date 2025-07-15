from scrapy.pipelines.images import ImagesPipeline
import hashlib
from scrapy.utils.python import to_bytes
from scrapy.http import Request

class DoppelgangerPipeline(ImagesPipeline):

    def file_path(self, request, response=None, info=None, *, item=None):
        """
        Bygg sökväg som full/<actress_name>/<hash>.jpg
        """
        url = request.url
        image_guid = hashlib.sha1(to_bytes(url)).hexdigest()
        # Försök hämta namn från item, annars fallback på meta
        folder_name = item.get('name') if item and item.get('name') \
                      else request.meta.get('name', 'unknown')
        return f'full/{folder_name}/{image_guid}.jpg'

    def get_media_requests(self, item, info):
        """
        Skicka med bara det fält (name) som behövs i meta,
        så att file_path får rätt folder_name.
        """
        for url in item.get(self.images_urls_field, []):
            yield Request(url, meta={'name': item.get('name')})

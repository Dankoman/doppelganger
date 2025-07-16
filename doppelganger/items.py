# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import scrapy
from scrapy.item import Item, Field


class DoppelgangerItem(Item):
    # define the fields for your item here like:
    name = Field()


class Actress(Item):
    name = Field()
    image_urls = Field()
    images = Field()

class PerformerThumb(scrapy.Item):
    performer   = Field()
    image_urls  = Field()      # obligatoriskt namn för ImagesPipeline
    images      = Field()      # här lagrar pipelinen meta om nedladdningen

class EgafdGalleryItem(scrapy.Item):
    performer   = Field()
    image_urls  = Field()   # krävs av ImagesPipeline
    images      = Field()

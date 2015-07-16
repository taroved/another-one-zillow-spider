# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class RealestateItem(scrapy.Item):
    # define the fields for your item here like:
    state = scrapy.Field()
    city = scrapy.Field()
    neighborhood = scrapy.Field()
    zip_code = scrapy.Field()
    listing_type = scrapy.Field()
    property_type = scrapy.Field()
    construction = scrapy.Field()
    lot = scrapy.Field()
    mls_number = scrapy.Field()
    parcel = scrapy.Field()
    price = scrapy.Field()
    zestimate = scrapy.Field()
    zestimate_rent = scrapy.Field()
    built_in = scrapy.Field()
    bedrooms = scrapy.Field()
    baths = scrapy.Field()
    address = scrapy.Field()
    url = scrapy.Field()
    description = scrapy.Field()
    listing_provided_by = scrapy.Field()
    timestamp = scrapy.Field()


from scrapy.contrib.loader import ItemLoader
from scrapy.contrib.loader.processor import Compose, Join, TakeFirst, MapCompose

from realestate.items import RealestateItem



class ZillowProcessor(ItemLoader):
    default_item_class = RealestateItem
    
    default_output_processor = TakeFirst()
    
    description_out = Join(' ')
    listing_provided_by_out = Compose(Join(''), lambda x: x.strip())

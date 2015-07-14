# -*- coding: utf-8 -*-
import json
import time

from scrapy.http import Request
from scrapy.http.response.html import HtmlResponse
from scrapy.selector import Selector
from scrapy.contrib.linkextractors import LinkExtractor
import scrapy

from w3lib import url

from realestate.processors import ZillowProcessor


class ZillowSpider(scrapy.Spider):
    name = "zillow"
    allowed_domains = ["zillow.com"]
    start_urls = (
        (
         'http://www.zillow.com/homes/Orlando-FL_rb/',
         'http://www.zillow.com/search/GetResults.htm?spt=homes&status=110011&lt=111101&ht=111111&pr=,&mp=,&bd=0%2C&ba=0%2C&sf=,&lot=,&yr=,&pho=0&pets=0&parking=0&laundry=0&pnd=1&red=0&zso=0&days=any&ds=all&pmf=1&pf=1&zoom=10&rect=-81814842,28313146,-80922203,28648114&p=1&sort=featured&search=list&disp=1&rid=13121&rt=6&listright=true&isMapSearch=0&zoom=10'
         #'http://www.zillow.com/search/GetResults.htm?spt=homes&status=110001&lt=111101&ht=111111&pr=,&mp=,&bd=0%2C&ba=0%2C&sf=,&lot=,&yr=,&pho=0&pets=0&parking=0&laundry=0&pnd=0&red=0&zso=0&days=any&ds=all&pmf=1&pf=1&zoom=10&rect=-81814842,28355755,-80922203,28606829&p=3&sort=days&search=list&disp=1&rid=13121&rt=6&listright=true&isMapSearch=false&zoom=10',
        ),
    )

    meta_url_tpl = 'zillow_url_tpl'

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url[0],  meta={self.meta_url_tpl: url[1]},
                          callback=self.parse_pages)
            
            
    def parse_pages(self, response):
        # get count of pages
        page_count = int(response.xpath('(//*[@id="search-pagination-wrapper"]//a[boolean(number(.))]/text())[last()]').extract()[0])
        
        # open pages
        #for page in xrange(page_count - 1):
        for page in xrange(1):
            yield Request(url.add_or_replace_parameter(response.meta[self.meta_url_tpl], 'p', page), callback=self.parse_page_json)

    def parse_page_json(self, response):
        j_response = json.loads(response.body_as_unicode())
        html = j_response["list"]["listHTML"]

        # parse list
        for link in LinkExtractor(
            restrict_xpaths='//article//*[@class="property-info"]/dt[1][contains(., "For Sale")]/../strong/dt'
        ).extract_links(HtmlResponse(response.url, body=html.encode('utf8'), encoding='utf8')):
            yield Request(link.url, callback=self.parse_details)

    def parse_details(self, response):
        """Parse house details into item.

        @url http://www.zillow.com/homedetails/2608-S-2nd-St-Austin-TX-78704/29475100_zpid/
        @returns items 1 1
        @scrapes state city neighborhood zip_code listing_type property_type construction lot parcel price zestimate zestimate_rent built_in bedrooms baths address url timestamp
        """
        l = ZillowProcessor(response=response)
        l.selector = Selector(response)
        l.add_value('state', 'FL')
        l.add_value('city', 'Orlando')
        l.add_xpath('neighborhood', '//h2/text()', re=r"Neighborhood: (.*)")
        l.add_xpath('zip_code', '(//h1)[1]/span/text()', re=r"(\d+)$")
        l.add_value('listing_type', 'For Sale')
        #import pdb
        #pdb.set_trace()
        l.add_xpath('property_type', '//h4[text()="Facts"]/..//li/text()', re=r"(Single Family|Condo)")
        l.add_xpath('construction', '(//h1)[1]/../h3/span/text()', re=r"([\d,]+) sqft")
        l.add_xpath('lot', '//h4[text()="Facts"]/..//li/text()', re=r"Lot: ([\d,]+) sqft")
        l.add_xpath('mls_number', '//h4[text()="Facts"]/..//li/text()', re=r"MLS #: (\d+)")
        l.add_value('parcel', 'na')  # not found
        l.add_xpath('price', '//*[@class="estimates"]//*[contains(@class,"main-row")]/span/text()')
        l.add_xpath('zestimate', '//*[@class="zest-value"]/text()')
        l.add_xpath('zestimate_rent', '//*[@class="zest-title" and contains(.,"Rent Zestimate")]/../*[@class="zest-value"]/text()',
                    re=r"(\$[\d,]+)")
        l.add_xpath('built_in', '//h4[text()="Facts"]/..//li/text()', re=r"Built in (\d+)")
        l.add_xpath('bedrooms', '//*[@class="zsg-layout-top"]', re=r"has (\d+) bedroom")
        l.add_xpath('baths', '//*[@class="zsg-layout-top"]', re=r"(\d+) bath")
        l.add_xpath('address', '(//h1)[1]/text()', re=r"(.*),")
        l.add_value('url', response.url)
        l.add_value('timestamp', time.time())
        
        yield l.load_item()
        
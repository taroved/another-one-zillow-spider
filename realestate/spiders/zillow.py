# -*- coding: utf-8 -*-
import json

from scrapy.http import Request, Response
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
         'http://www.zillow.com/search/GetResults.htm?spt=homes&status=110001&lt=111101&ht=111111&pr=,&mp=,&bd=0%2C&ba=0%2C&sf=,&lot=,&yr=,&pho=0&pets=0&parking=0&laundry=0&pnd=0&red=0&zso=0&days=any&ds=all&pmf=1&pf=1&zoom=10&rect=-81814842,28355755,-80922203,28606829&p=3&sort=days&search=list&disp=1&rid=13121&rt=6&listright=true&isMapSearch=false&zoom=10',
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
        for page in xrange(page_count - 1):
            yield Request(url.add_or_replace_parameter(response.meta[self.meta_url_tpl], 'p', page), callback=self.parse_page_json)

    def parse_page_json(self, response):
        j_response = json.loads(response.body_as_unicode())
        import pdb
        pdb.set_trace()
        html = j_response["list"]["listHTML"]

        # parse list
        for link in LinkExtractor(
            restrict_xpaths='//article//*[@class="property-info"]/dt[1][contains(., "For Sale")]/../strong/dt'
        ).extract_links(Response(response.url, body=html.encode('utf8'))):
            yield Request(link.url, callback=self.parse_details)

    def parse_details(self, response):
        l = ZillowProcessor(response=response)
        l.selector = Selector(response)
        l.add_xpath('address', '(//h1)[1]//text()')
        
        yield l.load_item()
        
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
        ),
        #(
        #    'http://www.zillow.com/homes/Tampa-FL_rb/',
        #    'http://www.zillow.com/search/GetResults.htm?spt=homes&status=110011&lt=111101&ht=111111&pr=,&mp=,&bd=0%2C&ba=0%2C&sf=,&lot=,&yr=,&pho=0&pets=0&parking=0&laundry=0&pnd=0&red=0&zso=0&days=any&ds=all&pmf=1&pf=1&zoom=10&rect=-82900429,27873983,-82007790,28118319&p=1&sort=featured&search=maplist&disp=1&rid=41176&rt=6&listright=true&isMapSearch=1&zoom=10',
        #),
        #(
        #    'http://www.zillow.com/homes/Miami-FL_rb/',
        #    'http://www.zillow.com/search/GetResults.htm?spt=homes&status=110011&lt=111101&ht=111111&pr=,&mp=,&bd=0%2C&ba=0%2C&sf=,&lot=,&yr=,&pho=0&pets=0&parking=0&laundry=0&pnd=0&red=0&zso=0&days=any&ds=all&pmf=1&pf=1&zoom=10&rect=-80677071,25657619,-79784432,25906791&p=2&sort=featured&search=list&disp=1&rid=12700&rt=6&listright=true&isMapSearch=false&zoom=10',
        #),
        #(
        #    'http://www.zillow.com/homes/St.-Petersburg-FL_rb/',
        #    'http://www.zillow.com/search/GetResults.htm?spt=homes&status=110011&lt=111101&ht=111111&pr=,&mp=,&bd=0%2C&ba=0%2C&sf=,&lot=,&yr=,&pho=0&pets=0&parking=0&laundry=0&pnd=0&red=0&zso=0&days=any&ds=all&pmf=1&pf=1&zoom=10&rect=-83100930,27617231,-82208291,27937393&p=2&sort=featured&search=list&disp=1&rid=26922&rt=6&listright=true&isMapSearch=false&zoom=10',
        #),
        #(
        #    'http://www.zillow.com/homes/jacksonville-FL_rb/',
        #    'http://www.zillow.com/search/GetResults.htm?spt=homes&status=110011&lt=111101&ht=111111&pr=,&mp=,&bd=0%2C&ba=0%2C&sf=,&lot=,&yr=,&pho=0&pets=0&parking=0&laundry=0&pnd=0&red=0&zso=0&days=any&ds=all&pmf=1&pf=1&zoom=9&rect=-82575303,30032244,-80790024,30656815&p=2&sort=featured&search=list&disp=1&rid=25290&rt=6&listright=true&isMapSearch=false&zoom=9',
        #),
    )
    
    prices = ((0, 1000), (1001, 25000), (25001, 35000), (35001, 50000), (50001, 60000), (60001, 70000),  (70001, 80000), (80001, 90000), (90001, 100000),
              (100001, 110000), (110001, 120000), (120001, 130000), (130001, 140000), (140001, 150000), (150001, 160000), (160001, 170000), (170001, 180000), (180001, 190000), (190001, 200000),
              (2000001, 20000000))    
    meta_url_tpl = 'zillow_url_tpl'
    meta_loader = 'zillow_loader'

    site_path = 'http://www.zillow.com'

    def start_requests(self):
        for start_url in self.start_urls:
            u = url.add_or_replace_parameter(start_url[1], 'p', 1) # page
            for price in self.prices:
                u = url.add_or_replace_parameter(u, 'pr', ",".join([str(p) for p in price])) 
                yield Request(u, callback=self.parse_pages_json)

    def parse_pages_json(self, response):
        # get count of pages
        j_response = json.loads(response.body_as_unicode())
        page_count = int(j_response["list"]["numPages"])

        # open pages
        for page in xrange(page_count - 1):
            yield Request(url.add_or_replace_parameter(response.url, 'p', page), callback=self.parse_page_json)

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
        @scrapes state city neighborhood zip_code listing_type property_type construction lot parcel price zestimate zestimate_rent built_in bedrooms baths address description listing_provided_by url timestamp
        """
        l = ZillowProcessor(response=response)
        l.selector = Selector(response)
        l.add_value('state', 'FL')
        l.add_value('city', 'Orlando')
        l.add_xpath('neighborhood', '//h2/text()', re=r"Neighborhood: (.*)")
        l.add_xpath('zip_code', '(//h1)[1]/span/text()', re=r"(\d+)$")
        l.add_value('listing_type', 'For Sale')
        l.add_xpath(
            'property_type', '//h4[text()="Facts"]/..//li/text()', re=r"(Single Family|Multi Family|Condo|Townhouse)")
        l.add_xpath(
            'construction', '(//h1)[1]/../h3/span/text()', re=r"([\d,]+) sqft")
        l.add_xpath(
            'lot', '//h4[text()="Facts"]/..//li/text()', re=r"Lot: ([\d,]+) sqft")
        l.add_value('lot', 'na')
        l.add_xpath(
            'mls_number', '//h4[text()="Facts"]/..//li/text()', re=r"MLS #: (\S+)")
        l.add_value('mls_number', 'na')
        
        #import pdb
        #pdb.set_trace()
        l.add_xpath('parcel', '//li[starts-with(.,"Parcel #: ")]/text()', re=r"Parcel #: (\d+)")
        l.add_value('parcel', 'na')
        l.add_xpath(
            'price', '//*[@class="estimates"]//*[contains(@class,"main-row")]/span/text()')
        l.add_xpath('zestimate', '//*[@class="zest-value"]/text()')
        l.add_xpath('zestimate_rent', '//*[@class="zest-title" and contains(.,"Rent Zestimate")]/../*[@class="zest-value"]/text()',
                    re=r"(\$[\d,]+)")
        l.add_xpath(
            'built_in', '//h4[text()="Facts"]/..//li/text()', re=r"Built in (\d+)")
        l.add_xpath(
            'bedrooms', '//*[@class="zsg-layout-top"]', re=r"has (\d+) bedroom")
        l.add_xpath('baths', '//*[@class="zsg-layout-top"]', re=r"(\d+) bath")
        l.add_xpath('address', '(//h1)[1]/text()', re=r"(.*),")
        l.add_value('url', response.url)
        l.add_xpath('description', '(//*[@class="notranslate"])[1]/text()')
        l.add_value('timestamp', time.time())

        url = self.site_path + response.xpath('//script/text()').re(
            r'ajaxURL:"([^"]+)",jsModule:"z-complaint-manager-async-block"')[0]

        yield Request(url, callback=self.parse_listing_provided_by, meta={self.meta_loader: l})

    def parse_listing_provided_by(self, response):
        l = response.meta[self.meta_loader]

        j_response = json.loads(response.body_as_unicode())
        html = j_response["html"]
        resp = HtmlResponse(response.url, body=html.encode('utf8'), encoding='utf8')
        
        l.selector = Selector(resp)
        l.add_xpath('listing_provided_by', '//h2[text()="Listing Provided by"]/../*[2]//text()')
        
        yield l.load_item()
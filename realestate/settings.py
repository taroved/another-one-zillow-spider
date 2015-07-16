# -*- coding: utf-8 -*-

# Scrapy settings for realestate project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'realestate'

SPIDER_MODULES = ['realestate.spiders']
NEWSPIDER_MODULE = 'realestate.spiders'

ITEM_PIPELINES = {'realestate.pipelines.CSVPipeline': 300 }

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'realestate (+http://www.yourdomain.com)'

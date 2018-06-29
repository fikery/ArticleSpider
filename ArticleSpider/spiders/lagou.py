# -*- coding: utf-8 -*-
import datetime
import scrapy
from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from ArticleSpider.utils.common import getMd5
from ..items import LagouItemLoader,LagouJobItem


class LagouSpider(CrawlSpider):
    name = 'lagou'
    allowed_domains = ['www.lagou.com']
    start_urls = ['https://www.lagou.com/']

    rules = (
        # Rule(LinkExtractor(allow=('zhaopin/.*',)), follow=True),
        # Rule(LinkExtractor(allow=('gongsi/j\d+.html',)), follow=True),
        Rule(LinkExtractor(allow=r'jobs/\d+.html'), callback='parse_job', follow=True),

    )

    def parse_job(self, response):
        #解析拉勾网职位
        itemLoader=LagouItemLoader(item=LagouJobItem(),response=response)
        itemLoader.add_css('title','.job-name::attr(title)')
        itemLoader.add_value('url',response.url)
        itemLoader.add_value('urlmd5',getMd5(response.url))
        itemLoader.add_css('salary','.job_request .salary::text')
        itemLoader.add_xpath('job_city','//*[@class="job_request"]/p/span[2]/text()')
        itemLoader.add_xpath('work_years','//*[@class="job_request"]/p/span[3]/text()')
        itemLoader.add_xpath('degree_need','//*[@class="job_request"]/p/span[4]/text()')
        itemLoader.add_xpath('job_type','//*[@class="job_request"]/p/span[5]/text()')
        itemLoader.add_css('tags','.position-label li::text')
        itemLoader.add_css('publish_time','.publish_time::text')
        itemLoader.add_css('job_advantage','.job-advantage p::text')
        itemLoader.add_css('job_desc','.job_bt div')
        itemLoader.add_css('job_addr','.work_addr')
        itemLoader.add_css('company_name','#job_company dt a img::attr(alt)')
        itemLoader.add_css('company_url','#job_company dt a::attr(href)')
        itemLoader.add_value('crawl_time',datetime.datetime.now())

        item=itemLoader.load_item()

        return item

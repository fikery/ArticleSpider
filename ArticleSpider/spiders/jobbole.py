# -*- coding: utf-8 -*-
import datetime

import scrapy
from scrapy import Request
from urllib import parse
from ..items import JobboleArticleItem,ArticleItemLoader
from ..utils.common import getMd5

from selenium import webdriver
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals


class JobboleSpider(scrapy.Spider):
    name = "jobbole"
    allowed_domains = ["blog.jobbole.com"]
    start_urls = ['http://blog.jobbole.com/all-posts/']

    # def __init__(self):
    #     self.browser=webdriver.Chrome()
    #     super(JobboleSpider,self).__init__()
    #     dispatcher.connect(self.spider_closed,signals.spider_closed)
    #
    # def spider_closed(self,spider):
    #     #爬虫退出对时候关闭browser
    #     self.browser.quit()


    def parse(self, response):
        pass
        '''
        1.获取文章列表页具体文章url并交给解析函数解析详细信息
        2.获取下一页url并下载，重新调用parse函数
        '''
        postinfo=response.css('div.post.floated-thumb div.post-thumb a')
        nexturl=response.css('.next.page-numbers::attr(href)').extract_first('')
        for info in postinfo:
            url=info.css('::attr(href)').extract_first('')
            url=parse.urljoin(response.url,url)
            imgurl=info.css('img::attr(src)').extract_first('')
            yield Request(url=url,meta={'imgurl':imgurl},callback=self.parse_detail)

        if nexturl:
            yield Request(url=parse.urljoin(response.url,nexturl),callback=self.parse)

    def parse_detail(self,response):
        imgurl=response.meta['imgurl']
        #普通方式解析保存item
        # title=response.xpath('//div[@class="entry-header"]/h1/text()').extract_first('').strip()
        # createDate = response.xpath('//p[@class="entry-meta-hide-on-mobile"]/text()').extract_first('').replace('·','').strip()
        # praiseNum = response.xpath('//span[contains(@class,"vote-post-up")]/h10/text()').extract_first('')
        # collectNum=response.xpath('//span[contains(@class,"bookmark-btn")]/text()').extract_first('').replace('收藏','').strip()
        # commentNum=response.xpath('//span[contains(@class,"hide-on-480")]/text()').extract_first('').replace('评论','').strip()
        # content=response.xpath('//div[@class="entry"]').extract_first('')
        # tagsList=response.xpath('//p[@class="entry-meta-hide-on-mobile"]/a/text()').extract()
        # tags=','.join([x for x in tagsList if not x.strip().endswith('评论')])
        #
        # item=JobboleArticleItem()
        #
        # item['title']=title
        # item['url']=response.url
        # item['urlmd5']=getMd5(response.url)
        # try:
        #     createDate=datetime.datetime.strptime(createDate,'%Y/%m/%d')
        # except:
        #     createDate=datetime.datetime.today()
        # item['createDate']=createDate
        # item['imgurl']=[imgurl]
        # item['praiseNum']=praiseNum
        # item['collectNum']=collectNum
        # item['commentNum']=commentNum
        # item['content']=content
        # item['tags']=tags

        #通过itemloader加载item
        itemld=ArticleItemLoader(item=JobboleArticleItem(),response=response)

        itemld.add_xpath('title','//div[@class="entry-header"]/h1/text()')
        itemld.add_value('url',response.url)
        itemld.add_value('urlmd5',getMd5(response.url))
        itemld.add_xpath('createDate','//p[@class="entry-meta-hide-on-mobile"]/text()')
        itemld.add_value('imgurl',imgurl)
        itemld.add_xpath('praiseNum','//span[contains(@class,"vote-post-up")]/h10/text()')
        itemld.add_xpath('collectNum','//span[contains(@class,"bookmark-btn")]/text()')
        itemld.add_xpath('commentNum','//span[contains(@class,"hide-on-480")]/text()')
        itemld.add_xpath('tags','//p[@class="entry-meta-hide-on-mobile"]/a/text()')
        itemld.add_xpath('content','//div[@class="entry"]')

        item=itemld.load_item()

        yield item

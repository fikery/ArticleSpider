# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class JobboleArticleItem(scrapy.Item):
    # define the fields for your item here like:
    title = scrapy.Field()
    url=scrapy.Field()
    urlmd5=scrapy.Field()
    imgurl=scrapy.Field()
    imgpath=scrapy.Field()
    createDate=scrapy.Field()
    tags=scrapy.Field()
    content=scrapy.Field()
    praiseNum=scrapy.Field()
    collectNum=scrapy.Field()
    commentNum=scrapy.Field()
    pass

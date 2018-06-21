# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import MapCompose, TakeFirst, Join
from scrapy.loader import ItemLoader
import datetime


def dateConvert(value):
    try:
        value = value.replace('·', '').strip()
        createDate = datetime.datetime.strptime(value, '%Y/%m/%d')
    except:
        createDate = datetime.datetime.today()
    return createDate


def wordFilter(value):
    if '收藏' in value:
        value = value.replace('收藏', '').strip()
    if '评论' in value:
        value = value.replace('评论', '').strip()
    return value


def tagsFilter(value):
    if '评论' in value:
        return None  # 如果返回''，最后会多一个分隔符，形成a,,b的情况
    else:
        return value


def returnValue(value):
    return value


class JobboleArticleItem(scrapy.Item):
    # define the fields for your item here like:
    collection = 'jobboleArticle'  # 定义字段存储的表名

    title = scrapy.Field()
    url = scrapy.Field()
    urlmd5 = scrapy.Field()  # 对应mongodb其实不需要，对于mysql可以要
    imgurl = scrapy.Field(
        output_processor=MapCompose(returnValue)  # 图片下载用的是list形式，这里覆盖掉取第一个值
    )
    imgpath = scrapy.Field()
    createDate = scrapy.Field(
        input_processor=MapCompose(dateConvert)
    )
    tags = scrapy.Field(
        input_processor=MapCompose(tagsFilter),
        output_processor=Join(',')
    )
    content = scrapy.Field()
    praiseNum = scrapy.Field()
    collectNum = scrapy.Field(
        input_processor=MapCompose(wordFilter)
    )
    commentNum = scrapy.Field(input_processor=MapCompose(wordFilter))
    pass


class ArticleItemLoader(ItemLoader):
    # 自定义itemloader
    default_output_processor = TakeFirst()

# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import re
import scrapy
from scrapy.loader.processors import MapCompose, TakeFirst, Join
from scrapy.loader import ItemLoader
import datetime
from ArticleSpider.settings import SQL_DATETIME_FORMAT, SQL_DATE_FORMAT
from ArticleSpider.utils.common import extractNum
from w3lib.html import remove_tags


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

    def get_insert_sql(self):
        insert_sql = 'insert into jobboleArticle(title,url,urlmd5) values(%s,%s,%s)'
        params = (self['title'], self['url'], self['urlmd5'])
        return insert_sql, params


class ArticleItemLoader(ItemLoader):
    # 自定义itemloader
    default_output_processor = TakeFirst()


class ZhihuQuestionItem(scrapy.Item):
    zhihu_id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    answer_num = scrapy.Field()
    comments_num = scrapy.Field()
    watch_user_num = scrapy.Field()
    click_num = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        zhihu_id = int(''.join(self['zhihu_id']))
        topics = ','.join(self['topics'])
        url = ''.join(self['url'])
        title = self['title'][0]
        content = ''.join(self['content'])
        answer_num = int(self['answer_num'][0])
        comments_num = extractNum(''.join(self['comments_num']))
        watch_user_num = int(self['watch_user_num'][0].replace(',', ''))
        click_num = int(self['watch_user_num'][1].replace(',', ''))
        crawl_time = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)

        insert_sql = '''
                    insert into zhihu_question(zhihu_id,topics,url,title,content,answer_num,comments_num,
                      watch_user_num, click_num,crawl_time) 
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON DUPLICATE KEY UPDATE content=VALUES (content),answer_num=VALUES (answer_num),
                      comments_num=VALUES (comments_num),watch_user_num=VALUES (watch_user_num),click_num=VALUES (click_num)
                '''
        params = (
        zhihu_id, topics, url, title, content, answer_num, comments_num, watch_user_num, click_num, crawl_time)

        return insert_sql, params


class ZhihuAnswerItem(scrapy.Item):
    zhihu_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    praise_num = scrapy.Field()
    comments_num = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        create_time = datetime.datetime.fromtimestamp(self['create_time']).strftime(SQL_DATETIME_FORMAT)
        update_time = datetime.datetime.fromtimestamp(self['update_time']).strftime(SQL_DATETIME_FORMAT)
        crawl_time = self['crawl_time'].strftime(SQL_DATETIME_FORMAT)

        insert_sql = '''
            insert into zhihu_answer(zhihu_id,url,question_id,author_id,content,praise_num,comments_num,
              create_time,update_time,crawl_time)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE content=VALUES (content),praise_num=VALUES (praise_num),
              comments_num=VALUES (comments_num),update_time=VALUES (update_time)
            
        '''
        params = (
        self['zhihu_id'], self['url'], self['question_id'], self['author_id'], self['content'], self['praise_num'],
        self['comments_num'], create_time, update_time, crawl_time)
        return insert_sql, params


class LagouItemLoader(ItemLoader):
    # 自定义itemloader,取第一个
    default_output_processor = TakeFirst()


def remove_splash(value):
    # 去掉斜线
    value = value.replace('/', '').strip()
    return value


def handle_addr(value):
    temp = ''.join(value)
    temp = temp.replace('\n', '').replace(' ','').replace('查看地图', '').strip()
    return temp


class LagouJobItem(scrapy.Item):
    # 拉勾网职位信息
    title = scrapy.Field()
    url = scrapy.Field()
    urlmd5 = scrapy.Field()
    salary = scrapy.Field()
    job_city = scrapy.Field(
        input_processor=MapCompose(remove_splash),
    )
    work_years = scrapy.Field(
        input_processor=MapCompose(remove_splash),
    )
    degree_need = scrapy.Field(
        input_processor=MapCompose(remove_splash),
    )
    job_type = scrapy.Field()
    publish_time = scrapy.Field()
    tags = scrapy.Field(
        input_processor=Join(',')
    )
    job_advantage = scrapy.Field()
    job_desc = scrapy.Field()
    job_addr = scrapy.Field(
        input_processor=MapCompose(remove_tags, handle_addr)
    )
    company_url = scrapy.Field()
    company_name = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        # 对发布时间进行处理
        pubtime = self['publish_time']
        today = re.findall(r'\d{2}:\d{2}', pubtime)
        shortday = re.findall(r'(\d+)天前', pubtime)
        longday = re.findall(r'(\d{4}-\d{2}-\d{2})', pubtime)
        if today:
            pubtime = datetime.datetime.today().date().strftime(SQL_DATE_FORMAT)
        elif shortday:
            pubtime = datetime.datetime.today().date() - datetime.timedelta(int(shortday[0]))
        elif longday:
            pubtime = longday[0]

        insert_sql = '''
            insert into lagou_job(title,url,urlmd5,salary,job_city,work_years,degree_need,job_type,publish_time,
              tags,job_advantage,job_desc,job_addr,company_url,company_name,crawl_time)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE salary=VALUES (salary),job_desc=VALUES (job_desc)
        '''
        params = (self['title'], self['url'], self['urlmd5'], self['salary'], self['job_city'], self['work_years'],
                  self['degree_need'], self['job_type'], pubtime, self['tags'], self['job_advantage'],
                  self['job_desc'], self['job_addr'], self['company_url'], self['company_name'],
                  self['crawl_time'].strftime(SQL_DATETIME_FORMAT)
                  )

        return insert_sql, params


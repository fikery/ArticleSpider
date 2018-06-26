# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.pipelines.images import ImagesPipeline
import codecs,json,pymongo
# import pymssql
from scrapy.exporters import JsonItemExporter
from twisted.enterprise import adbapi
#异步插入mysql数据库
import pymysql
import pymysql.cursors

class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item

class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if 'imgurl' in item:
            for k,v in results:
                imgpath=v['path']
                item['imgpath']=imgpath
        return item

class JsonWithEncodingPipeline(object):
    #自定义json文件的导出
    def __init__(self):
        self.file=codecs.open('jobbole.json','w',encoding='utf8')

    def process_item(self, item, spider):
        lines=json.dumps(dict(item),ensure_ascii=False)+'\n'
        self.file.write(lines)
        return item

    def spider_closed(self,spider):
        self.file.close()

class JsonExporterPipeline(object):
    #调用scrapy提供的json exporter导出json文件
    def __init__(self):
        self.file=open('jobbleexport.json','wb')
        self.exporter=JsonItemExporter(self.file,encoding='utf8',ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self,spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

class MongodbPipeline(object):
    def __init__(self,mongo_uri,mongo_db):
        self.mongo_uri=mongo_uri
        self.mongo_db=mongo_db

    @classmethod
    def from_crawler(cls,crawler):
        '''拿到setting.py中的数据库配置信息'''
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DB')
        )

    def open_spider(self,spider):
        self.client=pymongo.MongoClient(self.mongo_uri)
        self.db=self.client[self.mongo_db]

    def close_spider(self,spider):
        self.client.close()

    def process_item(self, item, spider):
        self.db[item.collection].insert(dict(item))
        return item

class MssqlPipeline(object):
    #普通方式插入mssql数据库
    def __init__(self,conn):
        self.conn=conn
        self.cursor=self.conn.cursor()

    @classmethod
    def from_settings(cls,settings):
        dbparms=dict(
            host=settings['SQL_HOST'],
            user=settings['SQL_USER'],
            password=settings['SQL_PASSWORD'],
            database=settings['SQL_DBNAME'],
            charset='utf8',
        )
        # conn=pymssql.connect(**dbparms)
        # return cls(conn)

    def process_item(self, item, spider):
        #插入操作，基本上只需要修改这个地方，包括进行重复插入检查，异常处理
        insert_sql = 'insert into jobboleArticle(title,url,urlmd5) values(%s,%s,%s)'
        self.cursor.execute(insert_sql, (item['title'], item['url'], item['urlmd5']))
        self.conn.commit()

        return item

class MssqlTwistedPipeline(object):
    def __init__(self,dbpool):
        self.dbpool=dbpool

    @classmethod
    def from_settings(cls,settings):
        dbparms=dict(
            host=settings['SQL_HOST'],
            user=settings['SQL_USER'],
            passwd=settings['SQL_PASSWORD'],
            db=settings['SQL_DBNAME'],
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor,
            use_unicode=True
        )
        dbpool=adbapi.ConnectionPool('pymssql',**dbparms)

        return cls(dbpool)

    def process_item(self, item, spider):
        #使用twisted异步插入
        query=self.dbpool.runInteraction(self.do_insert,item)
        query.addErrback(self.handle_error,item,spider)

    def handle_error(self,failure,item,spider):
        #处理错误
        print(failure)

    def do_insert(self,cursor,item):
        #执行插入操作
        insert_sql = 'insert into jobboleArticle(title,url,urlmd5) values(%s,%s,%s)'
        cursor.execute(insert_sql,(item['title'],item['url'],item['urlmd5']))

        return item
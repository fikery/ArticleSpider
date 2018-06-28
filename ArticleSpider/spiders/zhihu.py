# -*- coding: utf-8 -*-
import base64
import json
import time

import re

import os

from urllib import parse

import datetime
import scrapy
from PIL import Image
from scrapy import Request, FormRequest
from scrapy.http.cookies import CookieJar
from scrapy.loader import ItemLoader
from ..items import ZhihuQuestionItem, ZhihuAnswerItem

from ArticleSpider.utils.common import getSignature


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']
    start_answer_url='https://www.zhihu.com/api/v4/questions/{0}/answers?include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit={1}&offset={2}&sort_by=default'
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
        'referer': 'https://www.zhihu.com/',
        'origin': 'https://www.zhihu.com',
        'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20',
    }
    cookjar = CookieJar()

    def parse(self, response):
        if '<span class="GlobalSideBar-navText">我的收藏</span>' not in response.text:
            if os.path.exists('cookies.txt'):
                os.remove('cookies.txt')
            print('登录失败，请重试')
            return
        # 开始爬取
        all_urls = response.css('a::attr(href)').extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        all_urls = filter(lambda x: True if x.startswith('https') else False, all_urls)
        for url in all_urls:
            question_id = re.findall(r'zhihu.com/question/(\d+)', str(url))
            if question_id:
                request_url = 'https://www.zhihu.com/question/' + question_id[0]
                # 加载cookie后，后续request不能加header，否则会变成未登录状态
                yield Request(url=request_url, meta={'qid': question_id[0]}, callback=self.parse_question)
                # break
            else:
                pass
                yield Request(url=url,callback=self.parse)

    def parse_question(self, response):
        # 提取question项信息
        itemLoader = ItemLoader(item=ZhihuQuestionItem(), response=response)
        if 'QuestionHeader' in response.text:
            itemLoader.add_css('title', '.QuestionHeader-title::text')
            itemLoader.add_css('content', '.QuestionHeader-detail')
            itemLoader.add_value('url', response.url)
            itemLoader.add_value('zhihu_id', response.meta['qid'])
            itemLoader.add_css('answer_num', '.List-headerText span::text')
            itemLoader.add_css('comments_num', '.QuestionHeader-Comment button::text')
            itemLoader.add_css('watch_user_num', '.NumberBoard-itemValue::text')  # 取的是个数组，包括关注人数和浏览次数
            itemLoader.add_css('topics', '.QuestionHeader-topics .Popover div::text')

            questionItem = itemLoader.load_item()
            yield Request(url=self.start_answer_url.format(response.meta['qid'],20,0),callback=self.parse_answer)
            yield questionItem

    def parse_answer(self,response):
        answer_json=json.loads(response.text)
        is_end=answer_json['paging']['is_end']
        totals=answer_json['paging']['totals']
        next_page=answer_json['paging']['next']
        #提取answer字段
        for answer in answer_json['data']:
            answerItem=ZhihuAnswerItem()
            answerItem['zhihu_id']=answer['id']
            answerItem['url'] = answer['url']
            answerItem['question_id'] = answer['question']['id']
            answerItem['author_id'] = answer['author']['id']
            answerItem['content'] = answer['content']
            answerItem['praise_num'] = answer['voteup_count']
            answerItem['comments_num'] = answer['comment_count']
            answerItem['create_time'] = answer['created_time']
            answerItem['update_time'] = answer['updated_time']
            answerItem['crawl_time'] = datetime.datetime.now()

            yield answerItem

        if not is_end:
            yield Request(url=next_page,callback=self.parse_answer)

    def start_requests(self):
        if os.path.exists('cookies.txt'):
            with open('cookies.txt', 'r') as f:
                cookiejar = f.read()
                p = re.compile(r'<Cookie (.*?) for .*?>')
                cookies = re.findall(p, cookiejar)
                cookies = (cookie.split('=', 1) for cookie in cookies)
                cookies = dict(cookies)
            yield Request(url='https://www.zhihu.com/', cookies=cookies, callback=self.parse)
        else:
            # 访问登陆界面，获取xsrf
            geturl = 'https://www.zhihu.com/signup'
            yield Request(url=geturl, meta={'cookiejar': self.cookjar}, headers=self.headers, callback=self.getxsrf)

    def getxsrf(self, response):
        # 提取xsrf
        cookie = response.headers.getlist('Set-Cookie')  # 获取响应cookie
        # cookie2 = response.request.headers.getlist('Cookie')#获取请求cookie
        xsrf = re.findall(r'xsrf=(.*?);', str(cookie))[0]
        captchaurl = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=en'
        return [
            Request(url=captchaurl, meta={'xsrf': xsrf, 'cookiejar': response.meta['cookiejar']}, headers=self.headers,
                    callback=self.login)]

    def login(self, response):
        xsrf = response.meta['xsrf']
        rescap = response.text
        self.headers.update({'x-xsrftoken': xsrf})
        loginurl = 'https://www.zhihu.com/api/v3/oauth/sign_in'
        account = '18637658720'
        password = 'LYBabc110119120'
        # account=input('输入邮箱/手机号:')
        # password=input('输入密码:')
        strtime = str(int((time.time() * 1000)))
        postData = {
            'timestamp': strtime,
            'signature': getSignature(strtime),
            'client_id': 'c3cef7c66a1843f8b3a9e6a1e3160e20',
            'username': account,
            'password': password,
            'grant_type': 'password',
            'source': 'com.zhihu.web',
            'captcha': '',
            'lang': 'en',
            'ref_source': 'other_',
            'utm_source': ''
        }
        if 'false' in rescap:
            return [FormRequest(url=loginurl, meta={'cookiejar': response.meta['cookiejar']}, formdata=postData,
                                headers=self.headers, callback=self.saveCookie)]
        else:
            # 爬取验证码并识别
            return [scrapy.Request(url=response.url, headers=self.headers, callback=self.getcaptcha, method='PUT')]

    def getcaptcha(self, response):
        try:
            img = json.loads(response.body)['img_base64']
        except ValueError:
            print('获取img_base64的值失败！')
        else:
            img = img.encode('utf8')
            img_data = base64.b64decode(img)
            with open('zhihu.jpg', 'wb') as f:
                f.write(img_data)
        img = Image.open('zhihu.jpg')
        img.show()
        img.close()
        captcha = input('请输入验证码：')
        post_data = {
            'input_text': captcha
        }
        return [scrapy.FormRequest(url='https://www.zhihu.com/api/v3/oauth/captcha?lang=en',
                                   meta={'cookiejar': response.meta['cookiejar']}, formdata=post_data,
                                   callback=self.captcha_login, headers=self.headers)]

    def captcha_login(self, response):
        try:
            cap_result = json.loads(response.body)['success']
            print(cap_result)
        except ValueError:
            print('关于验证码的POST请求响应失败!')
        else:
            if cap_result:
                print('验证成功!')
        post_url = 'https://www.zhihu.com/api/v3/oauth/sign_in'
        account = '18637658720'
        password = 'LYBabc110119120'
        # account=input('输入邮箱/手机号:')
        # password=input('输入密码:')
        strtime = str(int((time.time() * 1000)))
        post_data = {
            'timestamp': strtime,
            'signature': getSignature(strtime),
            'client_id': 'c3cef7c66a1843f8b3a9e6a1e3160e20',
            'username': account,
            'password': password,
            'grant_type': 'password',
            'source': 'com.zhihu.web',
            'captcha': '',
            'lang': 'en',
            'ref_source': 'other_',
            'utm_source': ''
        }

        return [scrapy.FormRequest(url=post_url, meta={'cookiejar': response.meta['cookiejar']}, formdata=post_data,
                                   headers=self.headers, callback=self.saveCookie)]

    def saveCookie(self, response):
        if response.status == 201:
            self.cookjar.extract_cookies(response, response.request)
            with open('cookies.txt', 'w') as f:
                for cookie in self.cookjar:
                    f.write(str(cookie) + '\n')

            with open('cookies.txt', 'r') as f:
                cookiejar = f.read()
                p = re.compile(r'<Cookie (.*?) for .*?>')
                cookies = re.findall(p, cookiejar)
                cookies = (cookie.split('=', 1) for cookie in cookies)
                cookies = dict(cookies)
            yield Request(url='https://www.zhihu.com/', cookies=cookies, callback=self.parse)

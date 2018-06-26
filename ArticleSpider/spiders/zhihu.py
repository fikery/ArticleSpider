# -*- coding: utf-8 -*-
import base64
import json
import time

import re

import os
import scrapy
from PIL import Image
from scrapy import Request, FormRequest
from scrapy.http.cookies import CookieJar

from ArticleSpider.utils.common import getSignature


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
        'referer': 'https://www.zhihu.com/',
        'origin': 'https://www.zhihu.com',
        'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20',
    }
    cookjar=CookieJar()

    def parse(self, response):
        if '注册' in response.text:
            if os.path.exists('cookies.txt'):
                os.remove('cookies.txt')
            print('登录失败，请重试')
        pass

    def start_requests(self):
        if os.path.exists('cookies.txt'):
            with open('cookies.txt', 'r') as f:
                cookiejar = f.read()
                p = re.compile(r'<Cookie (.*?) for .*?>')
                cookies = re.findall(p, cookiejar)
                cookies = (cookie.split('=', 1) for cookie in cookies)
                cookies = dict(cookies)
            yield Request(url='https://www.zhihu.com/', cookies=cookies,callback=self.parse)
        else:
            #访问登陆界面，获取xsrf
            geturl = 'https://www.zhihu.com/signup'
            yield Request(url=geturl,meta={'cookiejar': self.cookjar}, headers=self.headers, callback=self.getxsrf)

    def getxsrf(self, response):
        # 提取xsrf
        cookie = response.headers.getlist('Set-Cookie')  # 获取响应cookie
        # cookie2 = response.request.headers.getlist('Cookie')#获取请求cookie
        xsrf = re.findall(r'xsrf=(.*?);', str(cookie))[0]
        captchaurl = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=en'
        return [Request(url=captchaurl, meta={'xsrf': xsrf,'cookiejar':response.meta['cookiejar']}, headers=self.headers, callback=self.login)]

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
            return [FormRequest(url=loginurl,meta={'cookiejar': response.meta['cookiejar']}, formdata=postData, headers=self.headers, callback=self.saveCookie)]
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
        return [scrapy.FormRequest(url='https://www.zhihu.com/api/v3/oauth/captcha?lang=en',meta={'cookiejar': response.meta['cookiejar']}, formdata=post_data,
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

        return [scrapy.FormRequest(url=post_url,meta={'cookiejar': response.meta['cookiejar']}, formdata=post_data, headers=self.headers, callback=self.saveCookie)]

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
            yield Request(url='https://www.zhihu.com/', cookies=cookies,callback=self.parse)

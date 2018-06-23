# -*- coding: utf-8 -*-
import base64
import json
import time
import requests
import scrapy
from PIL import Image
from ArticleSpider.utils.common import getSignature


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']
    headers={
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
        'referer': 'https://www.zhihu.com/',
        'origin': 'https://www.zhihu.com',
        'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20',
    }
    session=requests.session()


    def parse(self, response):
        print('success')
        pass

    def start_requests(self):
        geturl='https://www.zhihu.com/signup'
        return [scrapy.Request(url=geturl,headers=self.headers, callback=self.login)]

    def getxsrf(self):
        geturl = 'https://www.zhihu.com/signup'
        response = self.session.get(url=geturl, headers=self.headers)
        return response.cookies['_xsrf']

    def getCaptcha(self):
        geturl = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=en'
        response = self.session.get(url=geturl, headers=self.headers)
        rescap = response.text
        if 'false' in rescap:
            return ''
        else:
            showCaptcha = json.loads(rescap)['img_base64']
            with open('captcha.jpg', 'wb') as f:
                f.write(base64.b64decode(showCaptcha))
            img = Image.open('captcha.jpg')
            img.show()
            # img.close()
            captcha = input('请输入验证码:')
            self.session.post(url=geturl, data={'input_text': captcha}, headers=self.headers)
            return captcha

    def login(self,response):
        account='18637658720'
        password='LYBabc110119120'
        # account=input('输入邮箱/手机号:')
        # password=input('输入密码:')
        posturl = 'https://www.zhihu.com/api/v3/oauth/sign_in'
        xsrf=self.getxsrf()
        self.headers.update({'x-xsrftoken': xsrf})
        strtime=str(int((time.time() * 1000)))
        postData={
            'timestamp': strtime,
            'signature': getSignature(strtime),
            'client_id': 'c3cef7c66a1843f8b3a9e6a1e3160e20',
            'username': account,
            'password': password,
            'grant_type': 'password',
            'source': 'com.zhihu.web',
            'captcha': self.getCaptcha(),
            'lang': 'en',
            'ref_source': 'other_',
            'utm_source': ''
        }
        response = self.session.post(url=posturl, data=postData, headers=self.headers)
        if response.status_code == 201:
            print('登陆成功')
            yield scrapy.Request(url='https://www.zhihu.com/settings/account',headers=self.headers,callback=self.parse)
        else:
            print('登录失败')

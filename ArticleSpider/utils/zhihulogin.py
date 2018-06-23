import base64
import hmac
import json
import time
from hashlib import sha1

import requests
import http.cookiejar as cookielib

from PIL import Image

headers={
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
    'referer': 'https://www.zhihu.com/',
    'origin': 'https://www.zhihu.com',

}
session=requests.session()
session.cookies=cookielib.LWPCookieJar(filename='cookie.txt')
# try:
#     session.cookies.load(ignore_discard=True)
# except:
#     print('cookie未能加载')

def get_xsrf_dc0():
    geturl='https://www.zhihu.com/signup'
    response=session.get(url=geturl,headers=headers)
    return response.cookies['_xsrf']

def getCaptcha():
    geturl='https://www.zhihu.com/api/v3/oauth/captcha?lang=en'
    response=session.get(url=geturl,headers=headers)
    rescap=response.text
    if 'false' in rescap:
        pass
        return ''
    else:
        showCaptcha=json.loads(rescap)['img_base64']
        with open('captcha.jpg','wb') as f:
            f.write(base64.b64decode(showCaptcha))
        img=Image.open('captcha.jpg')
        img.show()
        # img.close()
        captcha=input('请输入验证码:')
        session.post(url=geturl,data={'input_text':captcha},headers=headers)
        return captcha

def getSignature(strtime):
    h=hmac.new(key='d1b964811afb40118a12068ff74a12f4'.encode('utf8'),digestmod=sha1)
    grant_type='password'
    client_id='c3cef7c66a1843f8b3a9e6a1e3160e20'
    source='com.zhihu.web'
    h.update((grant_type+client_id+source+strtime).encode('utf8'))
    return h.hexdigest()

def login(name,psd):
    postUrl='https://www.zhihu.com/api/v3/oauth/sign_in'
    xsrf=get_xsrf_dc0()
    headers.update({
        'authorization':'oauth c3cef7c66a1843f8b3a9e6a1e3160e20',
        # 'x-udid':udid,
        'x-xsrftoken':xsrf
    })
    strtime=str(int((time.time() * 1000)))
    postData={
        'timestamp': strtime,
        'signature': getSignature(strtime),
        'client_id': 'c3cef7c66a1843f8b3a9e6a1e3160e20',
        'username': name,
        'password': psd,
        'grant_type':'password',
        'source':'com.zhihu.web',
        'captcha':getCaptcha(),
        'lang':'en',
        'ref_source':'other_',
        'utm_source':''
    }
    response=session.post(url=postUrl,data=postData,headers=headers)
    if response.status_code==201:
        session.cookies.save()
        print('登陆成功')
    else:
        print('登录失败')

def getData():
    #完成登陆后获取信息
    pass

def isLogin():
    #检查是否登陆
    settingurl='https://www.zhihu.com/settings/account'
    response=session.get(url=settingurl,headers=headers,allow_redirects=False)
    if response.status_code==200:
        print('已登陆')
        return True
    else:
        print('现在尝试登陆...')
        login('+8618637658720','LYBabc110119120')

# print(get_xsrf_dc0())
# getCaptcha()
# login('+8618637658720','LYBabc110119120')
isLogin()
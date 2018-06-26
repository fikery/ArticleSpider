import hashlib
import hmac


def getMd5(url):
    if isinstance(url,str):
        url=url.encode('utf8')
    m=hashlib.md5()
    m.update(url)
    return m.hexdigest()

def getSignature(strtime):
    #知乎的固定加密方式,后续可能更改
    h = hmac.new(key='d1b964811afb40118a12068ff74a12f4'.encode('utf8'), digestmod=hashlib.sha1)
    grant_type = 'password'
    client_id = 'c3cef7c66a1843f8b3a9e6a1e3160e20'
    source = 'com.zhihu.web'
    h.update((grant_type + client_id + source + strtime).encode('utf8'))
    return h.hexdigest()


if __name__=='__main__':
    print(getMd5('http://sss.com'))
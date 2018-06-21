import hashlib

def getMd5(url):
    if isinstance(url,str):
        url=url.encode('utf8')
    m=hashlib.md5()
    m.update(url)
    return m.hexdigest()

if __name__=='__main__':
    print(getMd5('http://sss.com'))
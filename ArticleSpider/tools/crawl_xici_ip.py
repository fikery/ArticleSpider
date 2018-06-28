import re
import requests
from scrapy.selector import Selector
import pymysql

conn=pymysql.connect(host='127.0.0.1',user='root',passwd='mysqlpassword',db='articlcspider',charset='utf8')
cursor=conn.cursor()

def crawl_ips():
    #爬取西刺代理IP
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
    }
    for i in range(1,20):
        html=requests.get('http://www.xicidaili.com/nn/{0}'.format(i),headers=headers)
        selector=Selector(html)
        trs=selector.css('#ip_list tr')
        ip_list=[]
        for tr in trs[1:]:
            speed_str=tr.css('.bar::attr(title)').extract_first()
            if speed_str:
                speed=float(speed_str.replace('秒',''))
                all_texts=tr.css('td').extract()
                all_texts=','.join(all_texts)
                ip=re.findall(r'<td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>',all_texts)[0]
                port=re.findall(r'<td>(\d+)</td>',all_texts)[0]
                ptype=re.findall(r'<td>(HTTPS?)</td>',all_texts)[0]
                ip_list.append((ip,port,speed,ptype))
        for ip_data in ip_list:
            cursor.execute(
                'insert into proxy_ip(ip,port,speed,proxy_type) VALUES(%s,%s,%s,%s)',(
                    ip_data[0],ip_data[1],ip_data[2],ip_data[3])
            )
            conn.commit()

class GetIP():
    def checkIP(self,ip,port):
        http_url='http://www.baidu.com'
        proxy_url='http://{0}:{1}'.format(ip,port)
        proxy_dict={
            'http':proxy_url,
            # 'https':proxy_url
        }
        try:
            response=requests.get(http_url,proxies=proxy_dict)
        except:
            print('无效ip')
            self.deleteIP(ip)
            return False
        else:
            code=response.status_code
            if code>=200 and code<300:
                print('有效ip')
                return True
            else:
                print('无效ip')
                self.deleteIP(ip)
                return False
    def deleteIP(self,ip):
        delete_sql='delete from proxy_ip where ip=%s'
        cursor.execute(delete_sql,ip)
        conn.commit()

    def getRandomIP(self):
        #从数据库中随机取一个ip
        sql='select ip,port from proxy_ip ORDER BY rand() limit 1'
        result=cursor.execute(sql)
        for ips in cursor.fetchall():
            ip,port=ips
            checkres=self.checkIP(ip,port)
            if checkres:
                return 'http://{0}:{1}'.format(ip,port)
            else:
                return self.getRandomIP()

if __name__ == '__main__':
    # crawl_ips()
    getip=GetIP()
    print(getip.getRandomIP())
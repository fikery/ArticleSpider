from selenium import webdriver
from scrapy.selector import Selector


#设置无图模式
chrome_opt=webdriver.ChromeOptions()
prefs={'profile.managed_default_content_settings.images':2}
chrome_opt.add_experimental_option('prefs',prefs)

#设置无头模式
chrome_opt.add_argument('--headless')

browser=webdriver.Chrome(chrome_options=chrome_opt)
url='https://www.qichacha.com/firm_c70a55cb048c8e4db7bca357a2c113e0.html'
browser.get(url)

browser.quit()

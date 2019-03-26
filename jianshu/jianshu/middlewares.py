# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
import requests
import json
from selenium import webdriver
import time
from scrapy.http.response.html import HtmlResponse

"""
SeleniumDownloadMiddleware的逻辑：
截获request，改用selenium打开进行一些模拟操作或获取ajax数据用，最后返回response让pipeline处理
"""

# 更换代理用
class MyDownloadMiddleware(object):
    def __init__(self):
        self.current_proxy = None

    def process_request(self, request, spider):
        if not self.current_proxy:
            self.current_proxy = self.get_proxy()

        request.meta['proxy'] = self.current_proxy

    def get_proxy(self):
        proxy_url = 'http://api.xdaili.cn/xdaili-api//greatRecharge/getGreatIp?spiderId=070e962a280945d5a41fdd33a8f6fe19&orderno=YZ2019254495QRXEoW&returnType=2&count=1'
        resp = requests.get(proxy_url)
        resp = json.loads(resp.text)
        data = resp['RESULT'][0]
        ip = data['ip']
        port = data['port']
        proxy = 'http://' + ip + ':' + port
        return proxy


# 重写DownloadMiddleware，用selenium替换原本的request请求
class SeleniumDownloadMiddleware(object):
    def __init__(self):
        # 本来在这里也想把代理加上去，但是selenium+代理实在太卡，遂放弃
        # proxy = self.get_proxy()
        # options = webdriver.ChromeOptions()
        # options.add_argument('--proxy-server=' + proxy)
        # # 有时候这里没有用options=可能会报错，系统不知道分配给哪个
        # self.driver = webdriver.Chrome(options=options)
        # print('代理' + proxy + '设置成功')

        self.driver = webdriver.Chrome()

    def process_request(self, request, spider):
        self.driver.get(request.url)

        # 避免内容未加载而返回太快的情况
        time.sleep(1)
        # 专题部分需要点击“展示更多按钮才能全部拿到”
        self.click_showmore()

        # 内容加载完毕后将内容打包成HtmlResponse返回给pipeline处理
        source = self.driver.page_source

        # 传入各种需要的参数
        # Cannot convert unicode body：未指定编码则报此错误
        response = HtmlResponse(url=request.url, body=source, request=request, encoding='utf-8')

        return response

    def click_showmore(self):
        # 用try是避免找不到元素而报错
        try:
            while True:
                showmore = self.driver.find_element_by_class_name('show-more')
                showmore.click()
                time.sleep(0.3)
                # 猜测下面的showmore好像只是确认元素是否存在而不会引起找不到元素的报错（貌似很妙，待验证）
                if not showmore:
                    break
        except:
            pass

    def get_proxy(self):
        proxy_url = 'http://api.xdaili.cn/xdaili-api//greatRecharge/getGreatIp?spiderId=070e962a280945d5a41fdd33a8f6fe19&orderno=YZ2019254495QRXEoW&returnType=2&count=1'
        resp = requests.get(proxy_url)
        resp = json.loads(resp.text)
        data = resp['RESULT'][0]
        ip = data['ip']
        port = data['port']
        proxy = 'http://' + ip + ':' + port
        return proxy
# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from jianshu.items import JianshuItem

"""
简书全站爬虫的逻辑链：
1.从简书的首页开始，通过推荐阅读找到下一篇文章的链接，爬完全站
2.筛选内容，返回item
3.设置pipeline，存储到哦数据库中
4.针对ajax数据或者需要模拟操作的数据可以用selenium，在middlewares里重写
"""

class JsSpiderSpider(CrawlSpider):
    name = 'js_spider'
    allowed_domains = ['jianshu.com']
    # 简书网站首页
    start_urls = ['https://www.jianshu.com/']

    rules = (
        # 筛选的链接规则不需要全部定义好，scrapy会帮忙补全一些网址必要的元素（前缀后缀等）
        # 这里的规则是p/后12位小写字母或数字
        Rule(LinkExtractor(allow=r'/p/[0-9a-z]{12}'), callback='parse_item', follow=True),
    )

    def parse_item(self, response):
        # 字数
        wordage = response.xpath('//div[@class="author"]//span[@class="wordage"]/text()').get()
        # “喜欢”的数量
        likes_count = response.xpath('//div[@class="author"]//span[@class="likes-count"]/text()').get()
        # 文章url
        article_url = response.url
        # 文章对应id（12位那个）
        article_id = article_url.split('?')[0].split('/')[-1]
        # 字数少于400且无阅读量则丢弃该页面
        # if int(wordage.split()[-1]) < 400 and int(likes_count.split()[-1]) ==0:
        if int(wordage.split()[-1]) < 400:
            # print('字数少于400且无阅读量丢弃该文章：' + article_id)
            print('字数少于400丢弃该文章：' + article_id)
            return
        # 文章标题
        title = response.xpath('//h1[@class="title"]/text()').get()
        # 头像链接
        avatar = response.xpath('//div[@class="author"]/a/img/@src').get()
        # 作者
        author = response.xpath('//div[@class="author"]//span[@class="name"]/a/text()').get()
        # 编辑时间
        publish_time = response.xpath('//div[@class="author"]//span[@class="publish-time"]/text()').get().replace('*', '')
        # 文章内容
        show_content = response.xpath('//div[@class="show-content"]').get()
        # 文章专题
        # 这里的/a只有一条斜杠却把所有文字提取出来了，猜测/a应该就是路径下所有a元素的意思
        subjects = '，'.join(response.xpath('//div[@class="include-collection"]/a/div/text()').extract())

        item = JianshuItem(
            title=title,
            avatar=avatar,
            author=author,
            publish_time=publish_time,
            wordage=wordage,
            likes_count=likes_count,
            article_id=article_id,
            article_url=article_url,
            show_content=show_content,
            subjects=subjects,
        )

        yield item


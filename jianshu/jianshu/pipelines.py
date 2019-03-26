# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymssql
from twisted.enterprise import adbapi
from pymssql import Cursor

"""
因为是第一次使用python在SQL存储数据，因此在这之前要先做一点环境配置：
1.开启SQL Server身份验证（即账号密码）（之前用Managment和Visual Studio都不用，直接windows身份验证直连，但这里貌似不行）
1.1具体的做法可以参考网上的教程，这里我设置的账号为sa，密码为123456

2.接下来就是按格式写好sql插入语句了，这里SQL Server和MySql的区别在于：
2.1SQL Server的主机名（server/host）是这个“.\SQLSERVER2017”,MySql应该是localhost或者其它。server不对就容易导致scrapy连接超时出错，或者产生各种问题***
2.SQL Server在identity上不用插入（null也不需要），而MySql插入时在identity语句上要设为null

3.在这里端口号和charset貌似也不需要

4.String or binary data would be truncated表示存储规格太小，需增大
"""

"""
数据库传统写入流程：
1.设置连接参数
2.创建连接对象
3.创建执行游标
4.设置sql语句
5.执行sql语句
6.提交
"""

# 数据库写入（当前用的Pipeline）
class JianshuPipeline(object):
    def __init__(self):
        # 进行connect时要传入的参数
        dbparams = {
            # 传参发现端口charset等都不用传，并且账号密码貌似也不用（不传的默认本机身份验证），和pymysql的有区别
            'server': '.\SQLSERVER2017',
            'user': 'sa',
            'password': '123456',
            'database': 'jianshu',
        }
        # 创建连接对象
        # 前面带**表示关键字形式传入，例如等价于user='sa'
        self.conn = pymssql.connect(**dbparams)

        # 创建执行游标
        self.cursor = self.conn.cursor()

        # 声明sql语句
        self._sql = None

    def process_item(self, item, spider):
        # 执行插入语句
        # 前面的参数是sql语句。后面的参数是一个元组，指定要插入的数据
        self.cursor.execute(self.sql, (item['title'], item['avatar'], item['author'], item['publish_time'], item['wordage'], item['likes_count'], item['article_id'], item['article_url'], item['show_content'], item['subjects']))

        # 提交(没有提交则会回滚)
        self.conn.commit()
        return item

    # @property：装饰器，方法变属性调用（但是这里的意义好像不大）
    @property
    def sql(self):
        # 如果没有相应的sql语句则创建返回，否则直接返回
        if not self._sql:
            # 正确书写sql语句，主键id不用插入。values全部用%s代替
            self._sql = """
            insert into article(title, avatar, author, publish_time, wordage, likes_count, article_id, article_url, show_content, subjects) values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            return self._sql

        return self._sql




# 数据库异步写入(但是发现设计失败，pymssql的cursor和pymysql的传入设计不一样。如果能找到pymssql在异步下的cursor设计方法应该还是可以的)
# 好消息是，pymssql和SQL Server的配合好像还不错，而pymysql设计异步是因为MySql写入的速度跟不上爬取的速度
# 后来发现pymssql好像本身就是异步！！
class JianshuTwistedPipeline(object):
    def __init__(self):
        dbparams = {
            'server': '.\SQLSERVER2017',
            'user': 'sa',
            'password': '123456',
            'database': 'jianshu',
            # 'cursorclass': Cursor
        }
        self.dbpool = adbapi.ConnectionPool('pymssql', **dbparams)

        self._sql = None

    def process_item(self, item, spider):
        defer = self.dbpool.runInteraction(self.insert_item, item)
        defer.addErrback(self.handle_error, item, spider)

    def insert_item(self, Cursor, item):
        Cursor.excute(self.sql, (item['title'], item['avatar'], item['author'], item['publish_time'], item['wordage'], item['likes_count'], item['article_id'], item['article_url'], item['show_content'], item['subjects']))

    def handle_error(self, error, item, spider):
        print('='*10+'error'+'='*10)
        print(error)
        print('='*10+'error'+'='*10)

    @property
    def sql(self):
        # 如果没有相应的sql语句则创建返回，否则直接返回
        if not self._sql:
            # 正确书写sql语句，主键id不用插入。values全部用%s代替
            self._sql = """
            insert into article(title, avatar, author, publish_time, wordage, likes_count, article_id, article_url, show_content, subjects) values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            return self._sql

        return self._sql
# 笔趣看小说网爬虫
import os
import sys
import re

import requests
from bs4 import BeautifulSoup


class downloader(object):
    def __init__(self):
        self.server = 'https://www.biqukan.co/'
        self.target = 'https://www.biqukan.co/book/'
        self.id = '112856/'
        self.bookName = ''
        self.names = []  # 存放章节名
        self.urls = []  # 存放章节链接
        self.pageUrls = []  # 章节页数链接
        self.pageNum = 0  # 章节目录页数
        self.nums = 1   # 章节数
        # 通过定义请求头，把程序伪装成浏览器
        self.cookies = {
            'Hm_lvt_feb1ff39117c29e8b956edcbc9750dc6': '1708006801',
            '__e_inc': '1',
            'clickbids': '45604',
            'Hm_lpvt_feb1ff39117c29e8b956edcbc9750dc6': '1708048919',
            'jieqiVisitId': 'article_articleviews%3D45604',
        }

        self.headers = {
            'authority': 'www.biqukan.co',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9',
            # 'cookie': 'Hm_lvt_feb1ff39117c29e8b956edcbc9750dc6=1708006801;
            #               __e_inc=1; clickbids=45604; Hm_lpvt_feb1ff39117c29e8b956edcbc9750dc6=1708048919;
            #               jieqiVisitId=article_articleviews%3D45604',
            'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        }
    # 获取章节所有目录页链接
    def get_allpage(self):
        # 将第一页链接存放进数组
        url = self.target + self.id
        self.pageUrls.append(url)
        req = requests.get(url=url, headers=self.headers, cookies=self.cookies)
        html = req.text
        div_bf = BeautifulSoup(html, 'html.parser')

        # 获取书名
        title = div_bf.find_all('h1', class_='bookTitle')
        # 获取<h1>标签下的所有子节点
        children = title[0].contents
        # 筛选出文本节点并拼接文本内容
        title_text = ''.join([str(child) for child in children if isinstance(child, str)])
            # strip()删除字符串两端空格
        self.bookName = title_text.strip()

        # 获取下一页的链接
        next_page = div_bf.find_all('a', class_='btn btn-default')
        if len(next_page) > 1:
            next_page_link = next_page[1].get('href')
            # 将章节目录下一页链接添加到数组
            while next_page_link != 'javascript:':
                self.pageNum += 1
                self.pageUrls.append(self.server + next_page_link)
                # 跳转到下一页链接
                res = requests.get(url=self.pageUrls[self.pageNum], headers=self.headers, cookies=self.cookies)
                html = res.text
                div_bf = BeautifulSoup(html, 'html.parser')
                # 获取下一页的链接
                next_page = div_bf.find_all('a', class_='btn btn-default')
                if len(next_page) > 1:
                    next_page_link = next_page[1].get('href')
                else:
                    break

    # 获取单本书的下载链接(只包含一页的章节)
    def get_download_url(self):
        for url in self.pageUrls:
            req = requests.get(url=url, headers=self.headers, cookies=self.cookies)
            html = req.text
            div_bf = BeautifulSoup(html, 'html.parser')
            div = div_bf.find_all('dl', class_='panel-body panel-chapterlist')
            if div:
                a_bf = BeautifulSoup(str(div[0]), 'html.parser')
                a = a_bf.find_all('a')
            # 存放章节链接
            self.nums = self.nums + len(a)
            for each in a:
                self.names.append(each.string)
                self.urls.append(self.target + self.id + each.get('href'))

    # 获取章节内容
    def get_content(self, target):

        res = requests.get(url=target, headers=self.headers, cookies=self.cookies)
        html = res.text
        bf = BeautifulSoup(html, 'html.parser')
        texts = bf.find_all('div', class_='panel-body')
        # 判断是否有第二页
        next = bf.find_all('a', class_='btn btn-default', id='linkNext')
        next_text = next[0].get_text()
        next_link = next[0].get('href')

        while next_text == '下一页':
            res = requests.get(url=self.target + self.id + next_link, headers=self.headers, cookies=self.cookies)
            html = res.text
            bf = BeautifulSoup(html, 'html.parser')
            add_texts = bf.find_all('div', class_='panel-body')
            if not add_texts:
                return "No additional content found."
            # 将新内容直接添加到texts列表中
            texts += add_texts
            # 更新下一页链接和文本内容
            next = bf.find_all('a', class_='btn btn-default', id='linkNext')
            next_text = next[0].get_text()
            next_link = next[0].get('href')
        # 将texts中所有Tag对象的文本内容合并成一个字符串
        merged_text = ''.join(text.text for text in texts)
        # 处理脏数据
        clean_text = re.sub(r'\s+', '\n\n', merged_text)
        clean_text = clean_text.replace('\n\n', '', 5)
        clean_text = clean_text.replace('www.biqukan.co，最快更新' + self.bookName + '最新章节！', '')
        clean_text = clean_text.replace('笔趣看', '')
        clean_text = clean_text.replace('请安装我们的客户端更新超快的免费小说APP下载APP终身免费阅读添加到主屏幕请点击，然后点击“添加到主屏幕”', '')
        clean_text = clean_text.replace('\n\n-->>本章未完，点击下一页继续阅读\n\n\n\n', '')
        return clean_text

    # 将爬取的内容写入文件
    def writer(self, name, path, text):
        write_flag = True
        with open(path, 'a', encoding='utf-8') as f:
            f.write(name + '\n')
            f.writelines(text)
            f.write('\n\n')


if __name__ == "__main__":
    dl = downloader()
    dl.get_allpage()
    dl.get_download_url()
    print('《' + dl.bookName + '》' + '开始下载:')
    for i in range(dl.nums):
        if i < len(dl.names) and i < len(dl.urls):
            dl.writer(dl.names[i], dl.bookName + '.txt', dl.get_content(dl.urls[i]))
        sys.stdout.write("已下载:%.3f%%" % float(i/dl.nums) + '\r')
        sys.stdout.flush()
    print('《' + dl.bookName + '》' + '下载完成')


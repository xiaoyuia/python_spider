import concurrent.futures
import mysql.connector
import requests
from bs4 import BeautifulSoup
import re

# 伪装成浏览器访问
cookies = {
    'Hm_lvt_feb1ff39117c29e8b956edcbc9750dc6': '1708006801',
    '__e_inc': '1',
    'clickbids': '45604',
    'Hm_lpvt_feb1ff39117c29e8b956edcbc9750dc6': '1708048919',
    'jieqiVisitId': 'article_articleviews%3D45604',
}
headers = {
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

# 填入你的数据库信息
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="novel"
)

# 创建一个MySQL连接池
connection_pool = mysql.connector.pooling.MySQLConnectionPool(pool_name="mypool",
                                                              pool_size=32,
                                                              host="localhost",
                                                              user="root",
                                                              password="root",
                                                              database="novel")

# 网站小说分类网址
novel_all_urls = [
    'https://www.biqukan.co/fenlei1/1.html',
    'https://www.biqukan.co/fenlei2/1.html',
    'https://www.biqukan.co/fenlei3/1.html',
    'https://www.biqukan.co/fenlei4/1.html',
    'https://www.biqukan.co/fenlei5/1.html',
    'https://www.biqukan.co/fenlei6/1.html',
]

# 小说id
ids = []


# 获取一个数据库连接
def get_connection():
    return connection_pool.get_connection()


# 获取网站上所有的小说id，更新数据库
def get_novel_id(novel_url):
    response = requests.get(novel_url, headers=headers, cookies=cookies)
    soup = BeautifulSoup(response.text, 'html.parser')
    all_tr = soup.find_all('tr')
    for tr in all_tr[1:]:
        # 获取基本信息
        genre = tr.find_all('td')[0]
        name = tr.find_all('td')[1]
        a_tag = name.find('a')
        novel_url = a_tag.get('href')
        novel_id = novel_url.split('/')[-2]
        author = tr.find_all('td')[3]
        # 检查小说是否存在
        if not novel_exists(novel_id):
            # 更新数据库
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    # 更新novel表
                    sql = "INSERT INTO novel (novel_id, name, author, genre, novel_url) values (%s, %s, %s, %s, %s)"
                    val = (novel_id, name.text, author.text, genre.text, novel_url)
                    cursor.execute(sql, val)
                connection.commit()
    # 找到下一页标签
    next = soup.find('a', class_='next')
    # 当存在下一页，则一直循环
    if next:
        next_url = next.get('href')
        print(next_url)
        get_novel_id(next_url)
    else:
        print(next)


# 检查小说是否存在
def novel_exists(novel_id):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            sql = "SELECT novel_id FROM novel WHERE novel_id = %s"
            val = (novel_id,)
            cursor.execute(sql, val)
            result = cursor.fetchone()
            if result is not None:
                return result[0]
            return False


# 未完本则更新数据库
def inCompeleteOrCompelete(novel_id):
    # 建立数据库连接
    with get_connection() as connection:
        with connection.cursor() as cursor:
            response = requests.get('https://biqukan.co/book/' + novel_id, cookies=cookies, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            p = soup.find('p', class_='booktag')
            span = p.find_all('span')
            span_text = span[1].text
            # 若连载中则更新novel表中的status字段为Incomplete
            if span_text == '连载中':
                sql = "UPDATE novel SET status = 'Incomplete' WHERE novel_id = %s"
                val = (novel_id,)
                cursor.execute(sql, val)
                connection.commit()
                print(novel_id)

# 将爬取的内容写入文件
def writer(name, path, text):
    write_flag = True
    with open(path, 'a', encoding='utf-8') as f:
        f.write(name + '\n')
        f.writelines(text)
        f.write('\n\n')


# 获取章节内容并下载
def get_content(novel_id, novel_name, latest_chapter_number, genre, latest_chapter_name):
    response = requests.get('https://biqukan.co/book/' + novel_id, cookies=cookies, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    div = soup.find_all('dl', class_='panel-body panel-chapterlist')
    a_bf = BeautifulSoup(str(div[0]), 'html.parser')
    a = a_bf.find_all('a')
    chapter_names = []
    chapter_urls = []
    # novel_id 第一页章节的时候为 一串数字,当第二页章节时 novel_id 为 ${novel_id}/index_2.html //需加判断
    if '/' in novel_id:
        novel_id = novel_id.split('/')[0]
    for each in a:
        latest_chapter_number = latest_chapter_number + 1
        latest_chapter_name = each.string
        chapter_names.append(each.string)
        chapter_urls.append('https://www.biqukan.co/book/' + novel_id + '/' + each.get('href'))
    i = 0
    # 遍历当前页所有章节
    for url in chapter_urls:
        response = requests.get(url, cookies=cookies, headers=headers)
        bf = BeautifulSoup(response.text, 'html.parser')
        texts = bf.find_all('div', class_='panel-body')

        # 判断是否有第二页
        next = bf.find_all('a', class_='btn btn-default', id='linkNext')
        next_text = next[0].get_text()
        next_link = next[0].get('href')

        while next_text == '下一页':
            res = requests.get(url='https://www.biqukan.co/book/' + novel_id + '/' + next_link, headers=headers, cookies=cookies)
            bf = BeautifulSoup(res.text, 'html.parser')
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
        clean_text = clean_text.replace('www.biqukan.co，最快更新' + novel_name + '最新章节！', '')
        clean_text = clean_text.replace('笔趣看', '')
        clean_text = clean_text.replace(
            '请安装我们的客户端更新超快的免费小说APP下载APP终身免费阅读添加到主屏幕请点击，然后点击“添加到主屏幕”', '')
        clean_text = clean_text.replace('(看小说到.23us.)16977小游戏每天更新好玩的小游戏，等你来发现！', '')
        clean_text = clean_text.replace('\n\n-->>本章未完，点击下一页继续阅读\n\n\n\n', '')

        if i < len(chapter_names):
            chapter_name = chapter_names[i]
            if chapter_name:
                writer(chapter_name, "E:\\Novels\\" + genre + '\\' + novel_name + '.txt', clean_text)
        i = i+1
    # 若章节存在下一页，递归
    page_next = soup.find_all('a', class_='btn btn-default')
    if page_next:
        page_next_text = page_next[1].get_text()
        page_next_link = page_next[1].get('href')
        if page_next_link != 'javascript:' and page_next_text == '下一页':
            page_next_link = page_next_link.split('/book/')[1]
            get_content(page_next_link, novel_name, latest_chapter_number, genre, latest_chapter_name)

    # 更新数据库中 latest_chapter_number 和 latest_chapter_name
    with get_connection() as connection:
        with connection.cursor() as cursor:
            sql = "UPDATE novel SET latest_chapter_number = %s, latest_chapter_name = %s WHERE novel_id = %s"
            val = (latest_chapter_number, latest_chapter_name, novel_id)
            cursor.execute(sql, val)
            connection.commit()


# 线程爬取小说基本信息
def crawl_novel_id(novel_all_url):
    get_novel_id(novel_all_url)


# 更新novel_path
def update_novel_path(novel_id, path):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            sql = "UPDATE novel SET novel_path = %s WHERE novel_id = %s"
            val = (path, novel_id)
            cursor.execute(sql, val)
            connection.commit()


# 线程下载小说
def crawl_download(novel_id):
    novel_path = ''
    with get_connection() as connection:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM novel WHERE novel_id = %s"
            val = (novel_id,)
            cursor.execute(sql, val)
            result = cursor.fetchone()
            novel_name = result[1]
            genre = result[3]
            novel_path = result[5]
            latest_chapter_number = result[6]
            latest_chapter_name = result[7]
            # 更新novel_path
            if not novel_path:
                novel_path = "E:\\Novels\\" + genre + '\\' + novel_name + '.txt'
                update_novel_path(novel_id, novel_path)
    print('《' + novel_name + '》' + '开始下载')
    get_content(novel_id, novel_name, latest_chapter_number, genre, latest_chapter_name)
    print('《' + novel_name + '》' + '下载完成')


if __name__ == '__main__':
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT novel_id FROM novel")
            ids = [row[0] for row in cursor.fetchall()]

    # 利用线程爬取分类里的所有小说id，更新数据库
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # 完善数据库所有小说id
        # executor.map(crawl_novel_id, novel_all_urls)
        # 判断完本状态
        # executor.map(inCompeleteOrCompelete, ids)
        # 下载所有小说
        executor.map(crawl_download, ids)
    executor.shutdown(wait=True)

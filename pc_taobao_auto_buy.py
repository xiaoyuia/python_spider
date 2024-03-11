# 淘宝购物车定时购买
import datetime

# 时间包 控制程序的休眠时间
import time

from selenium import webdriver
from selenium.webdriver.common.by import By


def login():
    # 打开淘宝首页，并扫码登录
    browser.get('https://www.taobao.com')
    # 登录账号(扫码)
    if browser.find_element(By.LINK_TEXT,'亲，请登录'):
        login_link = browser.find_element(By.LINK_TEXT, '亲，请登录')
        login_link.click()
        # 20s内扫码登录
        time.sleep(20)

    # 打印登录时间
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    print("登录时间:", now)
    # 点击购物车链接
    browser.get('https://cart.taobao.com/cart.htm')
    # cart_link = browser.find_element(By.XPATH, '//*[@id="J_MiniCart"]/div[1]/a')
    # cart_link.click()
    # 等待购物车页面加载完成
    time.sleep(5)


def order(times):
    while True:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        # 时间对比
        if now >= times:
            while True:
                try:
                    if browser.find_element(By.XPATH, '//*[@id="J_SelectAll1"]'):
                        browser.find_element(By.XPATH, '//*[@id="J_SelectAll1"]').click()
                        break
                except:
                    print('未找到全选按钮')
            # 结算
            while True:
                try:
                    if browser.find_element(By.LINK_TEXT, '结 算'):
                        time.sleep(0.5)
                        browser.find_element(By.LINK_TEXT, '结 算').click()
                        print('结算成功')
                        break
                except:
                    pass
            # 提交订单
            while True:
                try:
                    if browser.find_element(By.XPATH, '//*[@id="submitOrderPC_1"]/div[1]/a[2]'):
                        browser.find_element(By.XPATH, '//*[@id="submitOrderPC_1"]/div[1]/a[2]').click()
                        order_time = time.strftime("%Y-%m-%d %H:%M:%S.%f")
                        print('提交成功，时间为：', order_time)
                        return
                except:
                    print('再次尝试提交订单')
                time.sleep(0.01)


if __name__ == '__main__':
    # 使用ChromeOptions来设置chromedriver的路径
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(r"executable_path=E:\python\WebScraping\WebDriver\chromedriver.exe")
    # 禁用图片加载,提升加载速度
    # chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    # 创建webdriver时传入chrome_options参数
    browser = webdriver.Chrome(options=chrome_options)
    times = input('请输入抢购时间，格式：2024-02-20 12:20:00.000000：')
    login()
    order(times)



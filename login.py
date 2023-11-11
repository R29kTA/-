import re
import threading
import urllib.parse
from hashlib import md5

import requests
from bs4 import BeautifulSoup
from retrying import retry

lock = threading.Lock()


@retry()
def get_cookie():
    __url = "http://jwc.scnucas.com/"
    __headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache'
    }
    print("get_cookie")
    __response = requests.get(__url, headers=__headers)
    if __response.status_code == 200:
        return __response.headers['Set-Cookie']
    print("[get_cookie]网络异常")
    raise Exception("[get_cookie]网络异常")


@retry()
def get_validata(cookie):
    __url = "http://jwc.scnucas.com/_data/login_home_jd.aspx"
    __headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Referer': 'http://jwc.scnucas.com/',
        'Cookie': f'myCookie=; ASP.NET_SessionId={cookie}',
        'Upgrade-Insecure-Requests': '1',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache'
    }
    print("get_validata...")
    __response = requests.get(__url, headers=__headers)
    if __response.status_code == 200:
        return __response.text
    print("[get_validata]网络异常")
    raise Exception("[get_validata]网络异常")


def parse_cookie(cookie: str):
    _cookie_pattern = r'ASP.NET_SessionId=(\w+);'
    _match = re.search(_cookie_pattern, cookie)
    if _match:
        return _match.group(1)


def get_payload(html: str, username: str, password: str):
    __soup = BeautifulSoup(html, 'html.parser')
    __VIEWSTATE = __soup.find('input', attrs={'name': '__VIEWSTATE'})['value']
    __VIEWSTATEGENERATOR = __soup.find('input', attrs={'name': '__VIEWSTATEGENERATOR'})['value']
    __EVENTVALIDATION = __soup.find('input', attrs={'name': '__EVENTVALIDATION'})['value']
    __dsdsdsdsdxcxdfgfg = md5((username + md5(password.encode()).hexdigest()[:30].upper() + '13671')
                              .encode()).hexdigest()[:30].upper()
    __params = {
        "__VIEWSTATE": __VIEWSTATE,
        "__VIEWSTATEGENERATOR": __VIEWSTATEGENERATOR,
        "__EVENTVALIDATION": __EVENTVALIDATION,
        "pcInfo": "Mozilla/5.0+(X11;+Linux+x86_64;+rv:109.0)+Gecko/20100101+Firefox/118.0Linux+x86_645.0+(X11)+SN:NULL",
        "txt_mm_expression": "",
        "txt_mm_length": "",
        "txt_mm_userzh": "",
        "typeName": "学生",
        "dsdsdsdsdxcxdfgfg": __dsdsdsdsdxcxdfgfg,
        "fgfggfdgtyuuyyuuckjg": "",
        "validcodestate": 0,
        "Sel_Type": "STU",
        "txt_asmcdefsddsd": username,
        "txt_pewerwedsdfsdff": password
    }
    return __params


@retry()
def get_login(payload: dict, cookie: str):
    __url = "http://jwc.scnucas.com/_data/login_home_jd.aspx"
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'http://jwc.scnucas.com',
        'Connection': 'keep-alive',
        'Referer': 'http://jwc.scnucas.com/_data/login_home_jd.aspx',
        'Cookie': f'myCookie=; ASP.NET_SessionId={cookie}',
        'Upgrade-Insecure-Requests': '1',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache'
    }
    __payload = urllib.parse.urlencode(payload, encoding='gb2312')
    print(f"{payload['txt_asmcdefsddsd']}正在登录...")
    __response = requests.post(__url, headers=headers, data=__payload)
    if __response.status_code == 200:
        if "正在加载，请稍候..." in __response.text:
            print(f"{payload['txt_asmcdefsddsd']}登录成功...,有效sessionId=[{cookie}]")
            return cookie
        else:
            print(f"{payload['txt_asmcdefsddsd']}帐号或者密码错误")
            return
    print("get_login网络异常")
    print(__response.text)
    raise Exception("[get_login]网络异常")


def handle_login(username: str, password: str, target: str):
    __t = get_cookie()
    __cookie = parse_cookie(__t)
    __html = get_validata(__cookie)
    __payload = get_payload(__html, username, password)
    __sessionId = get_login(__payload, __cookie)
    with lock:
        with open("cookies.txt", mode="a+", encoding="utf-8") as __f:
            __f.write(f"{username},{__sessionId},{target}\n")


if __name__ == '__main__':
    threads = []
    with open(file="acc.txt", mode="r", encoding="utf-8") as f:
        line = f.readline().strip()
        while line:
            acc = line.split(",")
            thread = threading.Thread(target=handle_login, args=(acc[0].strip(), acc[1].strip(), acc[2].strip()))
            thread.start()
            threads.append(thread)
            line = f.readline()
    for thread in threads:
        thread.join()
    print("所有帐号登录操作执行完毕")

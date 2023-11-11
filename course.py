import os.path
import threading
import urllib.parse

import requests
from bs4 import BeautifulSoup
from retrying import retry

lock = threading.Lock()


@retry()
def get_course(cookie: str):
    print("get_course")
    __payload = 'sel_lx=2'
    __url = "http://jwc.scnucas.com/wsxk/stu_xsyx_rpt.aspx"
    __headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'http://jwc.scnucas.com',
        'Connection': 'keep-alive',
        'Referer': 'http://jwc.scnucas.com/wsxk/stu_xsyx.aspx',
        'Cookie': f'myCookie=; ASP.NET_SessionId={cookie}',
        'Upgrade-Insecure-Requests': '1',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache'
    }
    __response = requests.post(__url, headers=__headers, data=__payload)
    __text = __response.text
    if "您无权访问此页" in __text:
        print("需要重新登录")
        return ""
    if __response.status_code == 200 and "503" not in __text:
        print("获取课程页面成功")
        return __text
    print(__text)
    raise Exception("[select_course]网络异常")


def find_course_id(html: str, target: str):
    __soup = BeautifulSoup(html, 'html.parser')
    __inp = __soup.find_all("input", {"type": "checkbox"})
    print(f"正在查找目标为[{target}]的课程ID")
    for i in __inp:
        if target in i["value"]:
            __id = f"TTT,{i['value']}$1"
            print(f"构造课程ID[{__id}]的payload")
            return {"id": __id}
    print(f"没有找到关于[{target}]的课程")


@retry()
def select_course(cookie: str, payload: dict, username: str):
    print("select course\n")
    __url = "http://jwc.scnucas.com/wsxk/stu_xsyx_rpt.aspx?func=1"
    __headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'http://jwc.scnucas.com',
        'Connection': 'keep-alive',
        'Referer': 'http://jwc.scnucas.com/wsxk/stu_xsyx_rpt.aspx',
        'Cookie': f'myCookie=; ASP.NET_SessionId={cookie}; myCookie=',
        'Upgrade-Insecure-Requests': '1',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache'
    }
    __payload = urllib.parse.urlencode(payload, encoding='gb2312')
    __response = requests.post(__url, headers=__headers, data=__payload)
    __text = __response.text
    if __response.status_code == 200 and "预选成功" in __text:
        with lock:
            with open("result.txt", mode="a+", encoding="utf-8") as __f:
                __f.write(f"[{username}]预选成功[{payload['id']}]\n")
        print(f"[{username}]预选成功[{payload['id']}]")
    else:
        if "您无权访问此页" in __text:
            print(f"[{username}]需要重新登录")
            return ""
        if "预选失败" in __text:
            print(f"[{username}]预选失败，可能是课程人数已满")
            return ""
        if "系统出错" in __text:
            print(f"[{username}]系统出错")
            return ""
    print(__text)
    raise Exception("网络异常")


def handle_course(username: str, cookie: str, target: str, html: str):
    __id = find_course_id(html, target)
    select_course(cookie=cookie, payload=__id, username=username)


if __name__ == '__main__':
    threads = []
    with open("cookies.txt", mode="r", encoding="utf-8") as f:
        line = f.readline().strip()
        li = line.split(",")
        ht = ""
        if os.path.exists("course.html"):
            with open("course.html", mode="r", encoding="utf-8") as c_f:
                ht = c_f.read()
                print("检测到课程页面具有缓存，使用缓存中")
        else:
            ht = get_course(li[1])
            with open("course.html", mode="w+", encoding="utf-8") as c_f:
                c_f.write(ht)
        if len(ht) < 10:
            print("没有获取到课程页面")
            exit()
        while len(line) > 5:
            thread = threading.Thread(target=handle_course, args=(li[0].strip(), li[1].strip(), li[2].strip(), ht))
            thread.start()
            threads.append(thread)
            line = f.readline()
        for thread in threads:
            thread.join()
    print("所有帐号课程预选完毕.")

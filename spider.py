# -*- coding:utf-8 -*-
import requests
from urllib import urlencode
from bs4 import BeautifulSoup
import json
import pymongo
from config import *

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

def get_first_page(baseurl,header,page):#分析动态加载后得到的json格式页面
    print '正在打开' + str(page) + '页网站'
    datas = {
        'page':page,
        'page_size':20,
        'version':0,
        'is_finish':0,
        'start_year':2017,
        'tag_id':'',
        'index_type':1,
        'index_sort':0,
        'quarter':0
    }
    data = urlencode(datas)
    url = baseurl + data
    try:
        r = requests.get(url,headers = header)
        r.raise_for_status()
        r.encoding = 'utf-8'
        response = r.text
        html = json.loads(response)
        return html
    except Exception,e:
        print '打开网页失败',url

def get_url(html):#从json页面中提取每一个番剧的url
    urllist = []
    urls = html['result']['list']
    for i in urls:
        url = i['url']
        urllist.append(url)
    return urllist

def get_each_page(url,header):#获取每一个番剧的页面
    print '正在打开网页:',url
    try:
        r = requests.get(url, headers=header)
        r.raise_for_status()
        r.encoding = 'utf-8'
        response = r.text
        return response
    except Exception, e:
        print '打开网页失败', url

def get_info(response):#从番剧页面中提取信息
    print '正在获取数据...'
    a = []
    soup = BeautifulSoup(response,"html.parser")
    title = soup.title.string.split('_')[0]  # 获取番剧名字
    plays = soup.find('span', class_="info-count-item-play")  # 获取播放总数
    play = plays.em.string
    fans = soup.find('span', class_="info-count-item-fans").em.string  # 获取追番人数
    review = soup.find('span', class_="info-count-item-review").em.string  # 获取弹幕总数
    desc = soup.find('div', class_='info-desc').string  # 获取番剧介绍
    infos = soup.find('div', class_="info-update")  # 获取时间以及集数
    for data in infos.em.strings:
        infos = data.strip().split('\n')[0]
        a.append(infos)
    date = a[1]  # 获取开播时间
    episodes = a[3]  # 获取集数
    return{
        '标题':title,
        '播放总量':play,
        '追番人数':fans,
        '弹幕总数':review,
        '番剧介绍':desc,
        '开播时间':date,
        '集数':episodes
    }


def save_to_mongo(result):#储存到mongoDB数据库
    print '正在储存数据...'
    if db[MONGO_TABLE].insert(result):
        print '储存成功'
        return True
    else:
        return False


def run():
    baseurl = 'https://bangumi.bilibili.com/web_api/season/index_global?'
    header = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64)'}
    page = 1
    total = 9
    while page <= total:
        html = get_first_page(baseurl, header, page)
        urllist = get_url(html)
        for url in urllist:
            response = get_each_page(url,header)
            result = get_info(response)
            save_to_mongo(result)
        page += 1


run()




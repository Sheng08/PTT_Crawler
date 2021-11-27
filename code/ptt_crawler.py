# -*- coding: utf-8 -*-
import requests
import bs4
import re
from datetime import datetime, timezone, timedelta
import csv


def get_PTTweb_page(url):
    resp = requests.get(url=url, cookies={'over18': '1'})  # ptt18歲的認證
    if resp.status_code != 200:  # 回傳200代表正常
        print('Invalid url:', resp.url)
        return None
    else:
        return resp.text

# 前幾名最多樓的文章


def push_right(i, l, r):
    global top_list
    if r == i:
        return
    top_list[r] = top_list[l].copy()
    push_right(i, l-1, r-1)


def find_top(one_article, top):
    global top_list
    for i in range(top):
        if top_list[i].get('push') < one_article['push']:  # 用get 能避免沒有key時 不會都出錯誤
            push_right(i, top-2, top-1)
            top_list[i] = one_article
            break


# timestamp 取得現在時間、指定時區
tz = timezone(timedelta(hours=+8))  # 設定為 +8 時區
dt = datetime.now(tz).replace(microsecond=0)


# 主爬蟲程式
top = 3
article_date = ''
stop = False
first_crawl = True
article_count = 0
page_count = 0

PTT_ROOT_URL = 'https://www.ptt.cc'
payload = {
    'timestamp': '',
    'push': 0,
    'author': '',
    'title': '',
    'href': '',
    'date': '',
    'ip': '',
    'contents': ''
}
top_list = [{'push': 0}]*top
compile_ip = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")


# 主爬蟲程式
response = get_PTTweb_page('https://www.ptt.cc/bbs/Gossiping/index.html')
soup = bs4.BeautifulSoup(response, "html.parser")

# proccess time
start = datetime.now()

while(True):
    for article_div in soup.find_all('div', 'r-ent'):
        push_count = 0
        article = article_div.find('div', 'title')
        article_date = article_div.find('div', 'date').text

        # 判斷前一天
        if not(article_date == (dt-timedelta(days=1)).strftime("%m/%d")):
            if (article_date == (dt-timedelta(days=2)).strftime("%m/%d")) and not(first_crawl):
                stop = True
            continue

        try:
            response_in = get_PTTweb_page(PTT_ROOT_URL+article.a['href'])
            soup_in = bs4.BeautifulSoup(response_in, "html.parser")

            header = soup_in.find_all('span', 'article-meta-value')
            author = header[0].text
            title = header[2].text
            date = header[3].text

            main_container = soup_in.find(id='main-container')
            all_text = main_container.text
            ip = re.search(compile_ip, all_text, flags=0).group()

            pre_text = all_text.split('--')[0]
            texts = pre_text.split('\n')
            contents = texts[2:]
            content = '\n'.join(contents)

            # timestamp
            dt = datetime.now(tz).replace(microsecond=0)
            timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")

            # find push
            for push_tag in soup_in.find_all('span', 'push-tag'):
                # print(push_tag)
                if ('推' in push_tag.text) or ('噓' in push_tag.text) or ('→' in push_tag.text):
                    push_count += 1

            payload['timestamp'] = timestamp
            payload['push'] = push_count
            payload['author'] = author
            payload['title'] = title
            payload['href'] = PTT_ROOT_URL+article.a['href']
            payload['date'] = date
            payload['ip'] = ip
            payload['contents'] = content

            find_top(payload.copy(), top)
            article_count += 1

        except Exception as e:
            # print(e)
            # print('\033[93m' + article.text.strip() + '\033[0m')
            pass

    first_crawl = False
    if stop:
        break

    # 換頁處理
    for link in soup.find_all('a', 'btn wide'):  # 用來抓取上一頁
        if link.text == '‹ 上頁':
            response = get_PTTweb_page(PTT_ROOT_URL+link['href'])
            soup = bs4.BeautifulSoup(response, "html.parser")
            break
    page_count += 1

end = datetime.now()

datetime_dt = datetime.today()  # 獲得當地時間
dt = datetime_dt.date()  # 最小日期顯示到日
new_date = dt - timedelta(days=1)

print("批踢踢實業坊›看板 Gossiping 爬蟲結果")
print("文章日期：{}年 {}月 {}日".format(new_date.year, new_date.month, new_date.day))
print("文章數：", article_count, "篇")
print("完成時間：", datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
print("執行時間：", end - start)
print('Done...')
print('**************************Result**************************')


# 寫入csv
try:
    # with open('result.csv', 'r+', newline='') as csvfile:
    #     reader = csv.reader(csvfile)
    with open('result.csv', 'a+', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for i in range(top):
            writer.writerow([top_list[i]['timestamp'], top_list[i]['author'], top_list[i]
                             ['title'], top_list[i]['push'], top_list[i]['date'], top_list[i]['ip'], top_list[i]['contents']])
except:
    with open('result.csv', 'w+', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Timestamp', 'Author', 'Title', 'Push',
                         'Date', 'IP_address', 'Contents'])

        for i in range(top):
            writer.writerow([top_list[i]['timestamp'], top_list[i]['author'], top_list[i]
                             ['title'], top_list[i]['push'], top_list[i]['date'], top_list[i]['ip'], top_list[i]['contents']])

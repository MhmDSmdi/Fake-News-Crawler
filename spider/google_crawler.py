import time
import random
import googlesearch as google
import pymongo
from bs4 import BeautifulSoup
from googleapiclient.discovery import build

GOOGLE_AUTH_INFO = [
    ('AIzaSyADBZ1y8fjLgUOz-2uBF2fP7jV9W4Lr5UI', '005477725399851830003:akasmjjjr2j'),
    ('AIzaSyCmJ8jc075yOPstAWMV-nCxG6hvLy2DnjA', '005477725399851830003:zptxhoavf0v'),
    ('AIzaSyAO7vLvuTQFCeTF8dIKr0zsNUw36bs7Iqk', '005477725399851830003:9dqgdbh4q1c')
]


def _google_api(query, api_key, cse_id, **kwargs):
    query_service = build("customsearch", "v1", developerKey=api_key)
    query_results = query_service.cse().list(q=query, cx=cse_id, **kwargs).execute()
    return query_results


def mine_links_api(query, **kwargs):
    api_key, cse_id = random.choice(GOOGLE_AUTH_INFO)
    return _google_api(query, api_key, cse_id, **kwargs)


def mine_google_links(query, tld='com', lang='fa', tbs='0', safe='off', num=10, start=0,
                        stop=None, domains=None, pause=2.0, tpe='', country='',
                        extra_params=None, user_agent=None):
    hashes = set()
    count = 0
    if domains:
        query = query + ' ' + ' OR '.join('site:' + domain for domain in domains)
    query = google.quote_plus(query)
    if not extra_params:
        extra_params = {}

    for builtin_param in google.url_parameters:
        if builtin_param in extra_params.keys():
            raise ValueError(
                'GET parameter "%s" is overlapping with \
                the built-in GET parameter',
                builtin_param
            )
    google.get_page(google.url_home % vars(), user_agent)
    if start:
        if num == 10:
            url = google.url_next_page % vars()
        else:
            url = google.url_next_page_num % vars()
    else:
        if num == 10:
            url = google.url_search % vars()
        else:
            url = google.url_search_num % vars()

    while not stop or count < stop:
        last_count = count
        for k, v in extra_params.items():
            k = google.quote_plus(k)
            v = google.quote_plus(v)
            url = url + ('&%s=%s' % (k, v))

        time.sleep(pause)
        html = google.get_page(url, user_agent)
        soup = BeautifulSoup(html, 'html.parser')
        news_item = soup.find_all('div', class_='ezO2md')
        for item in news_item:
            snippet = ''
            title = ''
            try:
                a = item.find('a')
                link = a['href']
                title_span = a.find('span')
                if title_span:
                    title = title_span.text
                details = item.find('td').text.split('·')
                if len(details) < 2:
                    date = ''
                else:
                    date = details[0]
                    snippet = details[1]
            except Exception:
                continue
            link = google.filter_result(link)
            if not link:
                continue
            h = hash(link)
            if h in hashes:
                continue
            hashes.add(h)
            yield title, link, snippet, date
            count += 1
            if stop and count >= stop:
                return
        if last_count == count:
            break
        start += num
        if num == 10:
            url = google.url_next_page % vars()
        else:
            url = google.url_next_page_num % vars()
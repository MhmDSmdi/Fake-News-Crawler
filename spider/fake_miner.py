import random
import time
from datetime import datetime
from datetime import timedelta
import uuid
import pandas as pd
import googlesearch as google
import string
import pymongo
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from text_processor import cleaner
from spider.google_crawler import mine_google_links, mine_links_api

DENIAL_WORDS = ['تکذیب', 'کذب', 'شايعه']
EXCLUDE_TERM = 'شایعه صحت کذب تکذیب'
EXACT_TERM = 'تکذیب'
CRAWLER_QUERY_WORDS = r' "{}"+ تکذیب" خبر" '

FAKE_MINER_ACCEPT_QUERY = 200
FAKE_MINER_SKIP_QUERY = 400
FAKE_MINER_EDIT_QUERY = 600
FAKE_MINER_ACCEPT_RESULT = 100
FAKE_MINER_IGNORE_RESULT = 300


def query_builder(query, exact_terms=[], exclude_terms=[], site=None, remove_stopwrods=True, filter_words=[]):
    EXACT_HOLDER = r' "{}" '
    EXCLUDE_HOLDER = r' -{}'
    SITE_HOLDER = r' site:{}'
    stopwords = open('../text_processor/stopwords/news_stopwords.txt', 'r').read().split('\n')
    query = ' '.join(list(filter(lambda word: word not in filter_words + stopwords,
                                 query.translate(str.maketrans('', '', string.punctuation)).split())))
    for exact in exact_terms:
        query += EXACT_HOLDER.format(exact)
    for exclude in exclude_terms:
        query += EXCLUDE_HOLDER.format(exclude)
    if site:
        query += SITE_HOLDER.format(site)
    return query


def crawl_denied_news(start, end, context_word='', interval=10, date_format='%Y%m%d', use_api=False, callback=None):
    # Input = (start:date(string), end:date(string))
    # Output = DataFrame(id, title, link, snippet, date)
    start_date = datetime.strptime(start, date_format)
    denied_news = pd.DataFrame(columns=['d_id', 'd_title', 'd_link', 'd_snippet', 'd_date'])
    while start_date <= datetime.strptime(end, date_format):
        end_interval = start_date + timedelta(days=interval)
        print('From {}, Until {}'.format(start_date.strftime('%Y-%m-%d'), end_interval.strftime('%Y-%m-%d')))
        if use_api:
            sort = 'date:r:{}:{}'.format(start_date.strftime(date_format), end_interval.strftime(date_format))
            results = mine_links_api(CRAWLER_QUERY_WORDS.format(context_word), num=10, sort=sort, gl='ir',
                                     exactTerms=EXACT_TERM)
            if 'items' in results.keys():
                for res in results['items']:
                    item = {
                        'd_id': uuid.uuid1().hex,
                        'd_title': '-' if not res['title'] else res['title'],
                        'd_link': res['link'],
                        'd_snippet': '-' if not res['snippet'] else res['snippet'],
                        'd_date': (start_date + timedelta(days=interval / 2)).strftime('%Y%m%d') if not 'date' in
                                                                                                        res['pagemap'][
                                                                                                            'metatags'][
                                                                                                            0].keys() else ''.join(
                            res['pagemap']['metatags'][0]['date'].split('-'))[:8]
                    }
                    if callback:
                        callback(item)
                    denied_news = denied_news.append(item, ignore_index=True)
        else:
            results = mine_google_links(CRAWLER_QUERY_WORDS.format(context_word), num=30, stop=30,
                                        pause=random.randint(2, 8),
                                        tbs=google.get_tbs(start_date, end_interval + timedelta(days=interval)))
            for (title, link, snippet, date) in results:
                if any(dword in title for dword in DENIAL_WORDS):
                    title = ' '.join(title.split())
                    snippet = ' '.join(snippet.split())
                    if date != '':
                        date = ' '.join(date.split())
                        date = cleaner.date_persian2english(date, delimiter=' ', persian_month=True)
                    item = {
                        'd_id': uuid.uuid1().hex,
                        'd_title': '-' if not title else title,
                        'd_link': link,
                        'd_snippet': '-' if not snippet else snippet,
                        'd_date': date}
                    if callback:
                        callback(item)
                    denied_news = denied_news.append(item, ignore_index=True)
        start_date = end_interval + timedelta(hours=12)
    denied_news.to_excel("denied_news.xlsx", index_label=False, index=False)
    return denied_news


def crawl_rumor_candidate(denied_news: pd.DataFrame, use_api=False, f_interval=5, b_interval=5, date_format='%Y%m%d',
                          q_callback=None, r_callback=None):
    # Input = DataFrame (denied news)
    # Output = DataFrame (fake candidate)
    # callback should return the status code of the candidate query
    candidate_list = pd.DataFrame(columns=['d_id', 'f_title', 'f_link', 'f_snippet', 'f_date'])
    for news in denied_news.itertuples():
        date = datetime.strptime(str(news.d_date), date_format)
        print(date)
        if use_api:
            query = query_builder(news.d_title, filter_words=DENIAL_WORDS)
            if q_callback:
                action_code, edit_query = q_callback(query)
                assert (action_code and action_code in [FAKE_MINER_EDIT_QUERY, FAKE_MINER_SKIP_QUERY, FAKE_MINER_ACCEPT_QUERY]), 'Callback function must return proper ACTION_CODE'
                if action_code == FAKE_MINER_ACCEPT_QUERY:
                    pass
                elif action_code == FAKE_MINER_SKIP_QUERY:
                    continue
                elif action_code == FAKE_MINER_EDIT_QUERY:
                    query = edit_query
            results = mine_links_api(query, num=10, excludeTerms=EXCLUDE_TERM)
            for res in results['items']:
                item = {
                    'd_id': news.d_id,
                    'f_id': uuid.uuid1().hex,
                    'f_title': '-' if not res['title'] else res['title'],
                    'f_link': res['link'],
                    'f_snippet': '-' if not res['snippet'] else res['snippet'],
                    'f_date': '-' if not 'date' in res['pagemap']['metatags'][0].keys() else ''.join(
                        res['pagemap']['metatags'][0]['date'].split('-'))[:8]
                }
                if r_callback:
                    result_code = r_callback(item)
                    assert (result_code and result_code in [FAKE_MINER_IGNORE_RESULT, FAKE_MINER_ACCEPT_RESULT]), 'Callback function must return proper RESULT_CODE'
                    if result_code == FAKE_MINER_ACCEPT_RESULT:
                        pass
                    elif result_code == FAKE_MINER_IGNORE_RESULT:
                        continue
                candidate_list = candidate_list.append(item, ignore_index=True)
        else:
            query = query_builder(news.d_title, exclude_terms=DENIAL_WORDS, filter_words=DENIAL_WORDS)
            if q_callback:
                action_code, edit_query = q_callback(query)
                assert (action_code and action_code in [FAKE_MINER_EDIT_QUERY, FAKE_MINER_SKIP_QUERY, FAKE_MINER_ACCEPT_QUERY]), 'Callback function must return proper ACTION_CODE'
                if action_code == FAKE_MINER_ACCEPT_QUERY:
                    pass
                elif action_code == FAKE_MINER_SKIP_QUERY:
                    continue
                elif action_code == FAKE_MINER_EDIT_QUERY:
                    query = edit_query
            results = mine_google_links(query, num=10, stop=10, pause=random.randint(1, 3))
            for (title, link, snippet, date) in results:
                title = ' '.join(title.split())
                snippet = ' '.join(snippet.split())
                if date != '':
                    date = ' '.join(date.split())
                    try:
                        date = cleaner.date_persian2english(date, delimiter=' ', persian_month=True)
                    except:
                        date = '-'
                item = {
                    'd_id': news.d_id,
                    'f_id': uuid.uuid1().hex,
                    'f_title': '-' if not title else title,
                    'f_link': link,
                    'f_snippet': '-' if not snippet else snippet,
                    'f_date': date
                }
                if r_callback:
                    result_code = r_callback(item)
                    assert (result_code and result_code in [FAKE_MINER_IGNORE_RESULT, FAKE_MINER_ACCEPT_RESULT]), 'Callback function must return proper RESULT_CODE'
                    if result_code == FAKE_MINER_ACCEPT_RESULT:
                        pass
                    elif result_code == FAKE_MINER_IGNORE_RESULT:
                        continue
                candidate_list = candidate_list.append(item, ignore_index=True)
    candidate_list.to_excel('fake_candidate_news.xlsx', index=False, index_label=False)
    return candidate_list


if __name__ == '__main__':
    def result_call(item):
        print(item)
        code = input('is good?')
        if code == 'y':
            return FAKE_MINER_ACCEPT_RESULT
        elif code == 'n':
            return FAKE_MINER_IGNORE_RESULT
    # df_denied = crawl_denied_news('20200501', '20200901', use_api=False)
    df_denied = pd.read_excel('denied_news.xlsx')
    df_candidate = crawl_rumor_candidate(df_denied)
    inner_join_df = pd.merge(df_denied, df_candidate, on='d_id', how='inner')
    inner_join_df.to_excel('new_fake_candidate_news.xlsx', index=False, index_label=False)

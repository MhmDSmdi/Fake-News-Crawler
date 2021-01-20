import datetime
import re
from persiantools.jdatetime import JalaliDate
import glob
from parsivar import Normalizer, Tokenizer, FindStems, POSTagger
from collections import OrderedDict
import arabic_reshaper

STOPWORDS_PATH = './stopwords/{}'
tokenizer = Tokenizer()
normalizer = Normalizer()
stemmer = FindStems()
STOPWORD_SET = set()
for stop_file in glob.glob(STOPWORDS_PATH.format('*.txt')):
    file = open(stop_file, 'r')
    lines = file.readlines()
    for line in lines:
        STOPWORD_SET.add(line.strip('\n'))

PERSIAN_MONTH_DICT = {
    'فروردین': '01',
    'اردیبهشت': '02',
    'خرداد': '03',
    'تیر': '04',
    'مرداد': '05',
    'شهریور': '06',
    'مهر': '07',
    'آبان': '08',
    'آذر': '09',
    'دی': '10',
    'بهمن': '11',
    'اسفند': '12'
}

ENGLISH_MONTH_DICT = {
    'ژانویهٔ': '01',
    'فوریهٔ': '02',
    'مارس': '03',
    'آوریل': '04',
    'مهٔ': '05',
    'ژوئن': '06',
    'ژوئیهٔ': '07',
    'اوت': '08',
    'سپتامبر': '09',
    'اکتبر': '10',
    'نوامبر': '11',
    'دسامبر': '12'
}

def num_persian2english(text):
    in_tab = '۱۲۳۴۵۶۷۸۹۰١٢٣٤٥٦٧٨٩٠'
    out_tab = '12345678901234567890'
    translation_table = str.maketrans(in_tab, out_tab)
    return text.translate(translation_table)

def removeDupWithOrder(text):
    modified_word = '~'
    for char in text:
        if modified_word[-1] != char:
            modified_word += char
    return modified_word[1:]

def clean(text, keep_stopword=False, tokenized=True, stemming=True, remove_repetition=True):
    text = re.sub(r"[,.;:?!،()؟]+", " ", text)
    text = re.sub('[^\u0600-\u06FF]+', " ", text)
    text = re.sub(r'[\u200c\s]*\s[\s\u200c]*', " ", text)
    text = re.sub(r'[\u200c]+', " ", text)
    text = re.sub(r'[\n]+', " ", text)
    text = re.sub(r'[\t]+', " ", text)
    text = re.sub(r'([1234567890۱۲٢٠٨۳۴۵٥٥۶۷۸۹۰٦٤١]+)|([^\w\s])', '', text)
    if remove_repetition:
        text = removeDupWithOrder(text)
    text = normalizer.normalize(text)
    text = tokenizer.tokenize_words(text)
    if not keep_stopword:
        text = list(filter(lambda x: x not in STOPWORD_SET, text))
    if stemming:
        text = list(stemmer.convert_to_stem(word).split('&')[0] for word in text)
    if not tokenized:
        text = ' '.join([str(elem) for elem in text])
        text = arabic_reshaper.reshape(text)
    return text


def date_persian2english(in_date, delimiter='-', persian_month=True):
    dates = str(in_date).split(delimiter)
    if any(dword in in_date for dword in ['پیش', 'قبل']):
        delta = int(num_persian2english(dates[0]))
        if 'ساعت' in in_date:
            return (datetime.datetime.now() - datetime.timedelta(hours=delta)).strftime('%Y%m%d')
        elif 'روز' in in_date:
            return (datetime.datetime.now() - datetime.timedelta(days=delta)).strftime('%Y%m%d')
        elif 'دقیقه' in in_date:
            return (datetime.datetime.now() - datetime.timedelta(minutes=delta)).strftime('%Y%m%d')
    year = num_persian2english(dates[0])
    days = num_persian2english(dates[2])
    if int(year) <= 31 and int(days) > 1300:
        days = num_persian2english(dates[0])
        year = num_persian2english(dates[2])
    months = num_persian2english(dates[1])
    if not months.isdigit():
        if persian_month:
            months = PERSIAN_MONTH_DICT[months]
        else:
            months = ENGLISH_MONTH_DICT[months]
    date = JalaliDate(day=int(days), month=int(months), year=int(year)).to_gregorian().strftime('%Y%m%d')
    return date
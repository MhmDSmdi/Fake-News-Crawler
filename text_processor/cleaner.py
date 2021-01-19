from hazm import *
import datetime
import re
from persiantools.jdatetime import JalaliDate

persian_month_dict = {
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

english_month_dict = {
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

normalizer = Normalizer()
stemmer = Stemmer()
tokenizer = WordTokenizer()
lema = Lemmatizer()


def clean_text(text, remove_stopwords=True):
    stop_list = []
    if remove_stopwords:
        stop_list = stopwords_list()
    data = re.sub(r'([1234567890۱۲٢٠٨۳۴۵٥٥۶۷۸۹۰٦٤١]+)|([^\w\s])', '', text)
    data = normalizer.normalize(data)
    tokens = tokenizer.tokenize(data)
    # tokens = [word for word in tokens if word not in stop_list]
    return ' '.join(tokens)


def num_persian2english(text):
    in_tab = '۱۲۳۴۵۶۷۸۹۰١٢٣٤٥٦٧٨٩٠'
    out_tab = '12345678901234567890'
    translation_table = str.maketrans(in_tab, out_tab)
    return text.translate(translation_table)


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
            months = persian_month_dict[months]
        else:
            months = english_month_dict[months]
    date = JalaliDate(day=int(days), month=int(months), year=int(year)).to_gregorian().strftime('%Y%m%d')
    return date
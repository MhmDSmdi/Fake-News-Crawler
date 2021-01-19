import json
import pymongo
from itemadapter import ItemAdapter
from text_processor import cleaner


class TextProcessingPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        adapter['body'] = ' '.join(adapter['body'].split())
        adapter['title'] = ' '.join(adapter['title'].split())
        adapter['snippet'] = ' '.join(adapter['snippet'].split())
        if adapter['agency'] == 'irna':
            adapter['date'] = cleaner.date_persian2english(' '.join(adapter['date'].split()).split('‏')[0].replace('،', ''), delimiter=' ')
        elif adapter['agency'] == 'isna':
            adapter['date'] = adapter['date'].split(' ')[0].replace('-', '')
        elif adapter['agency'] == 'mehrnews':
            adapter['date'] = cleaner.date_persian2english(adapter['date'].split('‏')[0].replace('،', ''), delimiter=' ')
        elif adapter['agency'] == 'fars':
            d = adapter['date'].split()[0].split('/')
            if len(d[0]) < 2:
                d[0] = '0' + d[0]
            if len(d[1]) < 2:
                d[1] = '0' + d[1]
            adapter['date'] = d[2] + d[0] + d[1]
        elif adapter['agency'] == 'hamshahri':
            adapter['date'] = cleaner.date_persian2english(' '.join(adapter['date'].split('-')[0].split()[1:4]), delimiter=' ')
        return item


class MongoPipeline:
    def __init__(self, mongo_collection, mongo_db):
        self.mongo_collection = mongo_collection
        self.mongo_db = mongo_db

    def open_spider(self, spider):
        self.client = pymongo.MongoClient()
        self.db = self.client[self.mongo_db][self.mongo_collection]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.db.insert_one(ItemAdapter(item).asdict())
        return item

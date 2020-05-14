# -*- coding: utf-8 -*-
"""
@time: 2020/5/11 3:14 下午
@desc:
"""
import json

from elasticsearch import Elasticsearch, helpers

from pyetl.utils import batch_dataset


class Index(object):

    def __init__(self, name, con, doc_type=None):
        self.name = name
        self.doc_type = doc_type
        self.es = con

    def search(self, body=None):
        return self.es.search(index=self.name, doc_type=self.doc_type, body=body)

    def insert_one(self, doc):
        return self.es.index(index=self.name, doc_type=self.doc_type, body=doc)

    def bulk_insert(self, docs, batch_size=10000):
        def mapping(doc):
            return {"_index": self.name, "_type": self.doc_type, "_source": doc}
        docs = (mapping(doc) for doc in docs)
        for batch in batch_dataset(docs, batch_size=batch_size):
            helpers.bulk(self.es, batch)

    def delete_one(self, _id):
        self.es.delete(index=self.name, doc_type=self.doc_type, id=_id)

    def bulk_delete(self, body):
        """
        批量删除
        body = {'query': {'match': {"_id": "BxCklGwBt0482SoSeXuE"}}}
        demo_index.delete_many(body=body)
        """
        self.es.delete_by_query(index=self.name, doc_type=self.doc_type, body=body)

    def create(self, settings):
        return self.es.indices.create(index=self.name, doc_type=self.doc_type, body=settings)

    def drop(self):
        return self.es.indices.delete(index=self.name, doc_type=self.doc_type, ignore=[400, 404])


class AliasManager(object):

    def __init__(self, name, es):
        self.name = name
        self.es = es

    def exists(self):
        return self.es.indices.exists_alias(self.name)

    def list(self):
        """
         {'job-boss': {'aliases': {'job': {}}}, 'accounts': {'aliases': {'job': {}}}}
        """
        if self.exists():
            return self.es.indices.get_alias(name=self.name)
        else:
            return {}

    def add(self, index):
        return self.es.indices.put_alias(name=self.name, index=index)

    def remove(self, index):
        actions = json.dumps({
            "actions": [
                {"remove": {"index": index, "alias": self.name}},
            ]
        })
        return self.es.indices.update_aliases(body=actions)

    def drop(self):
        return self.es.indices.delete_alias(name=self.name, index="_all")


class ES(Elasticsearch):

    def get_index(self, name, doc_type=None):
        return Index(name, self, doc_type=doc_type)

    def get_alias_manager(self, name):
        return AliasManager(name, self)
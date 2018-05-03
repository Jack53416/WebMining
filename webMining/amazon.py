import boto
import boto.cloudsearch2
#AbstractCloudSearchDocument

from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty

import hashlib
import json
from datetime import datetime

DEFAULT_BATCH_SIZE = 100

class AbstractCloudSearchDocument(object):
    __metaclass__ = ABCMeta
    
    @abstractproperty
    def cloudSearchId(self):
        pass
    
    @abstractmethod
    def toJson(self):
        pass

class CloudWebsiteDocument(AbstractCloudSearchDocument):
    def __init__(self, address, domain, content, last_update = datetime.utcnow(), author = None, content_language = None, keywords = None, description = None):
        self.address = address
        self.domain = domain
        self.content = content
        self.author, self.content_language, self.keywords, self.description, self.last_update = author, content_language, keywords, description, last_update
    
    @property
    def cloudSearchId(self):
        return hashlib.sha224(self.address).hexdigest()
    
    def toJson(self):
        return {
                'address': self.address,
                'domain': self.domain,
                'author': self.author,
                'keywords': self.keywords,
                'description': self.description,
                'content_language': self.content_language,
                'content': self.content,
                'last_update': self.last_update.strftime("%Y-%m-%dT%H:%M:%SZ")
                }
    

class AmazonClient(object):
    REGION = boto.cloudsearch2.regions()[6]
    
    _clsDomainCache = {}
    
    def getDomain(self, domainIndex):
        try:
            return self._clsDomainCache[domainIndex]
        except KeyError:
            print boto.connect_cloudsearch2(region = self.REGION, debug = True ,sign_request = True).list_domains()
            self._clsDomainCache[domainIndex] = \
                boto.connect_cloudsearch2(
                    region = self.REGION,
                    sign_request = True).lookup(domainIndex)
            return self._clsDomainCache[domainIndex]

class CloudSearchIndexer(AmazonClient):
    def __init__(self, domainIndex, batchSize = DEFAULT_BATCH_SIZE):
        self.domain = self.getDomain(domainIndex)
        print self.domain
        self.documentServiceConnection = self.domain.get_document_service()
        self.batchSize = batchSize
        self.itemsInBatch = 0
    
    @classmethod
    def forDomainIndex(cls, domainIndex):
        return cls(domainIndex)
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args, **kwargs):
        if len(args) > 1 and isinstance(args[1], Exception):
            raise args[1]
        self._commitToAmazon()
    
    def _commitToAmazon(self):
        self.documentServiceConnection.commit()
        self.documentServiceConnection.clear_sdf()
        self.itemsInBatch = 0
    
    def addDocument(self, cloudSearchDocument):
        cloudSearchJson = cloudSearchDocument.toJson()
        
        cloudSearchJson = self._nulifyFalsyValues(cloudSearchJson)
        self.documentServiceConnection.add(
                cloudSearchDocument.cloudSearchId,
                cloudSearchJson
            )
        self._updateBatch()
    
    def _nulifyFalsyValues(self, jsonDict):
        return {k: v for k, v in jsonDict.items() if v}
    
    def deleteDocument(self, cloudSearchDocument):
        self.documentServiceConnection.delete(cloudSearchDocument.cloudSearchId)
        self._updateBatch()
    
    def _updateBatch(self):
        self.itemsInBatch += 1
        if self.itemsInBatch == self.batchSize:
            self._commitToAmazon()
    
    
def test():
    with CloudSearchIndexer.forDomainIndex("websites") as cloudIndexer:
        document = CloudWebsiteDocument('http://test2.pl', 'test.pl', 'Some test python data, update')
        cloudIndexer.addDocument(document)

test()

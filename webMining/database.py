import sqlite3

from pattern.db import Database, field, pk, STRING, BOOLEAN, INTEGER, DATE, NOW, UNIQUE, date, TableError
from pattern.db import eq, all, any
from webPage import WebPage

class HistoryDb(object):
    
    def __init__(self):
        self.db = Database('website_history')
        self.createTables()
        
    def createTables(self):
        errMsg = ',ommitting...'
        
        try:
            self.db.create('websites', fields = (
                    pk('id'), 
                    field('address', index = UNIQUE), 
                    field('domain_id'), 
                    field('connected', BOOLEAN, default = True),
                    field('lastVisited', DATE, default = NOW)
                ))
        except TableError as err:
            print err, errMsg
            
        try:
            self.db.create('links', fields = (
                    pk('id'),
                    field('website', INTEGER, optional = False),
                    field('reference', INTEGER, optional = False)
                ))
        except TableError as err:
            print err, errMsg
        try:
            self.db.create('domains', fields = (
                    pk('id'),
                    field('name', STRING(80), index = UNIQUE)
                ))
        except TableError as err:
            print err, errMsg
            
        self.db.link(self.db.domains, 'domains.id', self.db.websites, 'websites.domain_id')
        
    def getDomainId(self, name):
        results = self.db.domains.search(filters = all(eq('name', page.url.domain))).rows()
        if len(results) > 0:
            return results[0][0]
        return None
    
    def insertDomain(self, domainName):
        try:
            self.db.domains.append(name = page.url.domain)
        except sqlite3.IntegrityError:
            pass
    
    def insertRelation(self, parent, child):
        parentId = self.db.websites.search(filters = all(eq('address', parent.url.string))).rows()[0][0]
        childId = self.db.websites.search(filters = all(eq('address', child.url.string))).rows()[0][0]
        currentRecords = self.db.links.search(filters = all(eq('website', parentId), eq('reference', childId))).rows()
        if len(currentRecords) == 0:
            self.db.links.append(website = parentId, reference = childId)
        
    
    def insertWebpage(self, page, connection = False):
        idDomain = None
        dateVisited = None
        
        if page.url.domain:
            self.insertDomain(page.url.domain)
            idDomain = self.getDomainId(page.url.domain)
        
        if connection:
            dateVisited = date(NOW)
        try:
            self.db.websites.append(address = page.url.string, domain_id = idDomain, connected = connection, lastVisited = dateVisited)
        except sqlite3.IntegrityError:
            pass

        for link in page.getLinks():
            if link.url.anchor:
                continue
            self.insertWebpage(link)
            self.insertRelation(page, link)
    
    def readWebPage(self, urlString, depth = 1):
        webPageData = self.db.websites.search(filters = all(eq('address', WebPage.parseUrl(urlString).string))).rows()
        pageLinks = []
        result = None
        
        if len(webPageData) == 0:
            return result
        
        webPageData = webPageData[0]
        pageId = webPageData[0]
        result = WebPage(url = webPageData[1], depth = depth)
        
        query = self.db.execute(
            'SELECT w.{0}, r.{0} from links join websites as w on links.{1} = w.id join websites as r on links.{2} = r.id WHERE w.id = {3};'
            .format(self.db.websites.fields[1], self.db.links.fields[1], self.db.links.fields[2], pageId)
            )
        
        for row in iter(query):
            pageLinks.append(WebPage(url = row[1], parent = result, depth = depth + 1))
        result.links =  pageLinks
        return result
          
            
        
    
page = WebPage(url = 'pduch.kis.p.lodz.pl')
page.downloadContent()
hist = HistoryDb()
hist.insertWebpage(page, connection = True)
hist.readWebPage('pduch.kis.p.lodz.pl')

import sqlite3

from pattern.db import Database, field, pk, STRING, BOOLEAN, INTEGER, DATE, NOW, UNIQUE, date, TableError
from pattern.db import eq, all, any
from webPage import WebPage

class WebsiteDatabase(object):
    
    class DbException(Exception):
        pass
    
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
        
        try:
            self.db.create('session', fields = (
                pk('id'),
                field('website_id', INTEGER, optional = False, index = UNIQUE),
                field('depth', INTEGER, optional = False)
                ))
        except TableError as err:
            print err, errMsg
            
        self.db.link(self.db.domains, 'domains.id', self.db.websites, 'websites.domain_id')
        self.db.link(self.db.session, 'session.website_id', self.db.websites, 'websites.id')
        
    def getDomainId(self, name):
        results = self.db.domains.search(filters = all(eq('name', name))).rows()
        if len(results) > 0:
            return results[0][0]
        return None
    
    def insertDomain(self, domainName):
        try:
            self.db.domains.append(name = domainName)
        except sqlite3.IntegrityError:
            pass
    
    def insertRelation(self, parent, child):
        if parent is None or child is None:
            return
        
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
            self.insertRelation(page.parent, page)
        except sqlite3.IntegrityError:
            if connection:
                self.db.websites.update(all(eq('address', page.url.string)), connected = True, lastVisited = dateVisited)


#        for link in page.getLinks():
#            if link.url.anchor and not link.isWebPage():
#                continue
#            self.insertWebpage(link)
#            self.insertRelation(page, link)
    
    def readWebPage(self, urlString, depth = 1, isExternal = False):
        webPageData = self.db.websites.search(filters = all(eq('address', WebPage.parseUrl(urlString).string))).rows()
        pageLinks = []
        result = None
        
        if len(webPageData) == 0:
            return result
        
        webPageData = webPageData[0]
        pageId = webPageData[0]

        depthData = self.db.session.search('depth', all(eq('website_id', pageId)))
        if len(depthData) > 0:
            depth = depthData[0][0]

        result = WebPage(url = webPageData[1], depth = depth, isExternal = isExternal)
        
        query = self.db.execute(
            'SELECT w.{0}, r.{0} from links join websites as w on links.{1} = w.id join websites as r on links.{2} = r.id WHERE w.id = {3};'
            .format(self.db.websites.fields[1], self.db.links.fields[1], self.db.links.fields[2], pageId)
            )
        
        for row in iter(query):
            pageLinks.append(WebPage(url = row[1], parent = result, depth = depth + 1))
        result.links =  pageLinks
        
        return result
    
    def wasPageVisited(self, page):
        webPageData = self.db.websites.search('lastVisited', filters = all(eq('address', page.url.string))).rows()
        if len(webPageData) == 0:
            return False
        dateVisited = webPageData[0][0]
        
        if dateVisited is None:
            return False
        return True
    
    def isInThisSession(self, page):
        webPageData = self.db.session.search('websites.address', filters = all(eq('websites.address', page.url.string))).rows()
        if len(webPageData) > 0:
            return True
        return False
    
    def appendSession(self, page):
        pageId = self.db.websites.search('id', filters = all(eq('address', page.url.string))).rows()
        if len(pageId) == 0:
            raise DbException("Trying to append website to session without having it in website table")
        
        pageId = pageId[0][0]
        try:
            self.db.session.append(website_id = pageId, depth = page.depth)
        except sqlite3.IntegrityError as err:
            print "Invalid session data, cleaning session..."
            self.clearSession()
            
    def clearSession(self):
        sessionData = self.db.session.rows()
        for row in iter(sessionData):
            self.db.session.remove(row[0])
            
        
def test():
    page = WebPage(url = 'pduch.kis.p.lodz.pl')
    page.downloadContent()
    hist = WebsiteDatabase()
    hist.insertWebpage(page, connection = True)
    if not hist.isInThisSession(page):
        hist.appendSession(page)
    hist.readWebPage('pduch.kis.p.lodz.pl')
    page = WebPage(url = 'http://www.kis.p.lodz.pl/')
    print hist.wasPageVisited(page)
    
    
#test()

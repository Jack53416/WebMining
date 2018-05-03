import re
import urlparse
import httplib
import hashlib

from collections import Counter
from pattern.web import URL, plaintext, DOM, abs, URLError, URLTimeout, HTTP404NotFound, MIMETYPE_WEBPAGE
from pattern.web import Crawler, HTMLLinkParser
from pattern.vector import count,words, LEMMA
from datetime import datetime

from emitter import Emitter
from amazon import CloudWebsiteDocument

class WebPage(CloudWebsiteDocument):
    
    def __init__(self, url = "", parent = None, links = [], depth = 1, isExternal = False):
        if url:
            self.url = WebPage.parseUrl(url)
        self.content = None
        self.dom = None
        self.parent = parent
        self.depth = depth
        if parent is not None:
            if parent.isExternal or self.parent.url.domain != self.url.domain:
                isExternal = True

        self.isExternal = isExternal
        self.links = links
    
    def __str__(self):
        return self.url.string
    
    def __eq__(self, other):
        return self.url.string == other.url.string
    
    def decodeContent(self):
        match = re.search("<meta .* charset=([a-zA-Z0-9\-]*).*\/>", self.content)
        if match:
            encoding = match.group(1)
            try:
                self.content = self.content.decode(encoding)
            except LookupError as err:
                print "Warning " + encoding + " is not valid"
    
    def isWebPage(self):
        try:
            return self.url.mimetype in MIMETYPE_WEBPAGE
        except httplib.InvalidURL:
            return False
        
    def downloadContent(self):
        if not self.isWebPage():
            raise URLError("Invalid or empty content type")
        try:
            self.content = self.url.download(timeout = 1)  
        except httplib.InvalidURL:
            raise URLError("Invalid URL")
        
        self.decodeContent()
        self.dom = DOM(self.content)
        
        
    def countWords(self):
        wordDict = count(words(plaintext(self.content), filter = lambda w: w.strip("'").isalpha()))
        return Counter(wordDict)

    def getLinks(self):
        if self.content is None:
            return self.links
        
        if len(self.links) == 0:
            links = [abs(x.url, base = self.url.redirect or self.url.string)
                    for x in HTMLLinkParser().parse(self.content, url = self.url.string)]
            self.links =  [WebPage(x, self, depth = self.depth + 1) for x in links]
        return self.links

    def getImages(self):
        images = []
        for image in self.dom('img'):
            images.append(abs(image.attributes.get('src', ''), base = self.url.redirect or self.url.string))
        return images
        
    def getScripts(self):
        scripts = []
        for script in self.dom('script'):
            src = script.attributes.get('src', '')
            if(src):
                scripts.append(abs(src, base = self.url.redirect or self.url.string))
            else:
                scripts.append(str(script))
        return scripts
    
    def cleanCashedData(self):
        self.content = None
        self.dom = None
        self.links = []
    
    @staticmethod
    def parseUrl(urlString):
        match = re.search('//', urlString)
        if not match:
            urlString = '//' + urlString
        
        url = urlparse.urlsplit(urlString)
        if not url.scheme:
            url = url._replace(scheme = 'http')

        return URL(url.geturl())
    
    @property
    def cloudSearchId(self):
        return hashlib.sha224(self.url.string).hexdigest()
    
    def toJson(self):
        try:
            content = plaintext(self.dom.body.content)
        except AttributeError:
            content = None
        return {
                'address': self.url.string,
                'domain': self.url.domain,
                'content': content,
                'last_update': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                }
        

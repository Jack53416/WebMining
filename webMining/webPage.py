import re
import urlparse
import httplib
import itertools
from collections import Counter
from pattern.web import URL, plaintext, DOM, abs, URLError, URLTimeout, HTTP404NotFound, MIMETYPE_WEBPAGE
from pattern.web import Crawler, HTMLLinkParser
from pattern.vector import count,words, LEMMA
from scipy import spatial
from emitter import Emitter


class WebPage:
    
    def __init__(self, url = "", parent = None, depth = 1):
        if url:
            self.url = URL(string = WebPage.parseUrl(url))
        self.content = None
        self.dom = None
        self.parent = parent
        self.depth = depth
    
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
    
        
    def downloadContent(self):
        try:
            if self.url.mimetype not in MIMETYPE_WEBPAGE:
                raise URLError(str(self.url.mimetype) + " is not supported content type")
            self.content = self.url.download(cached = False, timeout = 5)  
        except httplib.InvalidURL:
            raise URLError("Invalid Url")

        self.decodeContent()
        self.dom = DOM(self.content)
        
        
    def countWords(self):
        wordDict = count(words(plaintext(self.content), filter = lambda w: w.strip("'").isalpha()))
        return Counter(wordDict)

    def getLinks(self):
        links = [abs(x.url, base = self.url.redirect or self.url.string)
                 for x in HTMLLinkParser().parse(self.content, url = self.url.string)]
        return [WebPage(x, self, self.depth + 1) for x in links]

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
    
    @staticmethod
    def parseUrl(urlString):
        match = re.search('//', urlString)
        if not match:
            urlString = '//' + urlString
        
        url = urlparse.urlsplit(urlString)
        if not url.scheme:
            url = url._replace(scheme = 'http')

        return url.geturl()

class Result(object):
    def __init__(self, wordStats = Counter(), links = set(), images = set(), scripts = set()):
        self.wordStats, self.links, self.images, self.scripts = \
            wordStats, links, images, scripts
    
    def cosineSimilarity(self, other):
        jointVector = self.wordStats + other.wordStats
        selfVector = []
        otherVector = []
        for key in jointVector.keys():
            #print key + ' first: ' + str(self.wordStats[key]) + ' second ' + str(other.wordStats[key]) 
            selfVector.append(self.wordStats[key])
            otherVector.append(other.wordStats[key])
        #print selfVector
        #print otherVector
        return 1 - spatial.distance.cosine(selfVector, otherVector)
    
    def emit(self, output):
        result = unicode('')
        if len(self.wordStats) > 0:
            output.emitLine("Words: \r\n")
            output.emit(self.wordStats)
            output.emitLine('')
        if len(self.links) > 0:
            output.emitLine("Links: \r\n")
            output.emit(self.links)
            output.emitLine('')
        if len(self.images) > 0:
            output.emitLine("Images \r\n")
            output.emit(self.images)
            output.emitLine('')
        if len(self.scripts) > 0:
            output.emitLine("scripts: \r\n")
            output.emit(self.scripts)
            output.emitLine('')
            
        
class WebCrawler():
    def __init__(self, args, depth = 1):
        self.links = [WebPage(x) for x in args.url]
        self.depth = depth
        self.history = []
        self.done = False
        self.options = args
        self.results = {link.url.domain : Result() for link in self.links}
        
    def crawl(self):
        if len(self.links) < 1:
            self.done = True
            self.finish()
            return
        site = self.links.pop(0)
        try:
            site.downloadContent()
        except HTTP404NotFound:
            return self.fail(site, "404 not found")
        except URLTimeout:
            return self.fail(site, "Timeou error")
        except URLError as err:
            return self.fail(site, str(err))
        
        self.history.append(site)

        if site.depth < self.depth:
            for link in site.getLinks():
                if link not in self.links \
                and link not in self.history \
                and not link.url.anchor \
                and link.url.domain == site.url.domain:
                    self.links.insert(0,link)
    
        self.visit(site)
        site.cleanCashedData()

        
    
    def visit(self, page):
        print 'visited: ', page.url.string
        try:
            if self.options.text:
                self.results[page.url.domain].wordStats += page.countWords()
            if self.options.a:
                links = [link.url.string for link in page.getLinks()]
                self.results[page.url.domain].links.update(links)
            if self.options.image:
                self.results[page.url.domain].images.update(page.getImages())
            if self.options.script:
                self.results[page.url.domain].scripts.update(page.getScripts())
        except Exception as e:
            print "Error parsing document: ", type(e).__name__ + ': ' + str(e) 

    def fail(self, link, error):
        print 'failed:', link.url.string, 'err: ', error
    
    def finish(self):
        """Print all results and calculate cosine similarity between all provided ur;s"""
        with Emitter(self.options.console, self.options.file) as output:
            for key, value in self.results.iteritems():
                output.emitLine(key)
                value.emit(output)
            
            if len(self.results) > 1 and self.options.text and self.options.cos:
                combinations = [list(x) for x in itertools.combinations(self.results.keys(), 2)]
                for pair in combinations:
                    cosValue = self.results[pair[0]].cosineSimilarity(self.results[pair[1]])
                    output.emitLine(u"cos similarity between:{0} and {1} = {2}".format(pair[0], pair[1], cosValue))
    
            output.emitLine('')
            output.emitLine("max depth: " + str(max(site.depth for site in self.history)))
            output.emitLine("sites visited: " + str(len(self.history)))

import re
import urlparse
from collections import Counter
from pattern.web import URL, plaintext, DOM, abs, URLError
from pattern.web import Crawler
from pattern.vector import count,words, LEMMA

from emitter import Emitter


class WebPage:
    
    def __init__(self, url = ""):
        if url:
            self.url = URL(string = WebPage.parseUrl(url))
        self.content = None
        self.dom = None
            
    def decodeContent(self):
        match = re.search("<meta .* charset=(.*) .*\/>", self.content)
        if match:
            encoding = match.group(1)
            self.content = self.content.decode(encoding)
    
        
    def downloadContent(self):
        self.content = self.url.download(cached = True)        
        self.decodeContent()
        self.dom = DOM(self.content)
        
        
    def countWords(self):
        wordDict = count(words(plaintext(self.content), filter = lambda w: w.strip("'").isalpha()))
        return Counter(wordDict)

    def getLinks(self):
        links = []
        for link in self.dom('a'):
            links.append(abs(link.attributes.get('href', ''), base = self.url.redirect or self.url.string))
        return links

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


class WebCrawler():
    def __init__(self, args, depth = 1, delay = 20.0):
        self.links = args.url
        self.depth = depth
        self.delay = delay
        self.history = []
        self.done = False
        self.options = args
        
    def crawl(self):
        if len(self.links) < 1:
            self.done = True
            return
        
        site = WebPage(self.links.pop(0))
        try:
            site.downloadContent()
        except URLError as err:
            self.fail(site, str(err))
            return
        
        self.visit(site)
        self.history.append(site)
    
    def visit(self, page):
        with Emitter(self.options.console, self.options.file) as output:
            output.emitLine('visited:'+ page.url.string)
            if self.options.text:
                output.emitLine("Words: \r\n")
                output.emit(page.countWords())
                output.emitLine('')
            if self.options.a:
                output.emitLine("Links: \r\n")
                output.emit(page.getLinks())
                output.emitLine('')
            if self.options.image:
                output.emitLine("Images: \r\n")
                output.emit(page.getImages())
                output.emitLine('')
            if self.options.script:
                output.emitLine("Scripts: \r\n")
                output.emit(page.getScripts())
                output.emitLine('')
            

    def fail(self, link, error):
        print 'failed:', link.url.string, 'err: ', error
    
    

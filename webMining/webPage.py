import re
import urlparse
from pattern.web import URL, plaintext, DOM, abs, URLError
from pattern.vector import count,words, LEMMA

class WebPage:
    
    def __init__(self, url):
        self.url = URL(string = WebPage.parseUrl(url))
        self.content = None
        self.dom = None
            
    def decodeContent(self):
        match = re.search("<meta .* charset=(.*) .*\/>", self.content)
        if match:
            encoding = match.group(1)
            self.content = self.content.decode(encoding)
    
        
    def downloadContent(self):
        try:
            self.content = self.url.download(cached = True)
        except URLError as err:
            sys.exit("URLError: " + str(err))
        
        self.decodeContent()
        self.dom = DOM(self.content)
        
        
    def countWords(self):
        wordDict = count(words(plaintext(self.content), filter = lambda w: w.strip("'").isalpha()))
        return wordDict

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

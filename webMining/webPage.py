import re
import urlparse
import httplib
import itertools
import numpy as np

from collections import Counter
from pattern.web import URL, plaintext, DOM, abs, URLError, URLTimeout, HTTP404NotFound, MIMETYPE_WEBPAGE
from pattern.web import Crawler, HTMLLinkParser
from pattern.vector import count,words, LEMMA
from pattern.graph import Graph, bfs, adjacency

from scipy import spatial
from emitter import Emitter

import operator

class WebPage:
    
    def __init__(self, url = "", parent = None, links = [], depth = 1):
        if url:
            self.url = WebPage.parseUrl(url)
        self.content = None
        self.dom = None
        self.parent = parent
        self.depth = depth
        if parent is not None:
            self.isExternal = parent.isExternal
        else:
            self.isExternal = False
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
            for link in self.links:
                if link.url.domain != self.url.domain:
                    link.isExternal = True
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
        
        if args.graph or args.rank:
            self.webGraph = Graph(distance = 30.0) 
            for link in self.links:
                self.webGraph.add_node(link.url.domain, radius = 15, fill = (1, 0, 0, 0.5))
        
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
            return self.fail(site, "Timeout error")
        except URLError as err:
            return self.fail(site, str(err))
        
        self.history.append()

        for link in site.getLinks():
            if self.isValidForQueue(link):
                if link.isExternal and (self.options.graph or self.options.rank):
                    self.addDomainNode(link)
                    if site.depth < self.depth:
                        self.links.append(link)
                elif not link.isExternal and site.depth < self.depth:
                    self.links.insert(0, link)
        self.visit(site)
        site.cleanCashedData()

    def isValidForQueue(self, link):
        if link not in self.links \
            and link not in self.history \
            and not link.url.anchor:
                return True
        return False
                
    def addDomainNode(self, page):
        match = re.search("\.", page.url.domain)
        if not match:
            return
        if page.parent.url.domain == page.url.domain:
            return
        if self.webGraph.node(page.url.domain) is None:
            self.webGraph.add_node(page.url.domain, radius = 15)
        if self.webGraph.edge(page.parent.url.domain, page.url.domain) is None:
            self.webGraph.add_edge(page.parent.url.domain, page.url.domain, weight = 0.0, type = 'is-related-to')
    
    def visit(self, page):
        print 'visited: ', page.url.string
        if page.isExternal and self.options.graph or self.options.rank and page.url.domain not in self.results.keys():
            self.webGraph.node(page.url.domain).fill = (0,1,0,0.5)
            return
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
            
            if self.options.graph:
                self.webGraph.eigenvector_centrality()
                self.webGraph.export('graph', directed=True, width = 2200, height = 1600, repulsion = 10)
            if self.options.rank:
                ranks = self.calculatePageRank()
                output.emitLine('')
                output.emit(ranks)

    def calculatePageRank(self):
        adjMap = adjacency(self.webGraph, directed = True, stochastic = True)
        domains = adjMap.keys()
        M = np.zeros((len(domains), len(domains)))
        for idx, domain in enumerate(domains):
            connections = adjMap[domain].keys()
            for connection in connections:
                M[idx, domains.index(connection)] = adjMap[domain][connection]
            
        M = np.transpose(M)
        #M = np.array([[0,0,0,0,1], [0.5,0,0,0,0], [0.5,0,0,0,0], [0,1,0.5,0,0], [0,0,0.5,1,0]])
        #M = np.array([[0,  0.5, 0],[0.5,0.5, 0],  [0.5, 0,  0]])
        pageScores =  self.executeComputations(M)
        print pageScores
        ranks = dict(zip(domains, pageScores))
        ranks = sorted(ranks.items(), key = operator.itemgetter(1))
        return ranks
    
    def executeComputations(self, M):
        damping = 0.80
        error = 0.0000001
        N = M.shape[0]
        v = np.ones(N)
        v = v / np.linalg.norm(v, 1)
        last_v = np.full(N, np.finfo(float).max)
        for i in range(0, N):
            if sum(M[:, i]) == 0:
                M[:, i] = np.full(N, 1.0/N)
            

        M_hat = np.multiply(M, damping) + np.full((N,N), (1-damping)/N)
        while np.linalg.norm(v - last_v) > error:
            last_v = v
            v = np.matmul(M_hat, v)

        return np.round(v, 6)
            
        
        

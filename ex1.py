import sys
import re
import argparse
from pattern.web import URL, plaintext, DOM, abs
from pattern.vector import count,words, LEMMA

class Emitter:
    def __init__(self, console = False, filepath = None):
        self.filepath = filepath
        self.console = console
        self.file = None
                
    def emit(self, string):
        if self.file:
            self.file.write(string + '\r\n')
        if self.console:
            print string
                         
    def __enter__(self):
        if self.filepath:
            try:
                self.file = open(self.filepath, "w")
            except IOError as err:
                sys.exit("OSError: " + str(err))
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()
        

def initArgParser(parser):
    parser.add_argument('-site', metavar = 'URL', required = True, help = 'site address to be anylyzed')
    parser.add_argument('-file', metavar = 'FILE_PATH', help = 'output filename')
    parser.add_argument('-console', action = 'store_const', const = True, default = False,  help = 'output displayed directly on the console')
    parser.add_argument('-text', action = 'store_const', const = True, default = False, help = 'analyze all text on the website and count number of occurances of each word')
    parser.add_argument('-a', action = 'store_const', const = True, default = False, help = 'return all links present on website')
    parser.add_argument('-script', action = 'store_const', const = True, default = False, help = 'return all scripts present on website')
    parser.add_argument('-image', action = 'store_const', const = True, default = False, help = 'return all images present on website')

def decodePageContent(content):
    match = re.search("<meta .* charset=(.*) .*\/>", content)
    if match:
        encoding = match.group(1)
        content = content.decode(encoding)
    return content


def downloadPageContent(url):
    try:
        content = url.download(cached = True)
    except URLError as err:
        sys.exit("URLError: " + str(err))
    content = decodePageContent(content)
    return content

def countWords(content, output):
    w = count(words(plaintext(content)))
    output.emit("Words: \r\n")
    for key, value in w.iteritems():
        output.emit("{0}: {1}".format(key.encode('utf-8'), value))
    output.emit("\r\n")    

def getLinks(url, dom, output):
    output.emit("Links: \r\n")
    for link in dom('a'):
        output.emit(abs(link.attributes.get('href', ''), base = url.redirect or url.string))
    output.emit("\r\n")    

def getImages(url, dom, output):
    output.emit("Images: \r\n")
    for image in dom('img'):
        output.emit(abs(image.attributes.get('src', ''), base = url.redirect or url.string))
    output.emit("\r\n")
    
def getScripts(url, dom, output):
    output.emit ("Scripts: \r\n")
    for script in dom('script'):
        src = script.attributes.get('src', '')
        if(src):
            output.emit(abs(src, base = url.redirect or url.string))
        else:
            output.emit(str(script))
    output.emit("\r\n")

def main():
    parser = argparse.ArgumentParser(description='Web mining excersise 1')
    initArgParser(parser)
    args = parser.parse_args()
    if args.console == False and args.file == None:
        sys.exit("Error, Invalid output target!")
    url = URL(string = args.site)
    content = downloadPageContent(url)
    dom = DOM(content)
    
    with Emitter(args.console, args.file) as output:
        
        if args.text:
            countWords(content, output)
                
        if args.a:
            getLinks(url, dom, output)
        
        if args.image:
            getImages(url, dom, output)
        
        if args.script:
            getScripts(url, dom, output)
main()

import sys
import argparse
from webPage import WebPage, WebCrawler
from emitter import Emitter

from pattern.web import Crawler, BREADTH, DEPTH
class Polly(Crawler): 
    def visit(self, link, source=None):
        print 'visited:', repr(link.url), 'from:', link.referrer
    def fail(self, link):
        print 'failed:', repr(link.url)

def initArgParser(parser):
    parser.add_argument('-file', metavar = 'FILE_PATH', help = 'output filename')
    parser.add_argument('-url', nargs = '+', help = 'list of site adresses to be anylyzed')
    parser.add_argument('-console', action = 'store_const', const = True, default = False,  help = 'output displayed directly on the console')
    parser.add_argument('-text', action = 'store_const', const = True, default = False, help = 'analyze all text on the website and count number of occurances of each word')
    parser.add_argument('-a', action = 'store_const', const = True, default = False, help = 'return all links present on website')
    parser.add_argument('-script', action = 'store_const', const = True, default = False, help = 'return all scripts present on website')
    parser.add_argument('-image', action = 'store_const', const = True, default = False, help = 'return all images present on website')
    parser.add_argument('-depth', type = int, default = 1, help = 'domain depth of the crawler')
    parser.add_argument('-cos', action = 'store_const', const = True, default = False, help = 'calculate cosine similarity between provided urls if the option text was enabled')

def main(args = None):
    """The main routine"""
    reload(sys)  
    sys.setdefaultencoding('utf8')
    
    parser = argparse.ArgumentParser(description='Web mining excersise 1')
    initArgParser(parser)
    args = parser.parse_args()
    
    if args.console == False and args.file == None:
        parser.exit("Error, Invalid output target!")
    
    with Emitter(args.console, args.file) as output:
        output.clear()
   
    c = WebCrawler(args, depth = args.depth)
    while not c.done:
        c.crawl()
    
if __name__ == "__main__":
    main()

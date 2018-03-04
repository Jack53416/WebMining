import sys
import re
import argparse
from pattern.web import URL, plaintext, DOM, abs
from pattern.vector import count,words, LEMMA

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



def main():
    parser = argparse.ArgumentParser(description='Web mining excersise 1')
    initArgParser(parser)
    args = parser.parse_args()
    if args.console == False and args.file == None:
        sys.exit("Error, Invalid output target!")
    url = URL(string = args.site)
    content = downloadPageContent(url)
    dom = DOM(content)
    
    if args.text:
        print "Words: \r\n"
        w = count(words(plaintext(content)))
        for key, value in w.iteritems():
            print "{0}: {1}".format(key.encode('utf-8'), value)
        print "\r\n"
    
    if args.a:
        print "Links: \r\n"
        for link in dom('a'):
            print abs(link.attributes.get('href', ''), base = url.redirect or url.string)
        print "\r\n"
    
    if args.image:
        print "Images: \r\n"
        for image in dom('img'):
            print abs(image.attributes.get('src', ''), base = url.redirect or url.string)
        print "\r\n"
    
    if args.script:
        print "Scripts: \r\n"
        for script in dom('script'):
            print script
    
main()

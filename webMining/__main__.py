import argparse
from webPage import WebPage
from emitter import Emitter

def initArgParser(parser):
    parser.add_argument('-site', metavar = 'URL', required = True, help = 'site address to be anylyzed')
    parser.add_argument('-file', metavar = 'FILE_PATH', help = 'output filename')
    parser.add_argument('-url', nargs = '+', help = 'list of site adresses to be anylyzed')
    parser.add_argument('-console', action = 'store_const', const = True, default = False,  help = 'output displayed directly on the console')
    parser.add_argument('-text', action = 'store_const', const = True, default = False, help = 'analyze all text on the website and count number of occurances of each word')
    parser.add_argument('-a', action = 'store_const', const = True, default = False, help = 'return all links present on website')
    parser.add_argument('-script', action = 'store_const', const = True, default = False, help = 'return all scripts present on website')
    parser.add_argument('-image', action = 'store_const', const = True, default = False, help = 'return all images present on website')

def main(args = None):
    """The main routine"""
    
    parser = argparse.ArgumentParser(description='Web mining excersise 1')
    initArgParser(parser)
    args = parser.parse_args()
    
    if args.console == False and args.file == None:
        parser.exit("Error, Invalid output target!")
    
    page = WebPage(args.site)
    page.downloadContent()
    
    with Emitter(args.console, args.file) as output:
        output.clear()
        if args.text:
            output.emitLine("Words: \r\n")
            output.emit(page.countWords())
            output.emitLine('')
        if args.a:
            output.emitLine("Links: \r\n")
            output.emit(page.getLinks())
            output.emitLine('')
        if args.image:
            output.emitLine("Images: \r\n")
            output.emit(page.getImages())
            output.emitLine('')
        if args.script:
            output.emitLine("Scripts: \r\n")
            output.emit(page.getScripts())
            output.emitLine('')
    
if __name__ == "__main__":
    main()

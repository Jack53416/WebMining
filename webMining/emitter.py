import sys
from collections import Counter

class Emitter:
    def __init__(self, console = False, filepath = None):
        self.filepath = filepath
        self.console = console
        self.file = None
                
    def __enter__(self):
        if self.filepath:
            try:
                self.file = open(self.filepath, "a")
            except IOError as err:
                sys.exit("OSError: " + str(err))
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()
    
    def clear(self):
        if self.filepath:
            try:
                open(self.filepath, "w").close()
            except IOError as err:
                sys.exit("IOError: " + str(err))
    
    def printDict(self, dictionary):
        for key, value in dictionary.iteritems():
            self.emitLine("{0}: {1}".format(unicode(key).encode('utf-8'), unicode(value).encode('utf-8')))
    
    def printList(self, listObj):
        for element in listObj:
            self.emitLine(unicode(element))
    
    def emitLine(self, string):
        if self.file:
            self.file.write(string + '\r\n')
        if self.console:
            print string
    
    def emit(self, data):
        if isinstance(data, dict):
            self.printDict(data)
        elif type(data) is list or set:
            self.printList(data)
        else:
            self.emitLine(unicode(data))

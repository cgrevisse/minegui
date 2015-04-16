import sys
from enum import Enum
from app.views import importDataFromFile

def usage():
    sys.exit("Usage: python import.py (-(corpus|xml|ensemblHGNCMap|stringEntrezMap|entrezHGNCMap) file1 file2 ...)*")

if len(sys.argv) > 1:
    mode = None
    for i in range(1, len(sys.argv)):
        arg = sys.argv[i]
        
        if arg.startswith('-'):
            if arg in ['-corpus', '-xml', '-ensemblHGNCMap', '-stringEntrezMap', '-entrezHGNCMap']:
                mode = arg.replace('-','')
            else:
                usage()
        else:
            if mode is not None:
                importDataFromFile(arg, mode)
                print("{} file {} successfully imported".format(mode.title(), arg))
            else:
                usage()
else:
    usage()
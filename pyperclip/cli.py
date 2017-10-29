from __future__ import print_function
from optparse import OptionParser
import re
import sys
import pyperclip

def copy():
    contents = sys.stdin.read().decode('utf-8')
    contents = re.sub('\r?\n?$', '', contents) # trim trailing NL
    pyperclip.copy(contents)
    return

def paste():
    contents = pyperclip.paste()
    print(contents.encode('utf-8'))

def main():
    p = OptionParser()
    p.add_option('-i','--copy', action='store_const', const=copy, dest='action', default=copy)
    p.add_option('-o','--paste', action='store_const', const=paste, dest='action')
    opts, args = p.parse_args()
    assert len(args) == 0
    opts.action()

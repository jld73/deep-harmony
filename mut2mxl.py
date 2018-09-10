#!/usr/local/bin/python3
from music21 import *
from music_tokens import *
import sys, re
from pprint import pprint

# 
# read one or more .mut files on the command line and save them as 
# a single Music XML file.
#

fn = sys.argv[1]
print("Input file: {0}".format(sys.argv[1]))

s = converter.parse(fn)
print("Parsed music file:")
s.show('text')         # uncomment to print parsed music file


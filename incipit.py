#!/usr/local/bin/python3
from music21 import *
from music_tokens import *
# from mut_parser import *
import sys, re

# print the incipit for a music file -- for example, 11556-65443-32215 
# for "Twinkle twinkle little stars". 
# See comments on the music_tokens get_key function for caveats when using
# this on recorded polyphonic midi files. 

converter.registerSubconverter(MusicTokens)

fn = sys.argv[1]
s = converter.parse(fn)
#s.show('text')         # uncomment to print parsed music file

key, inc = get_incipit(s)
inc = "{0}-{1}-{2}".format(inc[0:5], inc[5:10], inc[10:15])
inc = re.sub('-$','',inc)
inc = re.sub('-$','',inc)
print("Key: {0}".format(key))
print("Incipit: {0}".format(inc))

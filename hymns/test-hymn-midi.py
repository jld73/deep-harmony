#!/usr/local/bin/python3
import sys, glob, re, os
from music_tokens import *
import json
from pprint import pprint


def main():
    with open('files-midi/Associations.json') as f:
        midi_dict = json.load(f)

    fn = sys.argv[1]

    print("{0}: {1}-{2}".format(fn, midi_dict[fn]['hymnalID'], midi_dict[fn]['number']))

    try:
        s = converter.parse(fn)
    except:
        print("couldn't parse file {0}".format(fn))
        exit(1)

    myKey = ""
    print("About to get key")
    try:
        myKey = get_first(s.flat, key.Key)
        print("Got embedded key: {0}".format(myKey.name))
    except:
        print("about to analyze for key")
        myKey = s.analyze('key')
        print("Analyzed key: {0}".format(myKey.name))
    key_tonic = myKey.tonic.name
    if myKey.mode != 'major':
        key_tonic = key_tonic.lower()
    key_tonic = re.sub('-','b',key_tonic)

    try:
        print("trying to get incipit")
        incipit = get_incipit(s)
    except:
        print("Couldn't get incipit for {0}".format(fn))
        exit(1)

    print(key_tonic, midi_dict[fn]['hymnalID'], midi_dict[fn]['number'])
    new_fn = "midi/{0}/{1}-{2}-{3}-{4}={5}-{6}.midi".format(incipit[:3],incipit[0:5],
        incipit[5:10], incipit[10:15], key_tonic, midi_dict[fn]['hymnalID'], midi_dict[fn]['number'])
    new_fn.replace(r"(", r"\(")
    new_fn.replace( r")", r"\)")

    print("mkdir -p midi/{0}".format(incipit[:3]))
#   os.system("mkdir -p midi/{0}".format(incipit[:3]))
    print("cp '{0}' {1}".format(fn, new_fn))
#   os.system("cp '{0}' {1}".format(fn, new_fn))
    
main()

#!/usr/local/bin/python3
import sys, glob, re, os
from music_tokens import *
import json
from pprint import pprint


def main():
  print("\n\n\n\n\n\nrename-hymn-midi.py:")
  with open('files-midi/Associations.json') as f:
    midi_dict = json.load(f)

# pprint(midi_dict)

  for fn in midi_dict.keys():
    # skip these midi files becase they are recorded midis, not edited, and they cause lots
    # of problems (because of e.g. overlapping notes, extra rests)
    if fn.find("=CYBER")>0 or fn.find("=CCEH")>0 or fn.find("=PsH")>0 or fn.find("=THCFinal")>0:
        continue

    print("\n----\n{0}: {1}-{2}".format(fn, midi_dict[fn]['hymnalID'], midi_dict[fn]['number']))

    try:
        s = converter.parse(fn)
    except:
        print("Couldn't parse {0}".format(fn))
        os.system("rm {0}".format(fn))
        continue

    myKey = ""
    try:
        myKey = get_first(s.flat, key.Key)
        print("Got embedded key: {0}".format(myKey.name))
    except:
        myKey = s.analyze('key')
        print("Analyzed key: {0}".format(myKey.name))
    key_tonic = myKey.tonic.name
    if myKey.mode != 'major':
        key_tonic = key_tonic.lower()
    key_tonic = re.sub('-','b',key_tonic)

    try:
        incipit = get_incipit(s)
    except:
        print("Couldn't get incipit for {0}".format(fn))
        continue
#   print(key_tonic, midi_dict[fn]['hymnalID'], midi_dict[fn]['number'])
    new_fn = "midi/{0}/{1}-{2}-{3}-{4}={5}-{6}.midi".format(incipit[:3],incipit[0:5],
        incipit[5:10], incipit[10:15], key_tonic, midi_dict[fn]['hymnalID'], midi_dict[fn]['number'])
    new_fn.replace(r"(", r"\(")
    new_fn.replace( r")", r"\)")

    # we missed files containing apostrophes: can we move them somehow?

#   print("mkdir -p midi/{0}".format(incipit[:3]))
    os.system("mkdir -p midi/{0}".format(incipit[:3]))
    print("mv '{0}' {1}".format(fn, new_fn))
    os.system("mv '{0}' {1}".format(fn, new_fn))
    
main()

#!/usr/local/bin/python3
# 
# test program: get a bach chorale from music21 corpus and output
# all the parts as mut files.
#
from music21 import *
from mut_out import *
import re, sys
theKey = 'C'


def main():
    fn = sys.argv[1]
    try:
        b = converter.parse(fn)
    except:
        print("Couldn't open", fn)
        exit(0)
    out_fn = re.sub(".mxl", "", fn)

    for myPart in b.parts:
        mut = to_mut(myPart)
        fn = "{0}-{1}.mut".format(out_fn, myPart.id)
        with open(fn, 'w') as f:
            f.write(mut)

    chord_mut = get_chords(b, 4)
    fn = out_fn + "-chords.mut"
    with open(fn, 'w') as f:
        f.write(chord_mut)

main()

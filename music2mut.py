#!/usr/local/bin/python3
# 
# read a music file given as command-line argument
# save it in parts in mut format, e.g. Soprano, Alto, Tenor, Bass
#
from music21 import *
from music_tokens import *
import re, sys
global theKey

def main():
    fn = sys.argv[1]
    try:
        s = converter.parse(fn)
    except:
        print("Couldn't open", fn)
        exit(0)
    print("music2mut: converting {0} to mut parts".format(fn))

    out_fn = re.sub(".(mxl|midi|xml)$", "", fn)

    myScore = stream.Score()
    for p in s.getElementsByClass(stream.Part):
        parts = partify(p)
        for part in parts:
            myScore.insert(part)

    if len(myScore.getElementsByClass(stream.Part)) != 4:
        print("{0} is not a 4-part piece--skipping ({1} parts)".format(fn, 
            len(myScore.getElementsByClass(stream.Part))))
#       exit(0)

    partNames = ['Soprano', 'Alto', 'Tenor', 'Bass', 'P5','P6','P7','P8','P9','P10','P11','P12']
    for i, part in enumerate(myScore.getElementsByClass(stream.Part)):
        mut = to_mut(part)
        fn = "{0}-{1}.mut".format(out_fn, partNames[i])
        with open(fn, 'w') as f:
            f.write(mut)

    rchord_mut, nchord_mut = get_chords(s, 1)
    rfn = out_fn + "-RChords.mut"
    with open(rfn, 'w') as f:
        f.write(rchord_mut)
    nfn = out_fn + "-NChords.mut"
    with open(nfn, 'w') as f:
        f.write(nchord_mut)

main()

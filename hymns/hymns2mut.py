#!/usr/local/bin/python3
# 
# read a music file given as command-line argument
# save it in parts in mut format, e.g. Soprano, Alto, Tenor, Bass
#
from music21 import *
from music_tokens import *
import re, sys, glob
global theKey

def main():

  num_converted = 0

  for fn in glob.glob("midi-unique/[0-9][0-9][0-9]/*mid*"):
    out_fn = re.sub("midi","mut",fn, count=1)
    out_fn = re.sub(".midi","",fn)

    try:
        s = converter.parse(fn)
    except:
        print("Couldn't parse", fn)
        continue
    print("converting {0} to mut parts, {1}".format(fn, out_fn))

    myScore = stream.Score()
    for p in s.getElementsByClass(stream.Part):
        try:
            parts = partify(p)
        except:
            continue

        for part in parts:
            myScore.insert(part)

    if len(myScore.getElementsByClass(stream.Part)) != 4:
        print("{0} is not a 4-part piece--skipping ({1} parts)".format(fn, 
            len(myScore.getElementsByClass(stream.Part))))
        continue

    partNames = ['Soprano', 'Alto', 'Tenor', 'Bass']
    for i, part in enumerate(myScore.getElementsByClass(stream.Part)):
        mut = to_mut(part)
        fn = "{0}-{1}.mut".format(out_fn, partNames[i])
        with open(fn, 'w') as f:
            f.write(mut)

    try:
        rchord_mut, nchord_mut = get_chords(s, 1)
    except:
        continue
    rfn = out_fn + "-RChords.mut"
    with open(rfn, 'w') as f:
        f.write(rchord_mut)
    nfn = out_fn + "-NChords.mut"
    with open(nfn, 'w') as f:
        f.write(nchord_mut)

    num_converted += 1

  print ("{0} midi files completely converted".format(num_converted))

main()

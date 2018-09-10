#!/usr/local/bin/python3
#
# read music files from specified directory (e.g. music_to_learn/). 
# create datafiles for tensorflow-nmt code:
# prefix bach is directory; train, test, dev files; suffix .sop, .alt, .ten, .bas, .nch
# e.g. bach/train.sop, bach/test.bas, bach/dev.nch
#
# output test, train, validate files suitable for OpenNMT 
# output file   src-test.txt	src-val.txt     tgt-test.txt	tgt-val.txt
#               src-train.txt	src-vocab.txt	tgt-train.txt	tgt-vocab.txt
#
# todo: doesn't support comments in mut files
#
import sys, glob, re, os, random
from os.path import isfile

#
# these could be command-line parameters
#
dir    = "midi-unique/*/"
out_dir = "hymn_data/"
os.system("mkdir -p " + out_dir)
portions = [80, 10, 10] 	# train, test, dev


def get_pieces(dir):
    pieces = []
    print("looking for hymns matching {0}*-Soprano.mut".format(dir))
    for fn in glob.glob("{0}*-Soprano.mut".format(dir)):
        base = re.sub(r"midi-unique/.../", "", fn)
        base = re.sub("-Soprano.mut", "", base)
#       print("base:", base)
        prefix = "midi-unique/{0}/{1}".format(base[0:3], base)
#       print("looking for {0}-Soprano.mut".format(prefix))

        if ((isfile(prefix+"-Soprano.mut") and isfile(prefix+"-Alto.mut") and
            isfile(prefix+"-Tenor.mut") and isfile(prefix+"-Bass.mut") and
            isfile(prefix+"-NChords.mut"))): 
            pieces.append(prefix)
#           print("  all the parts are there!!!")
    return pieces

def make_datafile(dir, pieces, file, part, ext):
    print("Making {0} datafiles for {1}".format(file, part))
    lines = ""
    for piece in pieces:
        with open("{0}-{1}.mut".format(piece, part, 'r')) as infile:
            line = infile.read().replace("\n", " ")
        lines = lines + line + "\n"
    out_file = "{0}{1}.{2}".format(dir, file, ext)
    with open(out_file, 'w') as f:
        f.write(lines)
    return lines

def get_vocab(data):
    word_set = set()
    for word in data.replace("\n","").split():
        word_set.add(word)
    words = "\n".join(sorted(word_set))
    return words

def main():
    print("Building training datafiles for music in {0}".format(out_dir))
    pieces = get_pieces(dir)
    random.shuffle(pieces)
    num = len(pieces)
    ntest = num * portions[0] // sum(portions)
    nval  = num * (portions[0]+portions[1]) // sum(portions)
    train = pieces[:ntest]
    test  = pieces[ntest:nval]
    val   = pieces[nval:]
    print("Pieces: {0} (train {1}, test {2}, val {3})".format(len(pieces), 
        len(train), len(test), len(val)))

    sop =  make_datafile(out_dir, train, "train", 'Soprano', 'sop')
    sop += make_datafile(out_dir, test,  "test", 'Soprano', 'sop')
    sop += make_datafile(out_dir, val,   "val", 'Soprano', 'sop')
    alt =  make_datafile(out_dir, train, "train", 'Alto', 'alt')
    alt += make_datafile(out_dir, test,  "test", 'Alto', 'alt')
    alt += make_datafile(out_dir, val,   "val", 'Alto', 'alt')
    ten =  make_datafile(out_dir, train, "train", 'Tenor', 'ten')
    ten += make_datafile(out_dir, test,  "test", 'Tenor', 'ten')
    ten += make_datafile(out_dir, val,   "val", 'Tenor', 'ten')
    bas =  make_datafile(out_dir, train, "train", 'Bass', 'bas')
    bas += make_datafile(out_dir, test,  "test", 'Bass', 'bas')
    bas += make_datafile(out_dir, val,   "val", 'Bass', 'bas')
    nch =  make_datafile(out_dir, train, "train", 'NChords', 'nch')
    nch += make_datafile(out_dir, test,  "test", 'NChords', 'nch')
    nch += make_datafile(out_dir, val,   "val", 'NChords', 'nch')

    with open(out_dir + "vocab.sop", 'w') as f:
        f.write(get_vocab(sop))
    with open(out_dir + "vocab.alt", 'w') as f:
        f.write(get_vocab(alt))
    with open(out_dir + "vocab.ten", 'w') as f:
        f.write(get_vocab(ten))
    with open(out_dir + "vocab.bas", 'w') as f:
        f.write(get_vocab(bas))
    with open(out_dir + "vocab.nch", 'w') as f:
        f.write(get_vocab(nch))
    
main()

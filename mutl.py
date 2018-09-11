#!/usr/local/bin/python3
from music21 import *
from music_tokens import *
from fractions import Fraction 
from math import ceil
from pprint import pprint
import numpy as np
import re, sys
debug = 0

note_vector_length = 28

pitch_class_dict = { 'C':0, 'C#':1, 'D-':1, 'Db':1, 'D':2, 'D#':3, 'E-':3, 'Eb':3, 
    'E':4, 'E#':5, 'F-':4, 'Fb':4, 'F':5, 'F#':6, 'F##':7, 'G-':6, 'Gb':6, 'G':7, 
    'G#':8, 'A--':7, 'Abb':7, 'A-':8, 'Ab':8, 'A':9, 'A#':10, 'B-':10, 'Bb':10, 
    'B':11, 'B#':0, 'C-':11, 'Cb':11, 'rest':12 }
duration_dict = { '8/1':0, '4/1':1, '2/1':2, '1/1':3, '1/2':4, '1/4':5, '1/8':6, 
    '1/16':7, '1/32':8 }
incipit_dict = { 0:'1', 1:'2', 2:'2', 3:'3', 4:'3', 5:'4', 6:'5', 7:'5', 8:'6', 
    9:'6', 9:'6', 10:'7', 11:'7' }

#
# print out loggin data if the debug level is high enough
#
def log(s,level):
    if debug>=level:
        print(s)

def parseData(strData): 
    print("In mutl's parseData")
    #
    #  first pass, by line: read metadata, dump comments 
    #
    strDataList = strData.splitlines()
    newData = ""
    s = stream.Part()
    s.insert(0, metadata.Metadata())
    s.metadata.title = "Imported piece"

    for line in strData.splitlines():
        if line == "":
            pass
        elif line[:4] == "### ":
            var, val = line[4:].split(':')
            print("Processing {0} => {1}".format(var,val))
            if var == "title":                  # rewrite this bit more elegantly,
                s.metadata.title = val          # configured with a table?
            elif var == "popularTitle":
                s.metadata.popularTitle = val
            elif var == "composer":
                s.metadata.composer = val
            elif var == "date":
                s.metadata.date = val
            elif var == "hymnalName":
                s.metadata.groupTitle = val
            elif var == "hymnalID":
                s.metadata.collectionDesignation = val
            elif var == "number":
                s.metadata.number = val
            elif var == "authorityNumber": 
                s.metadata.alternativeTitle = val
            elif var == "countryOfComposition":
                s.metadata.countryOfComposition = val
            elif var == "copyright":
                s.metadata.copyright = val
            elif var == "part":
                s.partName = val
            else:
                print("** Unhandled metadata: {0} => {1}".format(var, val))
        elif line[0] != '#':
            newData += line + " "

#   print(pprint(vars(s.metadata)))
#   print("Partname: {0}".format(s.partName))

    #
    # now split up into space-separated tokens and process them one at a time
    #
    # first pass: count number of pickup beats. Add a rest for the remainder of
    # the first measure, since music21's makeMeasures function doesn't do pickup beats.
    # 
    offset = 0.0
    quarterlengths_per_measure = 12.0
    initialRest = None

    strDataList = newData.split()
    print("First token pass: find pickup beats")
    for token in strDataList:
        print("  1. token: {0}".format(token))
        if token == "<bar>":
            print("     found <bar>: offset {0}".format(offset))
            if offset < quarterlengths_per_measure:
                duration = quarterlengths_per_measure-offset
                initialRest = note.Rest(quarterLength = duration)
                print("     adding rest with duration {0}".format(duration))
#               s.insert(0, initialRest)
                break
        elif token.startswith("<time"):
            print("     found <time> {0}".format(token[6:-1]))
            num, denom = token[6:-1].split('/')
            quarterlengths_per_measure = 4.0 * float(num) / float(denom);
            print("     quarterlengths_per_measure: {0}".format(quarterlengths_per_measure))
        elif token[0] != '<':
            note1, durfrac = token.split(':')
            if durfrac.endswith('t'):       # handle t (tie) after duration
                durfrac = durfrac[:-1]
            duration = float(Fraction(durfrac))

            if note1 == "backup":
                offset -= duration
            else:
                offset += duration
            print("     New offset: {0}".format(offset))
        elif offset >= quarterlengths_per_measure:
            break

    #
    # second pass: import music into music21
    #
    offset = 0.0
    tie_forward = False
    tie_back = False

    strDataList = newData.split()
    for token in strDataList:
        print("Token: ", token)
        if token[0] == "<":         # e.g. <sot>
            tok = token.replace("<","").replace(">","")
            if tok == "sot" or tok == "eot":
                offset = 0.0            # new file? rest time to zero
            elif tok == "bar":
                s.makeMeasures(inPlace=True)
#               b = bar.BarLine()
#               s.insert(offset, b)
#               pass
                # close off measure; start new one
            elif tok == "phrase":
                # can we indicate end of prhase in MusicXML somehow?
                pass
            else:
                op, val = tok.split(':')
                if op == "time":
                    m = meter.TimeSignature(val)
                    s.append(m)
                    if initialRest is not None:
                        s.insert(0, initialRest)
                elif op == "key":
                    k = key.Key(val)
                    s.append(k)
        else:           # it's a note, forward backward, rest, or chord
            note1, durfrac = token.split(':')

            if durfrac.endswith('t'):       # handle t (tie) after duration
                tie_forward = True;
                durfrac = durfrac[:-1]
            duration = float(Fraction(durfrac))

            if note1 == "forward":
                offset += duration
                print("Forward: new offset {0}".format(offset))
            elif note1 == "backup":
                offset -= duration
                print("Backup: new offset {0}".format(offset))
            elif note1[0] in "rR":             # rest
                r = note.Rest()
                r.duration.quarterLength = duration
                s.insert(offset, r)
                offset += duration
            elif note1.startswith("chord"):
                _, chord1 = note1.split('-')
                h = harmony.ChordSymbol(chord1, quarterLength=duration)
                n = note.Rest(quarterLength = duration)
                s.insert(offset, h)
                s.insert(offset, n)
                print("Chord: {0} start {1} duration {2}".format(chord1, offset, duration))
                offset += duration

            else:                           # a note
                note1 = note1.replace('-','')
                note1 = note1.replace('b', '-')
                n1 = note.Note(note1)
                n1.duration.quarterLength = duration

                if not tie_forward and tie_back:        # handle ties
                    n1.tie=tie.Tie('stop')
                elif tie_forward and not tie_back:
                    n1.tie=tie.Tie('start')
                elif tie_forward and tie_back:
                    n1.tie = tie.Tie('continue')
                tie_back = tie_forward
                tie_forward = False

                s.insert(offset, n1)
                offset += duration
    
    return s.makeMeasures()



print("Input file: {0}".format(sys.argv[1]))
fn = sys.argv[1]
with open(fn, 'r') as f:
  data = f.read()

s = parseData(data)

print("Parsed music file:")
s.show('text')         # uncomment to print parsed music file
s.makeMeasures(inPlace=True)
s.write('mxl', 'test.musicxml')

